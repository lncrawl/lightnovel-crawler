# -*- coding: utf-8 -*-
"""

This is a sample using the SearchableSoupTemplate and ChapterOnlySoupTemplate as the template.
It should be able to do searching and generating only chapter list excluding volumes list.

Put your source file inside the language folder. The `en` folder has too many
files, therefore it is grouped using the first letter of the domain name.
"""
import logging
import re
from typing import Generator, List
from urllib.parse import urlencode

from bs4 import BeautifulSoup, Tag

from lncrawl.models import Chapter, SearchResult
from lncrawl.templates.soup.chapter_only import ChapterOnlySoupTemplate
from lncrawl.templates.soup.searchable import SearchableSoupTemplate

logger = logging.getLogger(__name__)


class MyCrawlerName(SearchableSoupTemplate, ChapterOnlySoupTemplate):
    base_url = ["https://novelbuddy.io/"]

    has_mtl = True

    def initialize(self) -> None:
        # You can customize `TextCleaner` and other necessary things.
        pass

    def select_search_items(self, query: str) -> Generator[Tag, None, None]:
        # The query here is the input from user.
        params = {"q": query}
        soup = self.get_soup(f"{self.home_url}search?{urlencode(params)}")
        yield from soup.select("div.book-item")
        pass

    def parse_search_item(self, tag: Tag) -> SearchResult:
        # The tag here comes from self.select_search_items
        return SearchResult(
            title=tag.select_one("div.title h3 a").text.strip(),
            url=f"{self.home_url}{tag.select_one('div.title h3 a')['href']}"
        )

    def get_novel_soup(self) -> BeautifulSoup:
        return self.get_soup(self.novel_url)

    def parse_title(self, soup: BeautifulSoup) -> str:
        return soup.select_one("div.name.box h1").text.strip()

    def parse_cover(self, soup: BeautifulSoup) -> str:
        return f"https:{soup.select_one('div.img-cover img')['data-src']}"

    def parse_authors(self, soup: BeautifulSoup) -> List[str]:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        if soup.select("div.meta.box.mt-1.p-10")[0].select_one("strong") != "Authors":
            return ["Unknown"]
        authors = soup.select("div.meta.box.mt-1.p-10")[0].select("a")
        return [author.text.strip() for author in authors]

    def parse_genres(self, soup: BeautifulSoup) -> List[str]:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        for p in soup.select("div.meta.box.mt-1.p-10 p"):
            if p.select_one("strong") == "Genre":
                return [a.text.strip() for a in p.select("a")]
        return ["Unknown"]

    def parse_summary(self, soup: BeautifulSoup) -> str:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        return soup.select_one("div.section-body.summary span").text.strip()

    def select_chapter_tags(self, soup: BeautifulSoup) -> Generator[Tag, None, None]:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        script = soup.select_one("div.layout script").text
        pattern = r'(var|let|const)\s+(\w+)\s*=\s*(.*?);'
        matches = re.findall(pattern, script)
        variables = {}
        for _, name, value in matches:
            variables[name] = value.strip()
        chapters_soup = self.get_soup(f"https://novelbuddy.io/api/manga/{variables['bookId']}/chapters?source=detail")
        yield from chapters_soup.select("ul li")[::-1]
        pass

    def parse_chapter_item(self, tag: Tag, id: int) -> Chapter:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        return Chapter(
            id=id,
            title=tag.select_one("strong").text.strip(),
            url=f"{self.home_url}{tag.select_one('a')['href']}",
        )

    def select_chapter_body(self, soup: BeautifulSoup) -> Tag:
        # The soup here is the result of `self.get_soup(chapter.url)`
        return soup.select_one("div.chapter__content div.content-inner")

    def index_of_chapter(self, url: str) -> int:
        return int(url.split("/")[-1].split("-")[1])
