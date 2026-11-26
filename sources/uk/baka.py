from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from lncrawl.core import Chapter, Novel, SearchResult, SoupTemplate
from lncrawl.exceptions import LNException

_CHAPTER_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


class BakaCrawler(SoupTemplate):
    base_url = ["https://baka.in.ua/"]
    language = "uk"
    request_rate_limit = 1
    can_search = True
    chapter_body_selector = "#user-content"

    def build_search_url(self, query: str) -> str:
        search_url = urljoin(self.base_url[0], "search")
        return f"{search_url}?{urlencode({'search[]': query})}"

    def search(self, query: str) -> Iterable[SearchResult]:
        soup = self.scraper.get_soup(self.build_search_url(query))
        for title_tag in soup.select("h3"):
            result_card = title_tag.closest("a")
            if not result_card:
                continue

            href = result_card.get("href")
            if not href or not href.startswith("/fictions/"):
                continue

            yield SearchResult(
                title=title_tag.text.strip(),
                url=urljoin(self.base_url[0], href),
            )

    def read_novel(self, novel: Novel) -> None:
        parts = [part for part in urlsplit(novel.url).path.split("/") if part]
        if len(parts) != 2 or parts[0] != "fictions":
            raise ValueError(f"Invalid Baka fiction URL: {novel.url}")

        parsed_novel_url = urlsplit(novel.url)
        page_url = urlunsplit(
            (parsed_novel_url.scheme, parsed_novel_url.netloc, f"/{'/'.join(parts)}", "", "")
        )
        soup = self.scraper.get_soup(page_url)
        novel.title = soup.select_one("#fiction-panel-about h1, h1").text.strip()
        novel.cover_url = urljoin(
            page_url, soup.select_one('meta[property="og:image"]').get("content")
        )
        novel.author = soup.select_one('meta[name="author"]').get("content")
        novel.synopsis = soup.select_one("#fiction-description").text.strip()
        novel.tags = [
            tag.text.strip()
            for tag in soup.select('#fiction-panel-about a[href^="/fictions/genres/"] span')
            if tag.text.strip()
        ]
        novel.language = self.language

        sections = soup.select("#fiction-panel-chapters [data-section-key]")
        chapters = []
        for section_index, section in enumerate(sections):
            section_url_tag = section.select_one(
                "[data-chapter-section-url], [data-chapter-group-pager-url-value]"
            )
            section_url = section_url_tag.get("data-chapter-section-url") or section_url_tag.get(
                "data-chapter-group-pager-url-value"
            )
            if not section_url:
                continue

            parsed_url = urlsplit(urljoin(page_url, section_url))
            query = dict(parse_qsl(parsed_url.query, keep_blank_values=True))
            query.update({"order": "asc", "offset": "0", "limit": "all"})
            rows_url = urlunsplit(
                (parsed_url.scheme, parsed_url.netloc, parsed_url.path, urlencode(query), "")
            )
            rows = self.scraper.get_soup(
                rows_url,
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
            for row_index, row in enumerate(rows.select("li")):
                chapter_link = row.select_one('a[href^="/chapters/"]')
                number_tag = row.select_one("div > span")
                if not chapter_link or not number_tag:
                    continue

                number_match = _CHAPTER_NUMBER.search(number_tag.text)
                if not number_match:
                    continue
                try:
                    chapter_number = Decimal(number_match.group().replace(",", "."))
                except InvalidOperation:
                    continue

                title_tag = chapter_link.select_one('span[class~="md:hidden"]') or chapter_link
                title = title_tag.text.strip()
                label = number_match.group()
                chapters.append(
                    (
                        chapter_number,
                        section_index,
                        row_index,
                        urljoin(page_url, chapter_link.get("href")),
                        f"Розділ {label} — {title}",
                    )
                )

        if not chapters:
            raise LNException(f"No chapters found on Baka fiction page: {page_url}")

        for _, _, _, chapter_url, title in sorted(chapters):
            novel.add_chapter(url=chapter_url, title=title)

    def download_chapter(self, chapter: Chapter) -> None:
        super().download_chapter(chapter)
