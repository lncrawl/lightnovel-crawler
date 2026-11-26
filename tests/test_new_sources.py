from unittest.mock import patch

from lncrawl.core import Chapter, Novel, PageSoup
from sources.en.b.botitranslation import BotiTranslationCrawler
from sources.en.l.lightnovel_io import LightNovelIoCrawler
from sources.en.l.lorenovels import LoreNovelsCrawler
from sources.en.n.noveldex import _fnv_key, _xor_decrypt
from sources.en.n.novelping import NovelPingCrawler
from sources.en.w.wetriedtls import WeTriedTlsCrawler
from sources.id.indowebnovel import IndowebnovelCrawler
from sources.zh.xbiquge345 import Xbiquge345Crawler
from sources.zh.xszj import XszjCrawler


def test_lightnovel_io_metadata_and_toc_synthesis():
    crawler = LightNovelIoCrawler()
    novel = Novel(url="https://lightnovel.to/novel/my-novel")
    soup = PageSoup.create(
        '<h1 class="ln-dtitle">My Novel</h1>'
        '<div class="ln-crow"><a href="/novel/my-novel/chapter-1">Chapter 1: The Start</a></div>'
        "<p>with 2 chapters</p>"
    )
    with patch.object(crawler.scraper, "get_soup", return_value=soup):
        crawler.read_novel(novel)
    assert novel.title == "My Novel"
    assert len(novel.chapters) == 2
    assert novel.chapters[0].title == "Chapter 1: The Start"
    assert novel.chapters[1].url == "https://lightnovel.to/novel/my-novel/chapter-2"


def test_novelping_api_integration():
    crawler = NovelPingCrawler()
    novel = Novel(url="https://novelping.com/book/my-novel")
    crawler._novel_info = {
        "novel_name": "Ping Novel",
        "novel_author": "Ping Author",
        "novel_genres": ["Action"],
        "novel_desc": "Ping Desc",
    }
    crawler.parse_title(None, novel)
    crawler.parse_authors(None, novel)
    crawler.parse_tags(None, novel)
    crawler.parse_summary(None, novel)
    assert novel.title == "Ping Novel"
    assert novel.author == "Ping Author"
    assert novel.tags == ["Action"]
    assert novel.synopsis == "Ping Desc"


def test_lorenovels_drops_locked_member_posts():
    crawler = LoreNovelsCrawler()
    novel = Novel(url="https://lorenovels.com/support-novel/")
    soup = PageSoup.create(
        '<div class="entry-content">'
        '<div class="wp-block-group is-vertical">Title: Support Novel</div>'
        '<div class="wp-block-group is-vertical">Author: Lore Author</div>'
        '<div class="wp-block-group is-vertical">Genre: Fantasy, Action</div>'
        "<p>A great story.</p>"
        '<ul class="wp-block-latest-posts__list">'
        '<li><a href="/support-novel/ch-2/">Chapter 2</a></li>'
        '<li><a href="/support-novel/ch-1/">Chapter 1</a></li>'
        "</ul></div>"
    )
    posts_resp = [
        {
            "link": "https://lorenovels.com/support-novel/ch-2/",
            "excerpt": {"rendered": "logged in to view this content"},
        },
        {
            "link": "https://lorenovels.com/support-novel/ch-1/",
            "excerpt": {"rendered": "Free preview"},
        },
    ]
    with (
        patch.object(crawler.scraper, "get_soup", return_value=soup),
        patch.object(crawler, "_wp_json", side_effect=[[{"categories": [42]}], posts_resp]),
    ):
        crawler.read_novel(novel)
    assert novel.title == "Support Novel"
    assert novel.author == "Lore Author"
    assert [ch.title for ch in novel.chapters] == ["Chapter 1"]


