from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

from lncrawl.core import SearchResult
from lncrawl.services.crawler import CrawlerService, _matches_search_title


def test_source_search_returns_only_matching_novels():
    @contextmanager
    def prepare(*args, **kwargs):
        yield SimpleNamespace(
            search=lambda query: [
                SearchResult(title="Overgeared", url="https://example.com/overgeared"),
                SearchResult(
                    title="Всеозброєний",
                    url="https://zenko.online/titles/3662",
                    eng_title="Overgeared",
                ),
                SearchResult(title="Book of The Dead", url="https://example.com/dead"),
            ]
        )

    service = CrawlerService()
    with (
        patch("lncrawl.services.crawler.ctx.sources") as sources,
        patch.object(service, "prepare_crawler", side_effect=prepare),
    ):
        sources.get_source.return_value.url = "https://example.com/"
        results = service.search_novel("user", "overgeared", "example.com")

    assert {result.title for result in results} == {"Overgeared", "Всеозброєний"}


def test_search_requires_all_query_terms_in_title():
    assert _matches_search_title("Overgeared", "overgeared")
    assert not _matches_search_title("Book of The Dead", "overgeared")
    assert not _matches_search_title("A completely unrelated novel", "overgeared")


def test_search_matches_multiword_unicode_titles_case_insensitively():
    assert _matches_search_title("Тень и Кость", "тень кость")
    assert _matches_search_title("The Legendary Moonlight Sculptor", "moonlight sculptor")
    assert not _matches_search_title("The Legendary Moonlight Sculptor", "moonlight geard")
