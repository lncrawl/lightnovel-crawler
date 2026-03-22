#!/usr/bin/env python3
"""
List source base URLs that appear unreachable from multiple global vantage points.

Uses the free public API at https://check-host.net (see their /about/api page).
Checks are run from several independent nodes; if none receive a valid HTTP
response, the URL is reported as likely down for everyone (not just your
network).

Run from repo root:
  uv run python scripts/check_sources.py

Formatted summary (Rich) is written to stderr; stdout is one down URL per line for scripting.
"""

from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from tqdm import tqdm

workdir = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(workdir))

from lncrawl.context import ctx  # noqa: E402

app = typer.Typer(help="Check source base URLs against check-host.net multi-node HTTP probes.")

CHECK_HOST = "https://check-host.net"
HEADERS = {"Accept": "application/json"}

_lock = Lock()


def _row_has_http_response(row: Any) -> bool:
    """True if the probe got an HTTP status from the remote server."""
    if not isinstance(row, (list, tuple)) or len(row) < 4:
        return False
    code = row[3]
    if code is None:
        return False
    s = str(code)
    return s.isdigit() and len(s) == 3


def _node_is_reachable(node_data: Any) -> Optional[bool]:
    """
    None if this node has not finished yet (should not happen after polling).
    True if any probe returned an HTTP response.
    False if probes finished without HTTP.
    """
    if node_data is None:
        return None
    if not isinstance(node_data, list):
        return False
    for row in node_data:
        if _row_has_http_response(row):
            return True
    return False


