from contextlib import contextmanager
from unittest.mock import patch

from bs4 import BeautifulSoup
from ebooklib import epub
from sqlmodel import Session, SQLModel, create_engine

from lncrawl.core import Novel, PageSoup
from lncrawl.dao import Job, JobStatus, JobType, Novel as StoredNovel
from lncrawl.services.binder.epub import build_intro
from lncrawl.services.jobs.service import JobService
from lncrawl.templates.generic import GenericCrawler
from sources.en.w.webnovel import WebnovelCrawler


def test_generic_crawler_prefers_chapter_list_and_uses_title_numbering():
    crawler = GenericCrawler(origin="https://example.com/")
    soup = PageSoup.create(
        '<h1>Novel</h1><nav class="sidebar">'
        '<a href="/other-1">Other 1</a><a href="/other-2">Other 2</a></nav>'
        '<div class="chapter-list">'
        '<a href="/novel/chapter-one-2024">Chapter 1</a>'
        '<a href="/novel/chapter-two-2024">Chapter 2</a>'
        '<a href="/novel/chapter-three-2024">Chapter 3</a></div>'
    )
    novel = Novel(url="https://example.com/novel")
    try:
        with patch.object(crawler.scraper, "get_soup", return_value=soup):
            crawler.read_novel(novel)
        assert [chapter.title for chapter in novel.chapters] == [
            "Chapter 1",
            "Chapter 2",
            "Chapter 3",
        ]
        assert crawler.verdict.complete
        assert crawler.verdict.ordering == "title-number"
    finally:
        crawler.close()


def test_epub_keeps_synopsis_line_breaks_and_existing_html():
    novel = StoredNovel(
        domain="example.com",
        url="https://example.com/book",
        title="Book",
        synopsis="<p>First <em>line</em></p>\n<p>Second line</p>",
    )
    item = build_intro(novel)
    book = epub.EpubBook()
    book.add_item(item)
    content = item.get_content().decode()
    assert "<em>line</em>" in content
    synopsis = BeautifulSoup(content, "html.parser").select_one(".synopsis")
    assert synopsis.select_one("br") is not None
    assert [p.get_text() for p in synopsis.select("p")] == ["First line", "Second line"]


def test_webnovel_saves_description_and_distinct_tags():
    crawler = WebnovelCrawler()
    crawler.__dict__["csrf"] = "test"
    data = {
        "data": {
            "bookInfo": {
                "bookName": "Book",
                "description": "First & foremost\nSecond line",
                "categoryName": "Fantasy",
                "tagInfos": [
                    {"enTagName": "fantasy"},
                    {"tagName": "Adventure"},
                ],
            }
        }
    }
    novel = Novel(url="https://www.webnovel.com/book/123")
    try:
        with patch.object(crawler.scraper, "get_json", return_value=data):
            with patch.object(
                crawler.scraper, "get_soup", return_value=PageSoup.create("<div></div>")
            ):
                crawler.read_novel(novel)
        assert novel.synopsis == "<p>First &amp; foremost</p><p>Second line</p>"
        assert novel.tags == ["Fantasy", "Adventure"]
    finally:
        crawler.close()


def test_canceled_child_marks_batch_failed():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    parent = Job(user_id="user", type=JobType.NOVEL_BATCH, total=1)
    child = Job(user_id="user", type=JobType.NOVEL, parent_job_id=parent.id, total=1)
    parent_id = parent.id
    child_id = child.id
    with Session(engine) as session:
        session.add(parent)
        session.add(child)
        session.commit()

    @contextmanager
    def session_factory():
        with Session(engine) as session:
            yield session

    service = JobService()
    with patch("lncrawl.services.jobs.service.ctx.db.session", session_factory):
        service.cancel(child_id)
        with Session(engine) as session:
            updated = session.get(Job, parent_id)
            assert updated.status == JobStatus.FAILED
            assert updated.is_done
    engine.dispose()
