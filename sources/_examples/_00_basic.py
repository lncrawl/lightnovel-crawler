# -*- coding: utf-8 -*-
"""
# TODO: Read the TODOs carefully and remove all existing comments in this file.

This is a sample of directly using the base Crawler as the template.

Put your source file inside the language folder. The `en` folder has too many
files, therefore it is grouped using the first letter of the domain name.
"""

import logging
from typing import List

from lncrawl.core import Crawler
from lncrawl.models import Chapter, SearchResult

logger = logging.getLogger(__name__)


# TODO: You can safely delete all [OPTIONAL] methods if you do not need them.
class MyCrawlerName(Crawler):
    # TODO: [REQUIRED] Provide the URLs supported by this crawler.
    base_url = ["http://sample.url/"]

    # TODO: [OPTIONAL] Set True if this crawler is for manga/manhua/manhwa.
    has_manga = False

    # TODO: [OPTIONAL] Set True if this source contains machine translations.
    has_mtl = False

    # TODO: [OPTIONAL] This is called before all other methods.
    def initialize(self) -> None:
        # You can customize `TextCleaner` and other necessary things.
        super().initialize()

    # TODO: [OPTIONAL] This is called once per session before searching and fetching novel info.
    def login(self, username_or_email: str, password_or_token: str) -> None:
        # Examples:
        # - https://github.com/lncrawl/lightnovel-crawler/blob/master/sources/multi/mtlnovel.py
        # - https://github.com/lncrawl/lightnovel-crawler/blob/master/sources/multi/ranobes.py
        pass

    # TODO: [OPTIONAL] Return a list of search results using the query.
    def search_novel(self, query: str) -> List[SearchResult]:
        # You may raise an Exception or return empty list in case of failure.
        raise NotImplementedError()

    # TODO: [REQUIRED] Reads the TOC contents from the self.novel_url
    def read_novel_info(self) -> None:
        # The current input url is available at `self.novel_url`.
        # You can use self.get_soup, self.get_json etc. utilities to fetch contents.
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

    # TODO: [REQUIRED] Download the content of a single chapter and return it in a clean html format.
    def download_chapter_body(self, chapter: Chapter) -> str:
        # You can use `chapter['url']` to get the contents.
        # To keep it simple, check `self.cleaner.extract_contents`.
        raise NotImplementedError()
