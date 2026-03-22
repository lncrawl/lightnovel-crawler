import time
from concurrent.futures import Future
from typing import List
from urllib.parse import parse_qs, urlencode, urlparse

from lncrawl.core import PageSoup
from lncrawl.exceptions import LNException
from lncrawl.models import Chapter, SearchResult
from lncrawl.templates.browser.chapter_only import ChapterOnlyBrowserTemplate
from lncrawl.templates.browser.searchable import SearchableBrowserTemplate


class NovelMTLTemplate(SearchableBrowserTemplate, ChapterOnlyBrowserTemplate):
    is_template = True

    def initialize(self) -> None:
        self.cur_time = int(1000 * time.time())
        self.init_executor(ratelimit=1.4)

    def select_search_items(self, query: str):
        soup = self.get_soup(f"{self.home_url}search.html")
        form = soup.select_one('.search-container form[method="post"]')
        if not form:
            raise LNException("No search form")

        action_url = self.absolute_url(form["action"])
        payload = {input["name"]: input["value"] for input in form.select("input")}
        payload["keyboard"] = query
        response = self.submit_form(action_url, payload)

        soup = self.make_soup(response)
        yield from soup.select("ul.novel-list .novel-item a")

    def parse_search_item(self, tag: PageSoup) -> SearchResult:
        return SearchResult(
            url=self.absolute_url(tag["href"]),
            title=tag.select_one(".novel-title").text,
            info=" | ".join([x.text.strip() for x in tag.select(".novel-stats")]),
        )

    def parse_title(self, soup: PageSoup) -> str:
        return soup.select_one(".novel-info .novel-title").text

    def parse_cover(self, soup: PageSoup):
        tag = soup.select_one("#novel figure.cover img")
        if not tag:
            return None
        if tag.has_attr("data-src"):
            return self.absolute_url(tag["data-src"])
        elif tag.has_attr("src"):
            return self.absolute_url(tag["src"])

    def parse_authors(self, soup: PageSoup):
        for a in soup.select('.novel-info .author span[itemprop="author"]'):
            yield a.text.strip()

    def parse_genres(self, soup):
        for a in soup.select(".categories a"):
            yield a.text.strip()

    def parse_summary(self, soup: PageSoup) -> str:
        return self.cleaner.extract_contents(soup.select_one(".summary .content"))

    def select_chapter_tags(self, soup: PageSoup):
        tags = list(soup.select("#chapters .pagination li a"))
        if tags:
            last_page = str(tags[-1]["href"])
            last_page_qs = parse_qs(urlparse(last_page).query)
            max_page = int(last_page_qs["page"][0])
            wjm = last_page_qs["wjm"][0]

            futures: List[Future] = []
            for i in range(max_page + 1):
                payload = {
                    "page": i,
                    "wjm": wjm,
                    "_": self.cur_time,
                    "X-Requested-With": "XMLHttpRequest",
                }
                url = f"{self.home_url}e/extend/fy.php?{urlencode(payload)}"
                f = self.executor.submit(self.get_soup, url)
                futures.append(f)

            self.resolve_futures(futures, desc="TOC", unit="page")
            for i, future in enumerate(futures):
                if not future.done():
                    raise LNException(f"Failed to get page {i + 1}")
                soup = future.result()
                yield from soup.select("ul.chapter-list li a")
        else:
            yield from soup.select("ul.chapter-list li a")

    def parse_chapter_item(self, tag: PageSoup, id: int) -> Chapter:
        title = tag.select_one(".chapter-title")
        assert title, "No chapter title"
        return Chapter(
            id=id,
            url=self.absolute_url(tag["href"]),
            title=title.text,
        )

    def select_chapter_body(self, soup: PageSoup) -> PageSoup:
        return soup.select_one(".chapter-content")
