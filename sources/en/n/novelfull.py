# -*- coding: utf-8 -*-
import logging
from typing import Iterable, Optional
from urllib.parse import urlencode, urljoin

from lncrawl.core import Novel, PageSoup, Volume
from lncrawl.exceptions import LNException
from lncrawl.templates.novelfull import NovelFullTemplate

logger = logging.getLogger(__name__)


class NovelFullCrawler(NovelFullTemplate):
    base_url = [
        "http://novelfull.com/",
        "https://novelfull.com/",
        "https://novelfull.net/",
    ]

    def select_chapter_tags(
        self, tag: PageSoup, novel: Novel, volume: Optional[Volume] = None
    ) -> Iterable[PageSoup]:
        list_tag = tag.select_one("#list-chapter[data-novel-id][data-list-url]")
        if not list_tag:
            return super().select_chapter_tags(tag, novel, volume)

        novel_id = list_tag.get("data-novel-id")
        list_url = urljoin(novel.url, list_tag.get("data-list-url"))
        total_pages = int(list_tag.get("data-total-page") or 1)
        expected = int(list_tag.get("data-total-chapters") or 0)
        chapters = []
        page = 1
        while page <= total_pages:
            separator = "&" if "?" in list_url else "?"
            query = urlencode({"novelId": novel_id, "page": page})
            data = self.scraper.get_json(f"{list_url}{separator}{query}")
            if data.get("code") not in (None, 200, "200"):
                raise LNException(f"NovelFull chapter list failed on page {page}")
            if data.get("page") is not None and int(data["page"]) != page:
                raise LNException(f"NovelFull returned the wrong chapter list page: {page}")
            page_soup = PageSoup.create(data.get("html") or "")
            links = page_soup.select("li > a.con[href]") or page_soup.select("li > a[href]")
            if not links:
                raise LNException(f"NovelFull chapter list page {page} is empty")
            chapters.extend(links)
            total_pages = max(total_pages, int(data.get("totalPage") or 0))
            expected = max(expected, int(data.get("totalChapters") or 0))
            page += 1
        if expected and len(chapters) != expected:
            raise LNException(f"NovelFull expected {expected} chapters, found {len(chapters)}")
        return chapters

    def initialize(self) -> None:
        self.cleaner.bad_css.update(
            [
                'div[align="left"]',
                'img[src*="proxy?container=focus"]',
            ]
        )
