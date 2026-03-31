import logging
import re
from enum import Enum
from typing import List, Optional

import questionary
import typer
from openai import OpenAI
from rich import print

from ...assets.languages import language_codes
from ...context import ctx
from ...utils.url_tools import extract_base, extract_host, validate_url
from .app import app

logger = logging.getLogger(__name__)


class Feature(str, Enum):
    has_manga = "manga"
    has_mtl = "mtl"
    can_search = "search"
    can_login = "login"
    has_volumes = "volumes"


@app.command("create", help="Create a source.")
def create_one(
    non_interactive: bool = typer.Option(
        False,
        "--noin",
        help="Disable interactive mode",
    ),
    locale: Optional[str] = typer.Option(
        None,
        "-l",
        "--locale",
        help="Content language (ISO 639-1 code)",
    ),
    features: Optional[List[Feature]] = typer.Option(
        None,
        "-f",
        "--features",
        help="Crawler features. e.g.: -f search -f mtl",
    ),
    use_openai: Optional[bool] = typer.Option(
        None,
        "--openai",
        is_flag=True,
        help="Use OpenAI model for auto generation",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        is_flag=True,
        help="Replace existing crawler with new one",
    ),
    url: str = typer.Argument(
        default=None,
        help="The URL of the source website.",
    ),
):
    # validate host
    host = extract_host(url)
    if not host:
        if non_interactive:
            print(f"[red]Invalid URL: {url}[/red]")
            return
        url = _prompt_url()
        host = extract_host(url)
        if not host:
            return

    # ensure locale
    if locale is None:
        locale = "" if non_interactive else _prompt_locale()

    # build crawler name and file_name
    name = " ".join(host.split(".")).title()
    name = re.sub(r"[^A-Za-z0-9]", "_", name)
    file_name = name.casefold()
    name = name.replace("_", "")
    name += "Crawler"

    # check file path
    file_path = _build_path(locale, file_name)
    if file_path.is_file() and not overwrite and (non_interactive or not _prompt_replace(str(file_path))):
        print(f"[red]A file already exists for [b]{host}[/b]:[/red] [cyan]{file_path}[/cyan]")
        return

    # ensure capabilities
    if features is None:
        if non_interactive:
            features = []
        else:
            features = _prompt_features()

    # ensure to use openai
    if use_openai is None:
        if non_interactive:
            use_openai = bool(ctx.config.app.openai_key)
        else:
            use_openai = _prompt_use_openai()
    if use_openai and not ctx.config.app.openai_key:
        if non_interactive:
            use_openai = False
        else:
            ctx.config.app.openai_key = _prompt_openai_key()

    # generate content stub
    base_url = extract_base(url)
    content = _generate_stub(
        name=name,
        base_url=base_url,
        features=features,
    )

    # fill content stub with openai
    if use_openai:
        content = _fill_with_openai(base_url, content)

    # save content
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    print(f"[green]Created crawler for [b]{host}[/b]:[/green] [cyan]{file_path}[/cyan]")


def _build_path(locale: str, file_name: str):
    file_path = ctx.config.crawler.local_sources
    file_path /= locale or "multi"
    if locale == "en":
        file_path /= file_name[0]
    file_path /= file_name + ".py"
    return file_path


def _prompt_url() -> str:
    print("[i]The URL must start with [cyan]http[/cyan] or [cyan]https[/cyan].[/i]")
    return questionary.text(
        "Website URL:",
        qmark="🌐",
        validate=validate_url,
    ).ask()


def _prompt_locale() -> str:
    choices = [f"[{c:02}] {n}" for c, n in sorted(language_codes.items())]

    print("[i]Leave empty if locale is unknown or content is in multiple language:[/i]")
    language = questionary.autocomplete(
        "Enter language (ISO 639-1 code)", choices=choices, validate=lambda s: (s in choices) or (s in language_codes)
    ).ask()

    if len(language) > 2:
        language = language[1:3].strip()
    return language


def _prompt_features() -> List[Feature]:
    selected = questionary.checkbox(
        "Enable features:",
        choices=list(Feature),
    ).ask()
    return [Feature(v) for v in selected]


def _prompt_replace(file: str) -> bool:
    print(f"[i][cyan]{file}[/cyan][/i]")
    return questionary.confirm("Crawler file already exists. Do you want to replace it?", default=False).ask()


def _prompt_use_openai() -> bool:
    return questionary.confirm("Use OpenAI to auto-generate crawler?", default=bool(ctx.config.app.openai_key)).ask()


def _prompt_openai_key() -> str:
    return questionary.text("OpenAI API Key").ask()


