from abc import abstractmethod
from typing import Generator, List

from ...core.soup import PageSoup
from ...models import SearchResult
from .general import GeneralSoupTemplate


class SearchableSoupTemplate(GeneralSoupTemplate):
    def search_novel(self, query) -> List[SearchResult]:
        tags = self.select_search_items(query)
        return list(self.process_search_results(tags))

    def process_search_results(
        self, tags: Generator[PageSoup, None, None]
    ) -> Generator[SearchResult, None, None]:
        """Process novel item tag and generates search results"""
        count = 0
        for tag in tags:
            count += 1
            if count == 10:
                break
            yield self.parse_search_item(tag)

    @abstractmethod
    def select_search_items(self, query: str) -> Generator[PageSoup, None, None]:
        """Select novel items found on the search page by the query"""
        raise NotImplementedError()

    @abstractmethod
    def parse_search_item(self, tag: PageSoup) -> SearchResult:
        """Parse a tag and return single search result"""
        raise NotImplementedError()
