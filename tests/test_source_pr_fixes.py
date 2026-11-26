from concurrent.futures import Future
from unittest.mock import patch

from lncrawl.core import Novel, PageSoup
from sources.en.f.freewebnovel import FreewebnovelCrawler
from sources.en.n.novelfull import NovelFullCrawler
from sources.en.n.novelphoenix import NovelPhoenixCrawler


def test_novelphoenix_collects_every_chapter_page_in_order():
    crawler = NovelPhoenixCrawler()
    novel = Novel(url="https://novelphoenix.com/novel/book")
    first = PageSoup.create(
        '<select aria-label="Chapter range"><option>1</option><option>2</option></select><ul class="chapter-list"><li><a href="/1">Chapter 1</a></li></ul>'
    )
    second = PageSoup.create('<ul class="chapter-list"><li><a href="/2">Chapter 2</a></li></ul>')
    try:
        with patch.object(crawler.scraper, "get_soup", side_effect=[first, second]):
            links = list(crawler.select_chapter_tags(first, novel))
        assert [link.get("href") for link in links] == ["/1", "/2"]
    finally:
        crawler.close()


def test_novelfull_fetches_all_pages_and_validates_total():
    crawler = NovelFullCrawler()
    novel = Novel(url="https://novelfull.net/book.html")
    page = PageSoup.create(
        '<div id="list-chapter" data-novel-id="1" data-list-url="/ajax" data-total-page="2" data-total-chapters="2"></div>'
    )
    responses = [
        {
            "page": 1,
            "totalPage": 2,
            "totalChapters": 2,
            "html": '<li><a class="con" href="/1">Chapter 1</a></li>',
        },
        {
            "page": 2,
            "totalPage": 2,
            "totalChapters": 2,
            "html": '<li><a class="con" href="/2">Chapter 2</a></li>',
        },
    ]
    try:
        with patch.object(crawler.scraper, "get_json", side_effect=responses):
            links = list(crawler.select_chapter_tags(page, novel))
        assert [link.get("href") for link in links] == ["/1", "/2"]
    finally:
        crawler.close()


def test_freewebnovel_collects_results_in_page_order():
    crawler = FreewebnovelCrawler()
    novel = Novel(url="https://freewebnovel.com/book")
    page = PageSoup.create(
        "<script>window.chapterPagination = {totalPage: 2, pageSize: 1}</script>"
    )

    class Response:
        def __init__(self, number):
            self.number = number

        def json(self):
            return {"html": f'<a href="/{self.number}">Chapter {self.number}</a>'}

    futures = []
    for number in (1, 2):
        future = Future()
        future.set_result(Response(number))
        futures.append(future)
    try:
        with patch.object(crawler.taskman, "submit_task", side_effect=futures):
            links = list(crawler.select_chapter_tags(page, novel))
        assert [link.get("href") for link in links] == ["/1", "/2"]
    finally:
        crawler.close()
