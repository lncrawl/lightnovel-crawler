from unittest.mock import patch

from sources.uk.zenko import ZenkoCrawler


def test_search_preserves_translated_title_and_english_alias():
    crawler = object.__new__(ZenkoCrawler)
    response = {
        "data": [
            {"id": 3662, "name": "Всеозброєний", "engName": "Overgeared", "category": "RANOBE"}
        ],
        "meta": {"hasNextPage": False},
    }
    with patch.object(crawler, "get_json", return_value=response):
        results = crawler.search("Overgeared")
    assert [(r.title, r.eng_title, r.url) for r in results] == [
        ("Всеозброєний", "Overgeared", "https://zenko.online/titles/3662")
    ]


def test_search_fetches_later_pages_and_excludes_comics():
    crawler = object.__new__(ZenkoCrawler)
    responses = [
        {
            "data": [{"id": 1, "name": "Comic", "category": "MANGA"}],
            "meta": {"hasNextPage": True, "offset": 0, "limit": 10},
        },
        {
            "data": [{"id": 2, "name": "Novel", "category": "RANOBE"}],
            "meta": {"hasNextPage": False},
        },
    ]
    with patch.object(crawler, "get_json", side_effect=responses) as fetch:
        results = crawler.search("novel")
    assert [r.title for r in results] == ["Novel"]
    assert [call.args[0] for call in fetch.call_args_list] == [
        "https://api.zenko.online/titles?name=novel&offset=0",
        "https://api.zenko.online/titles?name=novel&offset=10",
    ]
