# -*- coding: utf-8 -*-
"""

This is a sample using the SearchableSoupTemplate and ChapterOnlySoupTemplate as the template.
It should be able to do searching and generating only chapter list excluding volumes list.

Put your source file inside the language folder. The `en` folder has too many
files, therefore it is grouped using the first letter of the domain name.
"""
import logging
from typing import Generator, List
from urllib.parse import urlencode

from bs4 import BeautifulSoup, Tag

from lncrawl.models import Chapter, SearchResult
from lncrawl.templates.soup.chapter_only import ChapterOnlySoupTemplate
from lncrawl.templates.soup.searchable import SearchableSoupTemplate

logger = logging.getLogger(__name__)
search_url = "https://massnovel.fr/?s="


class MassNovel(SearchableSoupTemplate, ChapterOnlySoupTemplate):
    base_url = ["https://massnovel.fr/"]

    has_mtl = True

    def initialize(self) -> None:
        # You can customize `TextCleaner` and other necessary things.
        pass

    def select_search_items(self, query: str) -> Generator[Tag, None, None]:
        # The query here is the input from user.
        params = {"s": query}
        soup = self.post_soup(f"{self.base_url[0]}?{urlencode(params)}&post_type=wp-manga&op=&author=&artist=&release=&adult=", params=params)
        yield from soup.select("div.row.c-tabs-item__content")
        pass

    def parse_search_item(self, tag: Tag) -> SearchResult:
        # The tag here comes from self.select_search_items
        title = tag.select_one("div.tab-summary div.post-title h3 a").text.strip()
        url = tag.select_one("div.tab-summary div.post-title h3 a")["href"]

        search_result = SearchResult(
            title=title,
            url=url
        )
        return search_result

    def get_novel_soup(self) -> BeautifulSoup:
        return self.get_soup(self.novel_url)

    def parse_title(self, soup: BeautifulSoup) -> str:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        return soup.select_one("div.tab-summary div.summary_content div.manga-title h2").text.strip()

    def parse_cover(self, soup: BeautifulSoup) -> str:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        return soup.select_one("div.tab-summary div.summary_image a img")["src"]

    def parse_authors(self, soup: BeautifulSoup) -> List[str]:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        author = soup.select_one("div.tab-summary div.summary_content div.manga-data div.manga-author span a").text.strip()
        return [author]

    def parse_genres(self, soup: BeautifulSoup) -> List[str]:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        #
        genre = soup.select_one("div.tab-summary div.summary_content div.manga-data div.manga-author span a").text.strip()
        return [genre]

    def parse_summary(self, soup: BeautifulSoup) -> str:
        summary = soup.select("div.tab-content div div.manga-extra-info__content div div.excerpt-content p")
        complet_summary = "\n".join([line.text.strip() for line in summary])
        return complet_summary

    def select_chapter_tags(self, soup: BeautifulSoup) -> Generator[Tag, None, None]:
        # The soup here is the result of `self.get_soup(self.novel_url)`

        chapters_url = f"{self.novel_url}ajax/chapters/?t=1"
        soup = self.post_soup(chapters_url)
        yield from soup.select("div.page-content-listing ul.main li")[::-1]
        pass

    def parse_chapter_item(self, tag: Tag, id: int) -> Chapter:
        # The soup here is the result of `self.get_soup(self.novel_url)`

        return Chapter(
            id=id,
            title=tag.select_one("a").text.strip(),
            url=tag.select_one("a")["href"],
        )

    def select_chapter_body(self, soup: BeautifulSoup) -> Tag:
        # The soup here is the result of `self.get_soup(chapter.url)`
        return soup.select_one("div.text-left")

    def index_of_chapter(self, url: str) -> int:
        return int(url.split("/")[-1].split("-")[1])
