from unittest.mock import patch

import pytest

from lncrawl.core import Chapter, PageSoup
from sources.en.n.novelbuddy import NovelbuddyCrawler


@pytest.mark.parametrize("origin", NovelbuddyCrawler.base_url)
def test_chapter_excludes_reader_controls_and_preserves_story(origin):
    crawler = NovelbuddyCrawler()
    chapter = Chapter(id=2, url=f"{origin}book/chapter-2")
    page = PageSoup.create(
        "<article><header><button>A+</button></header>"
        '<div class="novel-tts-content"><p>Next, she opened the door.</p>'
        "<p>Previous chapters were only a dream.</p></div>"
        '<div><a href="/book/chapter-1">Previous</a>'
        '<a href="/book/chapter-3">Next</a></div></article>'
    )
    try:
        with patch.object(crawler.scraper, "get_soup", return_value=page):
            crawler.download_chapter(chapter)
        assert "Next, she opened the door." in chapter.body
        assert "Previous chapters were only a dream." in chapter.body
        assert 'href="/book/chapter-1"' not in chapter.body
        assert 'href="/book/chapter-3"' not in chapter.body
        assert "A+" not in chapter.body
    finally:
        crawler.close()