def test_wetriedtls_reads_api_metadata_and_chapters():
    crawler = WeTriedTlsCrawler()
    novel = Novel(url="https://wetriedtls.com/series/regressor-tale")
    series_payload = {
        "title": "Regressor Tale",
        "thumbnail": "cover.jpg",
        "author": "Author",
        "description": "Synopsis",
        "tags": [{"name": "Cultivation"}],
        "id": 99,
    }
    chapters_payload = {
        "meta": {"last_page": 1, "total": 2},
        "data": [
            {"chapter_name": "Chapter 1", "chapter_title": "Awakening", "chapter_slug": "ch-1"},
            {"chapter_name": "Chapter 2", "chapter_title": "", "chapter_slug": "ch-2"},
        ],
    }
    with patch.object(crawler, "_api", side_effect=[series_payload, chapters_payload]):
        crawler.read_novel(novel)
    assert novel.title == "Regressor Tale"
    assert novel.tags == ["Cultivation"]
    assert [ch.title for ch in novel.chapters] == ["Chapter 1: Awakening", "Chapter 2"]


def test_botitranslation_skips_paywalled_chapters():
    crawler = BotiTranslationCrawler()
    novel = Novel(url="https://www.botitranslation.com/book/12345")
    book_payload = {
        "title": "Boti Novel",
        "authorPseudonym": "Boti Author",
        "coverImgUrl": "cover.jpg",
        "synopsis": "Boti Synopsis",
        "tag": "Action,Comedy",
    }
    chapters_payload = {
        "totalPages": 1,
        "list": [
            {
                "id": "c1",
                "title": "Chapter 1",
                "status": "published",
                "paywallStatus": "free",
                "tier": 0,
            },
            {
                "id": "c2",
                "title": "Chapter 2",
                "status": "published",
                "paywallStatus": "paid",
                "tier": 1,
            },
        ],
    }
    with patch.object(crawler, "_api", side_effect=[book_payload, chapters_payload]):
        crawler.read_novel(novel)
    assert novel.title == "Boti Novel"
    assert [ch.title for ch in novel.chapters] == ["Chapter 1"]


def test_xbiquge345_parses_metadata_and_strips_reading_banner():
    crawler = Xbiquge345Crawler()
    page = PageSoup.create(
        '<meta property="og:novel:book_name" content="Biquge Book"/>'
        '<meta property="og:novel:author" content="Chinese Author"/>'
        '<meta property="og:novel:category" content="Xianxia"/>'
        '<meta property="og:description" content="A book desc"/>'
        '<div class="border"><ul class="info"><li><a href="/chapter/1.html">Chapter 1</a></li></ul></div>'
    )
    novel = Novel(url="https://www.xbiquge345.com/book/123")
    crawler.parse_title(page, novel)
    crawler.parse_authors(page, novel)
    crawler.parse_tags(page, novel)
    crawler.parse_summary(page, novel)
    assert novel.title == "Biquge Book"
    assert novel.author == "Chinese Author"
    assert novel.tags == ["Xianxia"]
    assert novel.synopsis == "<p>A book desc</p>"

    chapter = Chapter(id=1, url="https://www.xbiquge345.com/chapter/1.html")
    page = PageSoup.create(
        '<div class="txt"><p>一秒记住【笔趣阁小说网】www.xbiquge345.com</p><p>Actual text content.</p></div>'
    )
    chapter_soup = page.select_one(".txt")
    crawler.parse_chapter_body(chapter_soup, chapter)
    assert chapter.body == "<p>Actual text content.</p>"


def test_xszj_chapter_ordering():
    crawler = XszjCrawler()
    page = PageSoup.create(
        '<div id="list">'
        '<a rel="chapter" href="/b/100/c/2">Chapter 2</a>'
        '<a rel="chapter" href="/b/100/c/1">Chapter 1</a>'
        "</div>"
    )
    novel = Novel(url="https://xszj.org/b/100")
    tags = list(crawler.select_chapter_tags(page, novel))
    assert [t.get("href") for t in tags] == ["/b/100/c/1", "/b/100/c/2"]


def test_noveldex_fnv_keystream_and_xor_decryption():
    key = _fnv_key("hint", "123456", "nonce")
    assert len(key) == 32
    secret = b"Hello, NovelDex!"
    encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(secret))
    import base64

    b64 = base64.b64encode(encrypted).decode()
    decrypted = _xor_decrypt(b64, key)
    assert decrypted == "Hello, NovelDex!"


def test_indowebnovel_com_domain_support():
    crawler = IndowebnovelCrawler()
    assert "https://indowebnovel.com/" in crawler.base_url
    assert "https://indowebnovel.id/" in crawler.base_url
