# -*- coding: utf-8 -*-
"""
# TODO: Read the TODOs carefully and remove all existing comments in this file.

This is a sample using the BasicBrowserTemplate as a template. This template
provides a basic wrapper around the base Crawler. In case a scraper based request
fails with `ScraperNotSupported`, it retries with the webdriver based scraping.

Put your source file inside the language folder. The `en` folder has too many
files, therefore it is grouped using the first letter of the domain name.
"""
import logging
from typing import Generator

from lncrawl.models.chapter import Chapter
from lncrawl.models.search_result import SearchResult
from lncrawl.templates.browser.basic import BasicBrowserTemplate

logger = logging.getLogger(__name__)


# TODO: You can safely delete all [OPTIONAL] methods if you do not need them.
class MyCrawlerName(BasicBrowserTemplate):
    # TODO: [REQUIRED] Provide the URLs supported by this crawler.
    base_url = ["http://sample.url/"]

    # TODO: [OPTIONAL] Set True if this crawler is for manga/manhua/manhwa.
    has_manga = False

    # TODO: [OPTIONAL] Set True if this source contains machine translations.
    has_mtl = False

    # TODO: [OPTIONAL] This is called before all other methods.
    def initialize(self) -> None:
        # You can customize `TextCleaner` and other necessary things.
        pass

    # TODO: [OPTIONAL] This is called once per session before searching and fetching novel info.
    def login(self, username_or_email: str, password_or_token: str) -> None:
        pass

    # TODO: [OPTIONAL] Search for novels with `self.scraper` requests
    def search_novel_in_soup(self, query: str) -> Generator[SearchResult, None, None]:
        # `raise ScraperNotSupported()` to use the browser only.
        raise NotImplementedError()

    # TODO: [OPTIONAL] Search for novels with `self.browser`
    def search_novel_in_browser(self, query: str) -> Generator[SearchResult, None, None]:
        raise NotImplementedError()

    # TODO: [OPTIONAL] Read novel info with `self.scraper` requests
    def read_novel_info_in_soup(self) -> None:
        # The current input url is available at `self.novel_url`.
        # You can use `self.get_soup`, `self.get_json` etc. utilities to fetch contents.
        #
        # You must set the following parameters:
        #       `self.novel_title`: the title of the novel
        #       `self.chapters`: the list of all chapters
        #
        # The following paramters are optional but good to have:
        #       `self.novel_author`: a comma separated list of names
        #       `self.novel_cover`: the novel cover image url
        #       `self.volumes`: the list of all volumes
        #
        # You may throw an Exception in case of failure.
        # `raise ScraperNotSupported()` to use the browser only.
        pass

    # TODO: [REQUIRED] Read novel info with `self.browser`
    def read_novel_info_in_browser(self) -> None:
        # This gets called only when the `read_novel_info_in_soup` fails.
        # The current input url is available at `self.novel_url`.
        # You can use `self.visit`, `self.browser.wait` etc. utilities.
        # Get a PageSoup instance from browser: `self.browser.soup`
        #
        # You must set the following parameters:
        #       `self.novel_title`: the title of the novel
        #       `self.chapters`: the list of all chapters
        #
        # The following paramters are optional but good to have:
        #       `self.novel_author`: a comma separated list of names
        #       `self.novel_cover`: the novel cover image url
        #       `self.volumes`: the list of all volumes
        #
        # You may throw an Exception in case of failure.
        pass

    # TODO: [OPTIONAL] Download the chapter contents using the self.scraper requests
    def download_chapter_body_in_soup(self, chapter: Chapter) -> str:
        # Use the `chapter['url']` to get the chapter contents.
        # You can use `self.get_soup`, `self.get_json` etc. utilities to fetch contents.
        # To clean chapter HTML easily, use `self.cleaner.extract_contents`.
        #
        # `raise ScraperNotSupported()` to use the browser only.
        raise NotImplementedError()

    # TODO: [REQUIRED] Download the chapter contents using the `self.browser`
    def download_chapter_body_in_browser(self, chapter: Chapter) -> str:
        # Use the `chapter['url']` to get the chapter contents.
        # You can use `self.visit` to visit the chapter in browser tab.
        # There can be only one thread using the browser at a time.
        # Get a PageSoup instance from browser: `self.browser.soup`
        # To clean chapter HTML easily, use `self.cleaner.extract_contents`.
        raise NotImplementedError()
