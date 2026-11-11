# -*- coding: utf-8 -*-
from concurrent.futures import Future
import logging
import re
from typing import Iterable, List, Optional

from lncrawl.core import Chapter, Novel, PageSoup, SoupTemplate, Volume

logger = logging.getLogger(__name__)

# Each row ends with how long ago the chapter went up.
POSTED_AGO = re.compile(r"\s*\d+\s+(?:second|minute|hour|day|week|month|year)s?\s+ago\s*$", re.I)
SPACES = re.compile(r"\s+")
CHAPTER_LINKS = "ul.chapter-list li a[href]"


class NovelPhoenixCrawler(SoupTemplate):
    base_url = ["https://novelphoenix.com/"]

    novel_title_selector = "h1"

    # `article` and `main` also hold the text, but each wraps it in the post header.
    chapter_body_selector = "#content"

    def select_chapter_tags(
        self, tag: PageSoup, novel: Novel, volume: Optional[Volume] = None
    ) -> Iterable[PageSoup]:
        # The novel page links only the newest chapter; the list lives one level down.
        url = self.absolute_url(novel.url).split("?")[0].rstrip("/") + "/chapters"
        soup = self.scraper.get_soup(url)
        yield from soup.select(CHAPTER_LINKS)

        # The list shows 100 chapters per page; the range picker has one option per page.
        page_count = len(soup.select('select[aria-label="Chapter range"] option'))
        futures: List[Future[PageSoup]] = [
            self.taskman.submit_task(self.scraper.get_soup, f"{url}?page={p}")
            for p in range(2, page_count + 1)
        ]
        for page in self.taskman.resolve(futures, desc="TOC", unit="page"):
            if page:
                yield from page.select(CHAPTER_LINKS)

    def parse_chapter_title(self, soup: PageSoup, chapter: Chapter) -> None:
        # A row runs number, title and timestamp together with no separators between the
        # spans, so the text has to be read with one inserted.
        text = SPACES.sub(" ", soup.get_text(" ", strip=True))
        chapter.title = POSTED_AGO.sub("", text).strip()
