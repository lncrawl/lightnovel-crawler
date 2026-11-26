from unittest.mock import patch

import pytest

from lncrawl.core import Chapter, Novel, PageSoup
from lncrawl.exceptions import LNException
from sources.uk.smakolyky import SmakolykyCrawler


@pytest.mark.parametrize(
    "url",
    [
        "https://www.smakolykytl.site/titles/50",
        "https://smakolykytl.site/titles/50",
        "https://test.smakolykytl.site/title/vseozbroyenyy",
    ],
)
def test_novel_urls_preserve_chapter_order_and_volume_groups(url):
    crawler = SmakolykyCrawler()
    novel = Novel(url=url)
    data = {
        "name": "Всеозброєний",
        "author": "Автор",
        "genres": "Фентезі, Пригоди",
        "chapters": [
            {"name": "Пролог", "path": "read/5", "volumeKey": "1", "volumeName": "Том 1"},
            {"name": "Розділ 1", "path": "read/3", "volumeKey": "2", "volumeName": "Том 2"},
        ],
    }
    page = PageSoup.create(
        '<script>window.__PRETTY__={"plugin":"smakolykytl","path":"titles/50"};</script>'
    )
    try:
        with patch.object(crawler.scraper, "get_json", return_value=data):
            with patch.object(crawler.scraper, "get_soup", return_value=page):
                crawler.read_novel(novel)
        assert novel.title == "Всеозброєний"
        assert novel.tags == ["Фентезі", "Пригоди"]
        assert [chapter.title for chapter in novel.chapters] == ["Пролог", "Розділ 1"]
        assert [chapter.volume for chapter in novel.chapters] == [1, 2]
        assert [chapter.url for chapter in novel.chapters] == [
            "https://www.smakolykytl.site/read/5",
            "https://www.smakolykytl.site/read/3",
        ]
    finally:
        crawler.close()


def test_chapter_preserves_story_html_and_rejects_empty_content():
    crawler = SmakolykyCrawler()
    chapter = Chapter(id=1, url="https://www.smakolykytl.site/read/5")
    try:
        with patch.object(
            crawler.scraper, "get_json", return_value={"content": "<p>Текст <em>тут</em>.</p>"}
        ):
            crawler.download_chapter(chapter)
        assert "Текст" in chapter.body
        assert "тут" in chapter.body
        assert "<html>" not in chapter.body
        with patch.object(crawler.scraper, "get_json", return_value={"content": ""}):
            with pytest.raises(LNException):
                crawler.download_chapter(chapter)
    finally:
        crawler.close()


def test_search_returns_novel_urls():
    crawler = SmakolykyCrawler()
    try:
        with patch.object(
            crawler.scraper,
            "get_json",
            return_value=[{"name": "Всеозброєний", "path": "titles/50"}],
        ):
            results = list(crawler.search("Всеозброєний"))
        assert [(result.title, result.url) for result in results] == [
            ("Всеозброєний", "https://www.smakolykytl.site/titles/50")
        ]
    finally:
        crawler.close()
