#!/usr/bin/env python3
"""
Wuxiaworld protobuf pipeline (replaces the old numbered scripts 1-4).

    python wuxia_proto.py scrape   [URL] [-f _proto] [-e .ts] [-o DIR] [-j 8]
    python wuxia_proto.py generate [--native-maps] [--no-optional] [-v]
    python wuxia_proto.py dump     [--py] [--json] [--pretty]
    python wuxia_proto.py all      [URL]            # scrape + generate + dump --py

scrape    pull the original TypeScript from the site's source maps (like DevTools > Sources)
generate  TypeScript -> proto_temp/*.proto + proto_temp/wuxia.proto (imports everything)
dump      compile wuxia.proto with pyease_grpc -> wuxiacom_proto.py (and/or wuxia.json)

Needs: requests (scrape), pyease-grpc >= 1.8 + grpcio-tools (dump).
All paths are relative to this script, not to the current directory.
"""  # noqa: E501
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from urllib.parse import urljoin, urlparse

import ts_to_proto

HERE = Path(__file__).resolve().parent
TS_DIR = HERE / "wuxiaworld_typescript"
PROTO_DIR = HERE / "proto_temp"
ROOT_PROTO = "wuxia.proto"
DEFAULT_URL = "https://www.wuxiaworld.com"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0;"
                   " Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
}
JS_RE = re.compile(r"""["'(]([^"'()\s]+?\.js)(?:\?[^"'()\s]*)?["')]""")
CHUNK_RE = re.compile(r"""["']([^"'\s]*?/_next/static/[^"'\s]+?\.js)["']""")
SMAP_RE = re.compile(r"//[#@]\s*sourceMappingURL=(\S+)\s*$")


# ----------------------------------------------------------------------------
# 1. scrape
# ----------------------------------------------------------------------------
def _make_session(workers: int):
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    s = requests.Session()
    s.headers.update(HEADERS)
    retry = Retry(total=3, backoff_factor=0.5, allowed_methods=("GET",),
                  status_forcelist=(429, 500, 502, 503, 504))
    adapter = HTTPAdapter(
        max_retries=retry, pool_connections=workers, pool_maxsize=workers)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def _get(session, url):
    import requests
    try:
        r = session.get(url, timeout=30)
        if r.status_code == 200:
            return r
    except requests.RequestException as e:
        print(f"  ! {url}: {e}")
    return None


def _find_map(session, js_url, js_text):
    """Parsed source map JSON for a JS file, or None."""
    candidates = []
    last = js_text.rstrip().splitlines()[-1] if js_text.strip() else ""
    m = SMAP_RE.search(last)
    if m and not m.group(1).startswith("data:"):
        candidates.append(urljoin(js_url, m.group(1)))
    candidates.append(js_url.split("?")[0] + ".map")
    for c in dict.fromkeys(candidates):
        r = _get(session, c)
        if r:
            try:
                return r.json()
            except ValueError:
                pass
    return None


def _clean_path(src):
    src = re.sub(r"^(webpack(-internal)?://[^/]*/|webpack://)", "", src)
    src = src.split("?")[0]
    parts = [p for p in re.split(r"[\\/]+", src) if p not in ("", ".", "..")]
    return Path(*parts) if parts else None


def _process_js(session, js_url, flt, ext):
    """Worker: download one JS file ->"""
    """(new chunk urls, [(rel path, source)], notes)."""
    r = _get(session, js_url)
    if not r:
        return None
    netloc = urlparse(js_url).netloc
    chunks = {urljoin(js_url, m.group(1)) for m in CHUNK_RE.finditer(r.text)
              if urlparse(urljoin(js_url, m.group(1))).netloc == netloc}
    files, notes = [], []
    smap = _find_map(session, js_url, r.text)
    if smap:
        sources = smap.get("sources", [])
        contents = smap.get("sourcesContent") or []
        for i, src in enumerate(sources):
            if flt not in src or not src.split("?")[0].endswith(ext):
                continue
            if i >= len(contents) or contents[i] is None:
                notes.append(f"  - {src} (no embedded content)")
                continue
            rel = _clean_path(src)
            if rel:
                files.append((rel, contents[i]))
    return chunks, files, notes


def scrape(url=DEFAULT_URL, flt="_proto", ext=".ts",
           out=TS_DIR, workers=8) -> int:
    session = _make_session(workers)
    page = _get(session, url)
    if not page:
        sys.exit("Could not download the page.")
    pending = {urljoin(url, m.group(1)) for m in JS_RE.finditer(page.text)}
    print(f"Found {len(pending)} JS files in page HTML")

    out = Path(out)
    seen, saved = set(), set()
    running = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        def submit_new(urls):
            for u in urls:
                if u not in seen:
                    seen.add(u)
                    running[pool.submit(_process_js, session, u, flt, ext)] = u

        submit_new(pending)
        while running:
            done, _ = wait(running, return_when=FIRST_COMPLETED)
            for fut in done:
                js_url = running.pop(fut)
                res = fut.result()
                if res is None:
                    continue
                chunks, files, notes = res
                print(f"[JS] {js_url}")
                submit_new(chunks)
                for note in notes:
                    print(note)
                for rel, text in files:
                    dest = out / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(text, encoding="utf-8")
                    if dest not in saved:
                        print(f"  + saved {dest}")
                    saved.add(dest)
    print(f"\nDone. Saved {len(saved)} file(s) to '{out.resolve()}'")
    return len(saved)


