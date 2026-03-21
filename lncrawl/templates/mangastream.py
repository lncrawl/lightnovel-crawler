from typing import Generator
from urllib.parse import urlencode

from lncrawl.core.soup import PageSoup
from lncrawl.models import Chapter, SearchResult, Volume
from lncrawl.templates.browser.optional_volume import \
    OptionalVolumeBrowserTemplate
from lncrawl.templates.browser.searchable import SearchableBrowserTemplate


class MangaStreamTemplate(SearchableBrowserTemplate, OptionalVolumeBrowserTemplate):
    is_template = True

    def initialize(self) -> None:
        self.cleaner.bad_tags.update(["h3"])

    def select_search_items(self, query: str):
        params = dict(s=query)
        soup = self.get_soup(f"{self.home_url}?{urlencode(params)}")
        yield from soup.select(".listupd > article")

    def select_search_items_in_browser(self, query: str):
        params = dict(s=query)
        self.visit(f"{self.home_url}?{urlencode(params)}")
        yield from self.browser.soup.select(".listupd > article")

    def parse_search_item(self, tag: PageSoup) -> SearchResult:
        a = tag.select_one("a.tip")
        title = tag.select_one("span.ntitle")
        info = tag.select_one("span.nchapter")
        return SearchResult(
            title=(title or a).text,
            url=self.absolute_url(a["href"]),
            info=info.text,
        )

    def parse_title(self, soup: PageSoup) -> str:
        return soup.select_one("h1.entry-title").text

    def parse_title_in_browser(self) -> str:
        self.browser.wait("h1.entry-title")
        return self.parse_title(self.browser.soup)

    def parse_cover(self, soup: PageSoup):
        tag = soup.select_one(
            ".thumbook img, meta[property='og:image'],.sertothumb img"
        )
        if not tag:
            return None
        if tag.has_attr("data-src"):
            return self.absolute_url(tag["data-src"])
        if tag.has_attr("src"):
            return self.absolute_url(tag["src"])
        if tag.has_attr("content"):
            return self.absolute_url(tag["content"])

    def parse_authors(self, soup: PageSoup):
        for a in soup.select(".spe a[href*='/writer/']"):
            yield a.text.strip()

    def parse_genres(self, soup: PageSoup):
        for a in soup.select(".bottom.tags a[href*='/tag/']"):
            yield a.text.strip()

    def parse_summary(self, soup: PageSoup) -> str:
        return self.cleaner.extract_contents(soup.select_one(".entry-content"))

    def select_volume_tags(self, soup: PageSoup):
        yield from ()

    def parse_volume_item(self, tag: PageSoup, id: int) -> Volume:
        return Volume(id=id)

    def select_chapter_tags(self, parent: PageSoup) -> Generator[PageSoup, None, None]:
        first_li = parent.select_one(".eplister li")
        li_class = first_li.get_attr("class", "") if first_li else ""
        data_num = first_li.get_attr("data-num", "0") if first_li else "0"
        chapters = parent.select(".eplister li a")
        if data_num == '1' or "tseplsfrst" not in str(li_class):
            yield from reversed(list(chapters))
        else:
            yield from chapters

    def parse_chapter_item(self, tag: PageSoup, id: int, vol: Volume) -> Chapter:
        return Chapter(
            id=id,
            url=self.absolute_url(tag["href"]),
            title=tag.select_one(".epl-title").text,
        )

    def select_chapter_body(self, soup: PageSoup) -> PageSoup:
        return soup.select_one("#readernovel, #readerarea, .entry-content")

    def visit_chapter_page_in_browser(self, chapter: Chapter) -> None:
        self.visit(chapter.url)
        self.browser.wait("#readernovel, #readerarea, .entry-content,.mainholder")
