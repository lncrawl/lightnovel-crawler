# -*- coding: utf-8 -*-
"""
# TODO: Read the TODOs carefully and remove all existing comments in this file.

This is a sample using the SearchableSoupTemplate and OptionalVolumeSoupTemplate
as the template. It should be able to do searching and generating the chapter list.
It can also optionally generate the volume list.

Put your source file inside the language folder. The `en` folder has too many
files, therefore it is grouped using the first letter of the domain name.
"""

import logging
from typing import Generator

from lncrawl.core import PageSoup
from lncrawl.models import Chapter, SearchResult, Volume
from lncrawl.templates.soup.optional_volume import OptionalVolumeSoupTemplate
from lncrawl.templates.soup.searchable import SearchableSoupTemplate

logger = logging.getLogger(__name__)


# TODO: You can safely delete all [OPTIONAL] methods if you do not need them.
class MyCrawlerName(SearchableSoupTemplate, OptionalVolumeSoupTemplate):
    # TODO: [REQUIRED] Provide the URLs supported by this crawler.
    base_url = ["http://sample.url/"]

    # TODO: [OPTIONAL] Set True if this crawler is for manga/manhua/manhwa.
    has_manga = False

    # TODO: [OPTIONAL] Set True if this source contains machine translations.
    has_mtl = False

    # TODO: [OPTIONAL] This is called before all other methods.
    def initialize(self) -> None:
        # You can customize `TextCleaner` and other necessary things.
        pass

    # TODO: [OPTIONAL] This is called once per session before searching and fetching novel info.
    def login(self, username_or_email: str, password_or_token: str) -> None:
        pass

    # TODO: [REQUIRED] Select novel items found in search page from the query
    def select_search_items(self, query: str) -> Generator[PageSoup, None, None]:
        # The query here is the input from user.
        #
        # Example:
        #   params = {"searchkey": query}
        #   soup = self.post_soup(f"{self.home_url}search?{urlencode(params)}")
        #   yield from soup.select(".col-content .con .txt h3 a")
        yield from []

    # TODO: [REQUIRED] Parse a tag and return single search result
    def parse_search_item(self, tag: PageSoup) -> SearchResult:
        # The tag here comes from self.select_search_items
        return SearchResult(
            title=tag.get_text(strip=True),
            url=self.absolute_url(tag["href"]),
        )

    # TODO: [OPTIONAL] Get a PageSoup instance from the self.novel_url
    def get_novel_soup(self) -> PageSoup:
        return super().get_novel_soup()

    # TODO: [REQUIRED] Parse and return the novel title
    def parse_title(self, soup: PageSoup) -> str:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        raise NotImplementedError()

    # TODO: [REQUIRED] Parse and return the novel cover
    def parse_cover(self, soup: PageSoup) -> str:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        return ""

    # TODO: [OPTIONAL] Parse and return the novel authors
    def parse_authors(self, soup: PageSoup) -> Generator[str, None, None]:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        #
        # Example 1: <a single author example>
        #   tag = soup.find("strong", string="Author:")
        #   assert tag
        #   yield tag.next_sibling.text.strip()
        #
        # Example 2: <multiple authors example>
        #   for a in soup.select(".m-imgtxt a[href*='/authors/']"):
        #       yield a.text.strip()
        yield from []

    # TODO: [OPTIONAL] Parse and return the novel categories or tags
    def parse_genres(self, soup: PageSoup) -> Generator[str, None, None]:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        #
        # See the `parse_authors` example above for a similar implementation.
        yield from []

    # TODO: [OPTIONAL] Parse and return the novel summary or synopsis
    def parse_summary(self, soup: PageSoup) -> str:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        return ""

    # TODO: [OPTIONAL] Select volume list item tags from the page soup
    def select_volume_tags(self, soup: PageSoup) -> Generator[PageSoup, None, None]:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        #
        # Example: yield from soup.select("#toc .vol-item")
        yield from []

    # TODO: [OPTIONAL] Parse a single volume from volume list item tag
    def parse_volume_item(self, tag: PageSoup, id: int) -> Volume:
        # The tag here comes from `self.select_volume_tags`
        # The id here is the next available volume id
        #
        # Example:
        return Volume(
            id=id,
            title=tag.get_text(strip=True),
        )

    # TODO: [REQUIRED] Select chapter list item tags from volume tag and page soup
    def select_chapter_tags(self, parent: PageSoup) -> Generator[PageSoup, None, None]:
        # The parent here is either `html` or comes from `self.select_volume_tags`
        #
        # Example: yield from tag.select(".chapter-item")
        yield from []

    # TODO: [REQUIRED] Parse a single chapter from chapter list item tag
    def parse_chapter_item(self, tag: PageSoup, id: int, vol: Volume) -> Chapter:
        # The tag here comes from `self.select_chapter_tags`
        # The vol here comes from `self.parse_volume_item`
        # The id here is the next available chapter id
        return Chapter(
            id=id,
            volume=vol.id,
            title=tag.get_text(strip=True),
            url=self.absolute_url(tag["href"]),
        )

    # TODO: [REQUIRED] Select the tag containing the chapter text
    def select_chapter_body(self, soup: PageSoup) -> PageSoup:
        # The soup here is the result of `self.get_soup(chapter.url)`
        #
        # Example: return soup.select_one(".m-read .txt")
        raise NotImplementedError()