# ----------------------------------------------------------------------------
# 2. generate
# ----------------------------------------------------------------------------
def generate(ts_dir=TS_DIR, proto_dir=PROTO_DIR,
             native_maps=False, explicit_optional=True, verbose=False):
    ts_dir, proto_dir = Path(ts_dir), Path(proto_dir)
    if not ts_dir.is_dir():
        sys.exit(f"{ts_dir} not found - run 'scrape' first")
    proto_dir.mkdir(parents=True, exist_ok=True)
    # proto_temp is generated output; drop stale files
    for old in proto_dir.glob("*.proto"):
        old.unlink()
    opt = ts_to_proto.Options(
        native_maps=native_maps,
        explicit_optional=explicit_optional, verbose=verbose)
    stems = ts_to_proto.convert_dir(
        ts_dir, proto_dir, opt, root_proto=ROOT_PROTO)
    print(f"Generated {len(stems)} proto files + {ROOT_PROTO} in {proto_dir}")
    return stems


# ----------------------------------------------------------------------------
# 3. dump
# ----------------------------------------------------------------------------
def dump(proto_dir=PROTO_DIR, out_dir=HERE, py=True,
         as_json=False, pretty=False):
    try:
        from pyease_grpc import Protobuf
    except ImportError:
        sys.exit(
            "pyease_grpc is not installed:  "
            "pip install -U pyease-grpc grpcio-tools")
    proto_dir = Path(proto_dir)
    try:
        data = Protobuf.from_file(
            # one protoc run
            str(proto_dir / ROOT_PROTO), [str(proto_dir)]).save()
    except TypeError as e:
        if "duplicate file name" in str(e):
            sys.exit(
                f"{e}\nYour pyease-grpc is too old for this protobuf version:"
                f"  pip install -U pyease-grpc")
        raise
    out_dir = Path(out_dir)
    if as_json or pretty:
        text = json.dumps(data, indent=4 if pretty else None)
        (out_dir / "wuxia.json").write_text(text, encoding="utf-8")
        print(f"wrote {out_dir / 'wuxia.json'}")
    if py:
        text = json.dumps(data)
        # repr() makes the JSON a valid Python literal
        # whatever quotes/backslashes it contains
        (out_dir / "wuxiacom_proto.py").write_text(
            "import json\n"
            f"WUXIWORLD_PROTO__str = {text!r}\n"
            "WUXIWORLD_PROTO = json.loads(WUXIWORLD_PROTO__str)\n",
            encoding="utf-8")
        print(f"wrote {out_dir / 'wuxiacom_proto.py'}")


# ----------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scrape", help="download TypeScript from source maps")
    s.add_argument("url", nargs="?", default=DEFAULT_URL)
    s.add_argument("-f", "--filter", default="_proto",
                   help="only sources whose path contains this text")
    s.add_argument("-e", "--ext", default=".ts", help="file extension to keep")
    s.add_argument("-o", "--out", default=str(TS_DIR))
    s.add_argument("-j", "--workers", type=int,
                   default=8, help="parallel downloads")

    g = sub.add_parser("generate", help="TypeScript -> .proto")
    g.add_argument("--native-maps", action="store_true",
                   help="real map<K,V> instead of MapEntry_N messages")
    g.add_argument("--no-optional", action="store_true",
                   help="no `optional` on every singular field")
    g.add_argument("-v", "--verbose", action="store_true")

    d = sub.add_parser(
        "dump", help="compile wuxia.proto -> wuxiacom_proto.py / wuxia.json")
    d.add_argument("--py", action="store_true",
                   help="write wuxiacom_proto.py (default)")
    d.add_argument("--json", action="store_true", help="write wuxia.json")
    d.add_argument("--pretty", action="store_true",
                   help="write indented wuxia.json")

    a = sub.add_parser("all", help="scrape + generate + dump")
    a.add_argument("url", nargs="?", default=DEFAULT_URL)

    args = ap.parse_args(argv)
    if args.cmd == "scrape":
        scrape(args.url, args.filter, args.ext, args.out, args.workers)
    elif args.cmd == "generate":
        generate(native_maps=args.native_maps,
                 explicit_optional=not args.no_optional, verbose=args.verbose)
    elif args.cmd == "dump":
        dump(py=args.py or not (args.json or args.pretty),
             as_json=args.json, pretty=args.pretty)
    else:
        scrape(args.url)
        generate()
        dump()


if __name__ == "__main__":
    main()
