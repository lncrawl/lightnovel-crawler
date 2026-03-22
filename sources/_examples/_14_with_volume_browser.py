# -*- coding: utf-8 -*-
"""
# TODO: Read the TODOs carefully and remove all existing comments in this file.

This is a sample using the ChapterWithVolumeBrowserTemplate as the template.
It provides a wrapper around the GeneralBrowserTemplate that generates both
volumes list and chapter list.

Put your source file inside the language folder. The `en` folder has too many
files, therefore it is grouped using the first letter of the domain name.
"""

import logging
from typing import Generator

from lncrawl.core import PageSoup
from lncrawl.models import Chapter, Volume
from lncrawl.templates.browser.with_volume import ChapterWithVolumeBrowserTemplate

logger = logging.getLogger(__name__)


# TODO: You can safely delete all [OPTIONAL] methods if you do not need them.
class MyCrawlerName(ChapterWithVolumeBrowserTemplate):
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

    # TODO: [OPTIONAL] Open the Novel URL in the browser
    def visit_novel_page_in_browser(self) -> None:
        self.visit(self.novel_url)

    # TODO: [OPTIONAL] Get a PageSoup instance from the self.novel_url
    def get_novel_soup(self) -> PageSoup:
        return self.get_soup(self.novel_url)

    # TODO: [OPTIONAL] Parse and return the novel title in the browser
    def parse_title_in_browser(self) -> str:
        return self.parse_title(self.browser.soup)

    # TODO: [REQUIRED] Parse and return the novel title
    def parse_title(self, soup: PageSoup) -> str:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        raise NotImplementedError()

    # TODO: [OPTIONAL] Parse and return the novel cover image in the browser
    def parse_cover_in_browser(self) -> str:
        return self.parse_cover(self.browser.soup)

    # TODO: [REQUIRED] Parse and return the novel cover
    def parse_cover(self, soup: PageSoup) -> str:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        return ""

    # TODO: [OPTIONAL] Parse and return the novel author in the browser
    def parse_authors_in_browser(self) -> Generator[str, None, None]:
        yield from self.parse_authors(self.browser.soup)

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

    # TODO: [OPTIONAL] Parse and return the novel author in the browser
    def parse_genres_in_browser(self) -> Generator[str, None, None]:
        yield from self.parse_genres(self.browser.soup)

    # TODO: [OPTIONAL] Parse and return the novel categories or tags
    def parse_genres(self, soup: PageSoup) -> Generator[str, None, None]:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        #
        # See the `parse_authors` example above for a similar implementation.
        yield from []

    # TODO: [OPTIONAL] Parse and return the novel summary or synopsis in the browser
    def parse_summary_in_browser(self) -> str:
        return self.parse_summary(self.browser.soup)

    # TODO: [OPTIONAL] Parse and return the novel summary or synopsis
    def parse_summary(self, soup: PageSoup) -> str:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        return ""

    # TODO: [OPTIONAL] Open the Chapter URL in the browser
    def visit_chapter_page_in_browser(self, chapter: Chapter) -> None:
        self.visit(chapter.url)

    # TODO: [OPTIONAL] Select volume list item tags from the browser
    def select_volume_tags_in_browser(self) -> Generator[PageSoup, None, None]:
        return self.select_volume_tags(self.browser.soup)

    # TODO: [REQUIRED] Select volume list item tags from the page soup
    def select_volume_tags(self, soup: PageSoup) -> Generator[PageSoup, None, None]:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        #
        # Example: yield from soup.select("#toc .vol-item")
        yield from []

    # TODO: [OPTIONAL] Parse a single volume from volume list item tag when using browser
    def parse_volume_item_in_browser(self, tag: PageSoup, id: int) -> Volume:
        return self.parse_volume_item(tag, id)

    # TODO: [REQUIRED] Parse a single volume from volume list item tag
    def parse_volume_item(self, tag: PageSoup, id: int) -> Volume:
        # The tag here comes from `self.select_volume_tags`
        # The id here is the next available volume id
        return Volume(
            id=id,
            title=tag.get_text(strip=True),
        )

    # TODO: [OPTIONAL] Select chapter list item tags from volume tag and page soup when in browser
    def select_chapter_tags_in_browser(self, tag: PageSoup, vol: Volume) -> Generator[PageSoup, None, None]:
        return self.select_chapter_tags(tag, vol, self.browser.soup)

    # TODO: [REQUIRED] Select chapter list item tags from volume tag and page soup
    def select_chapter_tags(self, tag: PageSoup, vol: Volume, soup: PageSoup) -> Generator[PageSoup, None, None]:
        # The tag here comes from `self.select_volume_tags`
        # The vol here comes from `self.parse_volume_item`
        #
        # Example: yield from tag.select(".chapter-item")
        yield from []

    # TODO: [REQUIRED] Parse a single chapter from chapter list item tag
    def parse_chapter_item(self, tag: PageSoup, id: int, vol: Volume) -> Chapter:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        return Chapter(
            id=id,
            volume=vol.id,
            title=tag.get_text(strip=True),
            url=self.absolute_url(tag["href"]),
        )

    # TODO: [OPTIONAL] Select the tag containing the chapter text in the browser
    def select_chapter_body_in_browser(self) -> PageSoup:
        return self.select_chapter_body(self.browser.soup)

    # TODO: [REQUIRED] Select the tag containing the chapter text
    def select_chapter_body(self, soup: PageSoup) -> PageSoup:
        # The soup here is the result of `self.get_soup(chapter.url)`
        #
        # Example: return soup.select_one(".m-read .txt")
        raise NotImplementedError()
