from unittest.mock import patch

from lncrawl.core import Chapter, Novel, PageSoup
from sources.en.c.chrysanthemumgarden import ChrysanthemumGarden
from sources.en.f.fenrirealm import FenriRealm
from sources.en.n.novelarrow import NovelArrowCrawler
from sources.en.n.novelfire import NovelFireCrawler
from sources.en.n.novelhall import NovelHallCrawler
from sources.multi.wattpad import WattpadCrawler
from sources.multi.wtrlab import WtrLab


def test_chrysanthemum_extracts_clean_chapter_titles():
    crawler = ChrysanthemumGarden()
    soup = PageSoup.create(
        '<h1 class="novel-title"><span class="junk">x</span>Title</h1>'
        '<div id="translated-chapters">'
        '<a class="chapter-item" href="/ch-1">'
        '<span class="chapter-item-number">Chapter 1</span>'
        '<span class="chapter-item-name">The Start</span></a></div>'
    )
    with patch.object(crawler, "get_soup", return_value=soup):
        crawler.read_novel_info()
    assert [ch.title for ch in crawler.chapters] == ["Chapter 1 The Start"]


def test_wattpad_extracts_synopsis():
    crawler = WattpadCrawler()
    with (
        patch.object(crawler, "get_response") as get_response,
        patch("re.compile") as compile_pattern,
    ):
        compile_pattern.return_value.search.return_value.group.return_value = "123"
        get_response.return_value.json.return_value = {
            "title": "Title",
            "cover": "cover.jpg",
            "user": {"name": "Author"},
            "description": "Story summary",
            "parts": [],
        }
        crawler.read_novel_info()
    assert crawler.novel_synopsis == "Story summary"


def test_fenrirealm_filters_locked_chapters_and_strips_hidden_elements():
    crawler = FenriRealm()
    novel_script = 'seriesData:{title:"Title",cover:"storage/cover.jpg",description:"Desc",tags:[{name:"Fantasy"}]}'
    with (
        patch.object(
            crawler, "get_soup", return_value=PageSoup.create(f"<script>{novel_script}</script>")
        ),
        patch.object(
            crawler,
            "get_response",
            return_value=type(
                "R",
                (),
                {
                    "text": '[{"number": 1, "id": 10, "url": "/ch1", "title": "Free", "locked": {"price": 0}}, '
                    '{"number": 2, "id": 20, "url": "/ch2", "title": "Paid", "locked": {"price": 10}}]'
                },
            )(),
        ),
    ):
        crawler.read_novel_info()
    assert [ch.title.strip() for ch in crawler.chapters] == ["- Free"]

    chapter_soup = PageSoup.create(
        '<div id="reader-area-1"><style>.bad{}</style><p>Real text</p><span aria-hidden="true">watermark</span></div>'
    )
    with patch.object(crawler, "get_soup", return_value=chapter_soup):
        body = crawler.download_chapter_body(Chapter(id=1, url="https://fenrirealm.com/ch1"))
    assert "Real text" in body
    assert "watermark" not in body


def test_wtrlab_uses_raw_id_and_post_for_chapter_download():
    crawler = WtrLab()
    chapter = Chapter(id=1, url="https://wtr-lab.com/ch1", order=1, chapter_id="cid", raw_id=123)
    with (
        patch.object(
            crawler,
            "post_json",
            return_value={"success": True, "data": {"data": {"body": "enc"}}},
        ) as post_json,
        patch.object(crawler, "decrypt_body", return_value=["Line 1"]),
    ):
        body = crawler.download_chapter_body(chapter)
    assert post_json.call_args[0][0].endswith("api/reader/get")
    assert post_json.call_args[1]["json"]["raw_id"] == 123
    assert "<p>Line 1</p>" in body


def test_novelfire_reads_synopsis_tags_and_fallback_content():
    crawler = NovelFireCrawler()
    crawler.novel_url = "https://novelfire.net/book/test"
    page = PageSoup.create(
        '<h1>Title</h1><span itemprop="author">Author</span><div class="cover"><img src="/c.jpg"/></div>'
        '<div class="summary"><div class="content"><p>Line 1</p><p>Line 2</p></div></div>'
        '<div class="categories"><a class="property-item">Action</a></div>'
    )
    with (
        patch.object(crawler, "get_soup", side_effect=[page, PageSoup.create("<ul></ul>")]),
        patch("time.sleep"),
    ):
        crawler.read_novel_info()
    assert crawler.novel_synopsis == "Line 1\nLine 2"
    assert crawler.novel_tags == ["Action"]

    chapter_page = PageSoup.create('<div class="chapter-content"><p>Story text</p></div>')
    with patch.object(crawler, "get_soup", return_value=chapter_page):
        body = crawler.download_chapter_body(Chapter(id=1, url="https://novelfire.net/ch1"))
    assert "Story text" in body


def test_novelhall_broadens_catalog_selector():
    crawler = NovelHallCrawler()
    page = PageSoup.create(
        '<div class="book-info"><h1>Title</h1><div class="booktag"><span class="blue">Author：Auth</span><a class="red">Tag</a></div></div>'
        '<div class="book-img"><img src="/img.jpg"/></div>'
        '<div class="book-catalog"><ul><li><a href="/ch1">Chapter 1</a></li></ul></div>'
    )
    with patch.object(crawler, "get_soup", return_value=page):
        crawler.read_novel_info()
    assert [ch.title for ch in crawler.chapters] == ["Chapter 1"]


def test_novelarrow_metadata_uses_api_novel_info():
    crawler = NovelArrowCrawler()
    novel = Novel(url="https://novelarrow.com/novel/test-book")
    crawler._novel_info = {
        "novel_name": "API Title",
        "novel_author": "API Author",
        "novel_genres": ["Action", "Fantasy"],
        "novel_desc": "API Summary",
    }
    crawler.parse_title(None, novel)
    crawler.parse_authors(None, novel)
    crawler.parse_tags(None, novel)
    crawler.parse_summary(None, novel)
    assert novel.title == "API Title"
    assert novel.author == "API Author"
    assert novel.tags == ["Action", "Fantasy"]
    assert novel.synopsis == "API Summary"
