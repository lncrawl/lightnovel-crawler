# -*- coding: utf-8 -*-
import logging
import re
from typing import Iterable, Optional

from lncrawl.core import Chapter, Novel, PageSoup, SoupTemplate, Volume

logger = logging.getLogger(__name__)

# Each row ends with how long ago the chapter went up.
POSTED_AGO = re.compile(r"\s*\d+\s+(?:second|minute|hour|day|week|month|year)s?\s+ago\s*$", re.I)
SPACES = re.compile(r"\s+")


class NovelPhoenixCrawler(SoupTemplate):
    base_url = ["https://novelphoenix.com/"]

    novel_title_selector = "h1"

    # `article` and `main` also hold the text, but each wraps it in the post header.
    chapter_body_selector = "#content"

    def select_chapter_tags(
        self, tag: PageSoup, novel: Novel, volume: Optional[Volume] = None
    ) -> Iterable[PageSoup]:
        base = self.absolute_url(novel.url).split("?")[0].rstrip("/") + "/chapters"
        seen, result = set(), []
        for page in range(1, 40):  # temporary low cap while testing
            url = base if page == 1 else f"{base}?page={page}"
            logger.info(f"Fetching chapter list page {page}: {url}")
            soup = self.scraper.get_soup(url)
            links = soup.select("ul.chapter-list li a[href]")
            new = [a for a in links if a["href"] not in seen]
            logger.info(f"page {page}: {len(links)} links, {len(new)} new")
            if not new:
                break
            for a in new:
                seen.add(a["href"])
                result.append(a)
        return result

    def parse_chapter_title(self, soup: PageSoup, chapter: Chapter) -> None:
        # A row runs number, title and timestamp together with no separators between the
        # spans, so the text has to be read with one inserted.
        text = SPACES.sub(" ", soup.get_text(" ", strip=True))
        chapter.title = POSTED_AGO.sub("", text).strip()
