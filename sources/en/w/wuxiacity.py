# -*- coding: utf-8 -*-

import logging
from typing import List
from urllib.parse import quote_plus

from lncrawl.core import Crawler
from lncrawl.models import Chapter, SearchResult, Volume

logger = logging.getLogger(__name__)

search_url = "https://www.wuxia.city/search?q=%s"


class WuxiaCityCrawler(Crawler):
    base_url = [
        "https://wuxia.city",
    ]

    # This source offers no manga/manhua/manhwa.
    has_manga = False

    # Set True if this source contains machine translations.
    has_mtl = True

    def search_novel(self, query: str) -> List[SearchResult]:
        query = quote_plus(str(query).lower())
        soup = self.get_soup(search_url % query)
        entries = [
            (
                e.select_one("div.book-caption a[href] h4"),
                e.select_one("p.book-genres a"),
                e.select_one("span.star[style]").get("style").split(" ")[1].strip(),
            )
            for e in soup.find_all("li", class_="section-item")
        ]
        print(entries)
        return [
            SearchResult(
                title=e[0].text,
                url=self.absolute_url(e[0].parent["href"]),
                info=f"{e[1].text} | Score: {e[2].strip()}",
            )
            for e in entries
        ]

    def read_novel_info(self):
        soup = self.get_soup(f"{self.novel_url}/table-of-contents")

        self.novel_title = soup.select_one("h1.book-name").text
        self.novel_author = soup.select_one("dl.author dd").text
        self.novel_cover = self.absolute_url(soup.select_one("div.book-img img[src]").get("src"))

        vol_id = 0
        self.volumes.append(Volume(id=vol_id))
        chapterItems = soup.select("ul.chapters li.oneline")
        for chapter in chapterItems:
            a = chapter.select_one("a.chapter-item")
            self.chapters.append(
                Chapter(
                    volume=vol_id,
                    id=len(self.chapters) + 1,
                    url=self.absolute_url(a["href"]),
                    title=a.find("p").text,
                    hash=a["href"].split("/")[-1],
                )
            )
        self.chapters.sort(key=lambda c: c["id"])

    def download_chapter_body(self, chapter):
        soup = self.get_soup(chapter["url"])
        return self.cleaner.extract_contents(soup.find("div", class_="chapter-content"))
