from abc import abstractmethod
from typing import Generator

from ...core.soup import PageSoup
from ...models import Chapter
from .general import GeneralSoupTemplate


class ChapterOnlySoupTemplate(GeneralSoupTemplate):
    def parse_chapter_list(self, soup: PageSoup) -> Generator[Chapter, None, None]:
        chap_id = 0
        for tag in self.select_chapter_tags(soup):
            chap_id += 1
            yield self.parse_chapter_item(tag, chap_id)

    @abstractmethod
    def select_chapter_tags(self, soup: PageSoup) -> Generator[PageSoup, None, None]:
        """Select chapter list item tags from the page soup"""
        raise NotImplementedError()

    @abstractmethod
    def parse_chapter_item(self, tag: PageSoup, id: int) -> Chapter:
        """Parse a single chapter from chapter list item tag"""
        raise NotImplementedError()
