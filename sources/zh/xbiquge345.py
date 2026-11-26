# -*- coding: utf-8 -*-
"""Crawler for xbiquge345.com (PR #3160)."""

import html
import re

from lncrawl.core import Chapter, Novel, PageSoup, SoupTemplate


class Xbiquge345Crawler(SoupTemplate):
    base_url = ["https://www.xbiquge345.com/"]
    language = "zh"
    request_rate_limit = 1.0

    novel_title_selector = 'meta[property="og:novel:book_name"]'
    novel_cover_selector = 'meta[property="og:image"]'
    novel_author_selector = 'meta[property="og:novel:author"]'
    novel_synopsis_selector = 'meta[property="og:description"]'
    chapter_list_selector = "div.border ul.info a[href^='/chapter/']"
    chapter_body_selector = "div.txt"

    def build_novel_url(self, novel: Novel) -> str:
        return f"{str(novel.url).rstrip('/')}/"

    def parse_title(self, soup: PageSoup, novel: Novel) -> None:
        tag = soup.select_one(self.novel_title_selector)
        novel.title = str(tag.get("content") or "").strip()

    def parse_authors(self, soup: PageSoup, novel: Novel) -> None:
        tag = soup.select_one(self.novel_author_selector)
        novel.author = str(tag.get("content") or "").strip()

    def parse_tags(self, soup: PageSoup, novel: Novel) -> None:
        tag = soup.select_one('meta[property="og:novel:category"]')
        category = str(tag.get("content") or "").strip() if tag else ""
        novel.tags = [category] if category else []

    def parse_summary(self, soup: PageSoup, novel: Novel) -> None:
        tag = soup.select_one(self.novel_synopsis_selector)
        summary = str(tag.get("content") or "").strip()
        novel.synopsis = f"<p>{html.escape(summary)}</p>" if summary else ""

    def parse_chapter_body(self, soup: PageSoup, chapter: Chapter) -> None:
        raw_tag = getattr(soup, "_tag", soup)
        body = self.cleaner.extract_contents(raw_tag)
        body = re.sub(r"<p>一秒记住【笔趣阁小说网】.*?</p>", "", body)
        body = re.sub(
            r"<p>(?:（本章未完，请点击下一页继续阅读）)?\d+第\s*\d+\s*章\(第\d+/\d+页\)</p>",
            "",
            body,
        )
        chapter.body = body.strip()
