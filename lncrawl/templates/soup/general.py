import logging
from abc import abstractmethod
from typing import Generator, Optional, Union

from ...core.soup import PageSoup
from ...exceptions import LNException
from ...models import Chapter, Volume
from .._base import CrawlerTemplate

logger = logging.getLogger(__name__)


class GeneralSoupTemplate(CrawlerTemplate):
    def read_novel_info(self) -> None:
        soup = self.get_novel_soup()

        try:
            self.novel_title = self.parse_title(soup)
        except Exception as e:
            raise LNException("Failed to parse novel title", e)

        try:
            self.novel_cover = self.parse_cover(soup)
        except Exception as e:
            logger.warning("Failed to parse novel cover | %s", e)

        try:
            authors = set(list(self.parse_authors(soup)))
            self.novel_author = ", ".join(authors)
        except Exception as e:
            logger.warning("Failed to parse novel authors | %s", e)

        try:
            self.novel_tags = list(set(self.parse_genres(soup)))
        except Exception as e:
            logger.warning("Failed to parse novel tags | %s", e)

        try:
            self.novel_synopsis = self.parse_summary(soup) or ""
        except Exception as e:
            logger.warning("Failed to parse novel synopsis | %s", e)

        for item in self.parse_chapter_list(soup):
            if isinstance(item, Chapter):
                self.chapters.append(item)
            elif isinstance(item, Volume):
                self.volumes.append(item)

    def get_novel_soup(self) -> PageSoup:
        return self.get_soup(self.novel_url)

    @abstractmethod
    def parse_title(self, soup: PageSoup) -> str:
        """Parse and return the novel title"""
        raise NotImplementedError()

    @abstractmethod
    def parse_cover(self, soup: PageSoup) -> Optional[str]:
        """Parse and return the novel cover image"""
        return None

    def parse_authors(self, soup: PageSoup) -> Generator[str, None, None]:
        """Parse and return the novel authors"""
        yield from []

    def parse_genres(self, soup: PageSoup) -> Generator[str, None, None]:
        """Parse and return the novel categories"""
        yield from []

    def parse_summary(self, soup: PageSoup) -> Optional[str]:
        """Parse and return the novel summary or synopsis"""
        return None

    @abstractmethod
    def parse_chapter_list(
        self, soup: PageSoup
    ) -> Generator[Union[Chapter, Volume], None, None]:
        """Parse and set the volumes and chapters"""
        raise NotImplementedError()

    def download_chapter_body(self, chapter: Chapter) -> str:
        soup = self.get_soup(chapter.url)
        body = self.select_chapter_body(soup)
        if not body:
            raise LNException('No chapter contents')
        return self.parse_chapter_body(body)

    @abstractmethod
    def select_chapter_body(self, soup: PageSoup) -> PageSoup:
        """Select the tag containing the chapter text"""
        raise NotImplementedError()

    def parse_chapter_body(self, tag: PageSoup) -> str:
        """Extract the clean HTML content from the tag containing the chapter text"""
        return self.cleaner.extract_contents(tag)