def _generate_stub(name: str, base_url: str, features: List[Feature]):
    content = """# -*- coding: utf-8 -*-
import logging
from typing import Generator, Optional

from bs4 import BeautifulSoup, Tag
"""

    models = "Chapter"
    if Feature.can_search in features:
        models += ", SearchResult"
    if Feature.has_volumes in features:
        models += ", Volume"

    content += f"""
from lncrawl.models import {models}"""

    main_class_name = "ChapterOnlySoupTemplate"
    if Feature.has_volumes not in features:
        content += """
from lncrawl.templates.soup.chapter_only import ChapterOnlySoupTemplate"""

    if Feature.can_search in features:
        content += """
from lncrawl.templates.soup.searchable import SearchableSoupTemplate"""

    if Feature.has_volumes in features:
        main_class_name = "ChapterWithVolumeSoupTemplate"
        content += """
from lncrawl.templates.soup.with_volume import ChapterWithVolumeSoupTemplate"""

    content += """

logger = logging.getLogger(__name__)


"""

    if Feature.can_search in features:
        content += f"""class {name}(SearchableSoupTemplate, {main_class_name}):"""
    else:
        content += f"""class {name}({main_class_name}):"""

    content += f"""
    base_url = ["{base_url}"]
    has_manga = {Feature.has_manga in features}
    has_mtl = {Feature.has_manga in features}

    def initialize(self) -> None:
        # You can customize `TextCleaner` and other necessary things.
        super().initialize()
        self.init_executor(1)
"""

    if Feature.can_login in features:
        content += """
    def login(self, username_or_email: str, password_or_token: str) -> None:
        # Add logic to login. For example: sources/en/l/lnmtl.py
        pass
"""

    if Feature.can_search in features:
        content += """
    def select_search_items(self, query: str) -> Generator[Tag, None, None]:
        # Select novel items found in search page from the query
        #
        # Example:
        #   params = {"searchkey": query}
        #   soup = self.post_soup(f"{self.home_url}search?{urlencode(params)}")
        #   yield from soup.select(".col-content .con .txt h3 a")
        yield from []

    def parse_search_item(self, tag: Tag) -> SearchResult:
        # Parse a tag and return single search result
        # The tag here comes from self.select_search_items
        return SearchResult(
            title=tag.get_text(strip=True),
            url=self.absolute_url(tag["href"]),
        )
"""

    content += """
    def parse_title(self, soup: BeautifulSoup) -> str:
        # Parse and return the novel title
        #
        # Example:
        # tag = soup.select_one("h1")
        # assert tag, 'No novel title tag'
        # return tag.get_text(strip=True)
        raise NotImplementedError()

    def parse_cover(self, soup: BeautifulSoup) -> str:
        # Parse and return the novel cover
        #
        # Example:
        # tag = soup.select_one("img[src]")
        # if not tag:
        #     return ""
        # return self.absolute_url(tag["src"])
        raise NotImplementedError()

    def parse_authors(self, soup: BeautifulSoup) -> Generator[str, None, None]:
        # Parse and return the novel authors
        #
        # Example 1: <single author>
        #   tag = soup.find(string="Author:")
        #   if tag:
        #       yield tag.get_text(strip=True)
        #
        # Example 2: <multiple authors>
        #   for a in soup.select("a[href*='/author/']"):
        #       yield a.get_text(strip=True)
        yield from []

    def parse_genres(self, soup: BeautifulSoup) -> Generator[str, None, None]:
        # Parse and return the novel categories or tags
        yield from []

    def parse_summary(self, soup: BeautifulSoup) -> str:
        # Parse and return the novel summary or synopsis
        return ''
"""

    if Feature.has_volumes in features:
        content += """
    def select_volume_tags(self, soup: BeautifulSoup) -> Generator[Tag, None, None]:
        # Select volume list item tags from the page soup
        #
        # Example:
        # yield from soup.select("#toc .vol-item")
        yield from []

    def parse_volume_item(self, tag: Tag, id: int) -> Volume:
        # Parse a single volume from `select_volume_tags` result
        #
        # Example:
        return Volume(
            id=id,
            title=tag.get_text(strip=True),
        )

    def select_chapter_tags(self, tag: Tag, vol: Volume, soup: BeautifulSoup) -> Generator[Tag, None, None]:
        # Select chapter list item tags from volume tag and page soup
        #
        # Example:
        # yield from tag.select("a[href]")
        yield from []

    def parse_chapter_item(self, tag: Tag, id: int, vol: Volume) -> Chapter:
        # Parse a single chapter from `select_chapter_tags` result
        #
        # Example:
        return Chapter(
            id=id,
            volume=vol.id,
            title=tag.get_text(strip=True),
            url=self.absolute_url(tag["href"]),
        )
"""
    else:
        content += """
    def select_chapter_tags(self, soup: BeautifulSoup) -> Generator[Tag, None, None]:
        # Select chapter list item tags from page soup
        #
        # Example:
        # yield from soup.select("table > li > a")
        yield from []

    def parse_chapter_item(self, tag: Tag, id: int) -> Chapter:
        # Parse a single chapter from `select_chapter_tags` result
        #
        # Example:
        return Chapter(
            id=id,
            title=tag.get_text(strip=True),
            url=self.absolute_url(tag["href"]),
        )
"""

    content += """
    def select_chapter_body(self, soup: BeautifulSoup) -> Optional[Tag]:
        # Select the tag containing the chapter content text
        #
        # Example:
        # return soup.select_one(".chapter-content")
        raise NotImplementedError()
"""

    return content


def _fill_with_openai(url: str, stub: str) -> str:
    client = OpenAI(api_key=ctx.config.app.openai_key)

    print(f"[i]Complete the stub functions from [cyan]{url}[/cyan][/i]")
    content_prompt = f"""
You are given the URL of a novel-hosting website: `{url}`.

Fetch the site content. Identify any novel available on the site, and generate Python code that completes the functions in the class below:

```
{stub}
```

Tasks:
- Fetch page content from the given URL.
- Locate and retrieve any novel detail page.
- If a volume list cannot be determined, return a placeholder value.
- If a chapter list cannot be determined, return a placeholder value.
- Identify and fetch a chapter content page to supply data for `select_chapter_body`.

Requirements:
- Output valid Python code only.
- Do not include explanations, comments, or markdown fences.
- Implement a function only if sufficient data is available; otherwise leave it unimplemented.
- Do not leave any unused imports
"""

    try:
        response = client.chat.completions.create(
            model="gpt-5.1",
            messages=[
                {"role": "system", "content": "Output Python code only."},
                {"role": "user", "content": content_prompt},
            ],
        )
        code = response.choices[0].message.content
        if not code:
            raise Exception("No code content in response")
        return code
    except Exception:
        logger.error("Failed to generate code", exc_info=True)
        return stub