def _all_nodes_down(results: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    True if every node reported a non-reachable result (no HTTP code).
    """
    if not results:
        return False, "empty result"
    verdicts: List[bool] = []
    for node_id, node_data in results.items():
        if not node_id.endswith(".node.check-host.net"):
            continue
        v = _node_is_reachable(node_data)
        if v is None:
            return False, "incomplete"
        verdicts.append(v)
    if not verdicts:
        return False, "no nodes"
    if all(not x for x in verdicts):
        return True, None
    return False, None


def _poll_check_result(client: httpx.Client, request_id: str, timeout: float) -> Dict[str, Any]:
    deadline = time.time() + timeout
    last: Dict[str, Any] = {}
    while time.time() < deadline:
        r = client.get(f"{CHECK_HOST}/check-result/{request_id}", headers=HEADERS, timeout=30.0)
        r.raise_for_status()
        last = r.json()
        if not last:
            time.sleep(0.4)
            continue
        pending = [k for k, v in last.items() if k.endswith(".node.check-host.net") and v is None]
        if not pending:
            return last
        time.sleep(0.4)
    return last


def check_url_globally_down(
    client: httpx.Client,
    url: str,
    max_nodes: int,
    poll_timeout: float,
) -> Tuple[bool, str]:
    """
    Returns (is_down_for_everyone, detail_note).
    """
    r = client.get(
        f"{CHECK_HOST}/check-http",
        params={"host": url, "max_nodes": max_nodes},
        headers=HEADERS,
        timeout=30.0,
    )
    r.raise_for_status()
    start = r.json()
    if not start.get("ok"):
        return False, f"check failed: {start}"
    request_id = start.get("request_id")
    if not request_id:
        return False, "no request_id"
    results = _poll_check_result(client, request_id, poll_timeout)
    down, reason = _all_nodes_down(results)
    if down:
        link = start.get("permanent_link", "")
        return True, f"report {link}" if link else "all nodes unreachable"
    if reason:
        return False, reason
    return False, "reachable from at least one node"


def _normalize_base_url(url: str) -> str:
    """
    Ensure a scheme + netloc suitable for check-http (host= full URL).
    """
    p = urlparse(url.strip())
    if not p.scheme or not p.netloc:
        return f"https://{url.lstrip('/')}"
    return url.strip()


def _unique_urls(items: Iterable[Any]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for it in items:
        u = _normalize_base_url(it.url)
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _report_link_from_note(note: str) -> Optional[str]:
    if note.startswith("report "):
        return note[7:].strip()
    return None


def _render_tqdm_line(console: Console, *parts: Tuple[str, str]) -> str:
    """Capture a single rich line for tqdm.write without breaking the bar."""
    with console.capture() as cap:
        text = Text()
        for i, (s, style) in enumerate(parts):
            if i:
                text.append(" ")
            text.append(s, style=style)
        console.print(text)
    return cap.get().rstrip("\n")


def _print_final_report(
    err_console: Console,
    *,
    total: int,
    ok_count: int,
    down_rows: List[Tuple[str, str]],
    err_rows: List[Tuple[str, str]],
) -> None:
    err_console.print()
    err_console.rule("[bold cyan]Source availability report[/]", align="left")
    err_console.print(
        f"[dim]Multi-node HTTP checks via[/] [link={CHECK_HOST}]{CHECK_HOST}[/link]\n",
        end="",
    )

    stats = Table.grid(padding=(0, 3))
    stats.add_column(style="bold", justify="right")
    stats.add_column(justify="left")
    stats.add_row("[cyan]Checked[/]", f"{total} unique base URL(s)")
    stats.add_row("[green]Reachable[/]", f"{ok_count} (HTTP from at least one probe node)")
    stats.add_row("[red]Down everywhere[/]", f"{len(down_rows)} (no HTTP from any probe node)")
    stats.add_row("[yellow]Errors[/]", f"{len(err_rows)} (request or parse failure)")
    err_console.print(Panel(stats, title="[bold]Summary[/]", border_style="dim", box=box.ROUNDED))

    if down_rows:
        dt = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold red",
            border_style="red",
            title="[bold]Unreachable from all probed nodes[/]",
            expand=True,
        )
        dt.add_column("#", style="dim", justify="right", width=3)
        dt.add_column("URL", overflow="ellipsis", no_wrap=True, ratio=2)
        dt.add_column("Report", overflow="ellipsis", style="dim", ratio=1)
        for i, (url, note) in enumerate(down_rows, start=1):
            link = _report_link_from_note(note)
            if link:
                link = f"[link={link}]{link}[/link]"
            dt.add_row(str(i), url, link or note)
        err_console.print(dt)

    if err_rows:
        et = Table(
            box=box.SIMPLE_HEAD,
            show_header=True,
            header_style="bold yellow",
            border_style="yellow",
            title="[bold]Check failures[/]",
        )
        et.add_column("#", style="dim", justify="right", width=4)
        et.add_column("URL", overflow="fold")
        et.add_column("Error", overflow="fold", style="dim")
        for i, (url, msg) in enumerate(err_rows, start=1):
            et.add_row(str(i), url, msg)
        err_console.print(et)

    err_console.print()


def _check_one_url(
    client: httpx.Client,
    url: str,
    max_nodes: int,
    poll_timeout: float,
) -> Tuple[str, str, str]:
    """
    Returns (url, status, detail). status is 'ok', 'down', or 'err'.
    """
    try:
        is_down, note = check_url_globally_down(client, url, max_nodes, poll_timeout)
        if is_down:
            return url, "down", note
        return url, "ok", note
    except Exception as e:
        return url, "err", repr(e)


def _update_rejected(url: str):
    with _lock:
        local_file = ctx.config.crawler.local_index_file
        rejected_file = local_file.parent / "_rejected.json"
        if not rejected_file.is_file():
            return
        json_str = rejected_file.read_text(encoding="utf-8")
        rejected = json.loads(json_str)
        rejected.update({url: "Site is down"})
        json_str = json.dumps(rejected, indent=2, sort_keys=True)
        rejected_file.write_text(json_str, encoding="utf-8")


@app.command()
def main(
    max_nodes: int = typer.Option(
        3,
        "--max-nodes",
        help="Number of check-host nodes per URL.",
    ),
    poll_timeout: float = typer.Option(
        25.0,
        "--poll-timeout",
        help="Seconds to wait for all nodes to return results.",
    ),
    workers: int = typer.Option(
        8,
        "-j",
        "--workers",
        help="Parallel checks (thread pool size). Lower if check-host rate-limits you.",
    ),
    include_rejected: bool = typer.Option(
        False,
        "--include-rejected",
        help="Include sources marked disabled in the index.",
    ),
    sync_remote_index: bool = typer.Option(
        False,
        "--sync-remote-index",
        help="Sync remote source index on startup (slower).",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        help="Only check the first N unique URLs (for testing).",
    ),
) -> None:
    """
    List sources whose base URLs fail HTTP checks from multiple global nodes (check-host.net).
    Progress bar and formatted report on stderr; plain down-only URLs on stdout (one per line).
    """
    err_console = Console(stderr=True)

    ctx.setup(sync_remote_index=sync_remote_index)
    ctx.sources.ensure_load()
    items = ctx.sources.list(include_rejected=include_rejected)
    urls = _unique_urls(items)
    if limit is not None:
        urls = urls[:limit]

    down_rows: List[Tuple[str, str]] = []
    err_rows: List[Tuple[str, str]] = []
    ok_count = 0
    n = len(urls)
    if n == 0:
        err_console.print("[yellow]No source URLs to check.[/]")
        return

    workers = max(1, workers)

    with httpx.Client(follow_redirects=True) as client:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            future_to_url = {
                pool.submit(
                    _check_one_url,
                    client,
                    url,
                    max_nodes,
                    poll_timeout,
                ): url
                for url in urls
            }
            with tqdm(
                total=n,
                desc="Checking sources",
                unit="url",
                file=sys.stderr,
                leave=True,
            ) as bar:
                for fut in as_completed(future_to_url):
                    url, status, detail = fut.result()
                    bar.update(1)
                    if status == "err":
                        err_rows.append((url, detail))
                        line = _render_tqdm_line(
                            err_console,
                            ("ERR", "bold yellow"),
                            (url, "yellow"),
                            (detail[:120] + ("..." if len(detail) > 120 else ""), "dim"),
                        )
                        tqdm.write(line, file=sys.stderr)
                    elif status == "down":
                        down_rows.append((url, detail))
                        line = _render_tqdm_line(err_console, ("DOWN", "bold red"), (url, "red"))
                        tqdm.write(line, file=sys.stderr)
                        _update_rejected(url)
                    else:
                        ok_count += 1

    order = {u: i for i, u in enumerate(urls)}
    down_rows.sort(key=lambda row: order.get(row[0], 0))
    err_rows.sort(key=lambda row: order.get(row[0], 0))

    _print_final_report(
        err_console,
        total=n,
        ok_count=ok_count,
        down_rows=down_rows,
        err_rows=err_rows,
    )


if __name__ == "__main__":
    app()
