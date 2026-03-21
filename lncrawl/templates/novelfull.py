import re
from typing import Generator
from urllib.parse import urlencode

from lncrawl.core.soup import PageSoup
from lncrawl.exceptions import LNException
from lncrawl.models import Chapter, SearchResult
from lncrawl.templates.soup.chapter_only import ChapterOnlySoupTemplate
from lncrawl.templates.soup.searchable import SearchableSoupTemplate


class NovelFullTemplate(SearchableSoupTemplate, ChapterOnlySoupTemplate):
    is_template = True

    def select_search_items(self, query: str) -> Generator[PageSoup, None, None]:
        params = {"keyword": query}
        soup = self.get_soup(f"{self.home_url}search?{urlencode(params)}")
        yield from soup.select("#list-page .row h3[class*='title'] > a")

    def parse_search_item(self, tag: PageSoup) -> SearchResult:
        return SearchResult(
            url=self.absolute_url(tag["href"]),
            title=tag.get_attr("title") or tag.text,
        )

    def parse_title(self, soup: PageSoup) -> str:
        return soup.select_one("h3.title").text

    def parse_cover(self, soup: PageSoup):
        tag = soup.select_one(".book img")
        if not tag:
            return None
        if tag.has_attr("data-src"):
            return self.absolute_url(tag["data-src"])
        if tag.has_attr("src"):
            return self.absolute_url(tag["src"])

    def parse_authors(self, soup: PageSoup):
        selectors = [
            ".info a[href*='/a/']",
            ".info a[href*='/au/']",
            ".info a[href*='author']",
        ]
        for a in soup.select(','.join(selectors)):
            yield a.text.strip()

    def parse_genres(self, soup: PageSoup):
        info_section = soup.select_one(".info, .info-meta")
        if not info_section:
            return
        for li in info_section.select("li"):
            header = li.select_one("h3")
            if not header or ("Genre" not in header.text and "Tag" not in header.text):
                continue

            for a in li.select("a"):
                if a and a.text.strip():
                    yield a.text.strip()

    def parse_summary(self, soup: PageSoup) -> str:
        return self.cleaner.extract_contents(soup.select_one(".desc-text"))

    def select_chapter_tags(self, soup: PageSoup):
        nl_id = soup.select_one("#rating[data-novel-id]")["data-novel-id"]
        if not nl_id:
            raise LNException("No novel_id found")

        script = soup.find("script", string=re.compile(r"ajaxChapterOptionUrl\s+="))
        if script:
            url = f"{self.home_url}ajax-chapter-option?novelId={nl_id}"
        else:
            url = f"{self.home_url}ajax/chapter-archive?novelId={nl_id}"

        soup = self.get_soup(url)
        yield from soup.select("ul.list-chapter > li > a[href], select > option[value]")

    def parse_chapter_item(self, tag: PageSoup, id: int) -> Chapter:
        return Chapter(
            id=id,
            title=tag.text,
            url=self.absolute_url(tag["href"] or tag["value"]),
        )

    def select_chapter_body(self, soup: PageSoup) -> PageSoup:
        contents = soup.select_one("#chr-content, #chapter-content")
        for ads in contents.select("div"):
            ads.decompose()
        return contents
