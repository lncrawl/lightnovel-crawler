import json
import re
from typing import Iterable
from urllib.parse import urlencode, urljoin, urlsplit

from lncrawl.core import Chapter, Novel, PageSoup, SearchResult, SoupTemplate
from lncrawl.exceptions import LNException


class SmakolykyCrawler(SoupTemplate):
    base_url = [
        "https://www.smakolykytl.site/",
        "https://smakolykytl.site/",
        "https://test.smakolykytl.site/",
    ]
    language = "uk"
    can_search = True
    request_rate_limit = 1
    api_url = "https://test.smakolykytl.site/api/plugins/smakolykytl/"

    def search(self, query: str) -> Iterable[SearchResult]:
        params = urlencode({"q": query, "page": 1})
        results = self.scraper.get_json(f"{self.api_url}search?{params}")
        return [
            SearchResult(title=item["name"], url=urljoin(self.base_url[0], item["path"]))
            for item in results
        ]

    def read_novel(self, novel: Novel) -> None:
        path = urlsplit(novel.url).path.strip("/")
        if re.fullmatch(r"titles/\d+", path):
            title_path = path
        elif re.fullmatch(r"title/[^/]+", path):
            soup = self.scraper.get_soup(novel.url)
            match = re.search(r"window\.__PRETTY__\s*=\s*({[^;]+})", str(soup))
            if not match:
                raise LNException(f"Could not resolve Smakolyky title: {novel.url}")
            title_path = json.loads(match.group(1))["path"]
            if not re.fullmatch(r"titles/\d+", title_path):
                raise LNException(f"Invalid Smakolyky title path: {title_path}")
        else:
            raise ValueError(f"Invalid Smakolyky title URL: {novel.url}")

        params = urlencode({"path": title_path})
        data = self.scraper.get_json(f"{self.api_url}novel?{params}")
        novel.title = data["name"]
        novel.author = data.get("author") or ""
        novel.cover_url = data.get("cover") or ""
        novel.synopsis = data.get("summary") or ""
        novel.tags = [tag.strip() for tag in (data.get("genres") or "").split(",") if tag.strip()]
        novel.language = self.language

        volumes = {}
        for item in data.get("chapters", []):
            key = item.get("volumeKey") or item.get("volumeNumber")
            if key not in volumes:
                volumes[key] = novel.add_volume(title=item.get("volumeName") or "").id
            novel.add_chapter(
                url=urljoin(self.base_url[0], item["path"]),
                title=item["name"],
                volume=volumes[key],
            )
        if not novel.chapters:
            raise LNException(f"No chapters found for Smakolyky title: {novel.url}")

    def download_chapter(self, chapter: Chapter) -> None:
        path = urlsplit(chapter.url).path.strip("/")
        if not re.fullmatch(r"read/\d+", path):
            raise ValueError(f"Invalid Smakolyky chapter URL: {chapter.url}")
        params = urlencode({"path": path})
        data = self.scraper.get_json(f"{self.api_url}chapter?{params}")
        content = data.get("content") or ""
        if not content.strip():
            raise LNException(f"Empty Smakolyky chapter: {chapter.url}")
        soup = PageSoup.create(f"<div>{content}</div>")
        chapter.body = self.cleaner.extract_contents(soup.select_one("div"))
