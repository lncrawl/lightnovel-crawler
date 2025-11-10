# -*- coding: utf-8 -*-
"""
# TODO: Read the TODOs carefully and remove all existing comments in this file.

This is a sample using the SearchableSoupTemplate as the template. This template
provides a wrapper around the GeneralSoupTemplate to support search.

Put your source file inside the language folder. The `en` folder has too many
files, therefore it is grouped using the first letter of the domain name.
"""
import logging
import re
from typing import Generator, Union

from bs4 import BeautifulSoup, Tag
import urllib.parse

from lncrawl.core.crawler import Crawler
from lncrawl.models import Chapter, SearchResult, Volume
from lncrawl.templates.soup.searchable import SearchableSoupTemplate
from scripts.index_gen import crawler

logger = logging.getLogger(__name__)
search_url = "https://cheldra.wordpress.com"


class Cheldra(SearchableSoupTemplate):
    # TODO: [REQUIRED] Provide the URLs supported by this crawler.
    base_url = ["https://cheldra.wordpress.com"]

    # TODO: [OPTIONAL] Set True if this crawler is for manga/manhua/manhwa.
    has_manga = False

    # TODO: [OPTIONAL] Set True if this source contains machine translations.
    has_mtl = False

    # TODO: [OPTIONAL] This is called before all other methods.
    def initialize(self) -> None:
        # You can customize `TextCleaner` and other necessary things.
        pass

    # TODO: [REQUIRED] Select novel items found in search page from the query
    def select_search_items(self, query: str) -> Generator[Tag, None, None]:
        soup = self.post_soup(self.home_url)
        results = soup.select(".site-header .site-header-top .main-navigation div ul li")
        filtered_results = [result for result in results if
                            query in str(result.find("a", href=True)) and result.find("a", href=True).text != "About"]
        yield from filtered_results
        pass

    # TODO: [REQUIRED] Parse a tag and return single search result
    def parse_search_item(self, tag: Tag) -> SearchResult:
        url = tag.find("a").get("href")
        soup = self.post_soup(url)
        title = soup.select(".entry-title")[0].text
        return SearchResult(
            title=title,
            url=url
        )

    # TODO: [OPTIONAL] Get a BeautifulSoup instance from the self.novel_url
    def get_novel_soup(self) -> BeautifulSoup:
        return self.get_soup(self.novel_url)

    # TODO: [REQUIRED] Parse and return the novel title
    def parse_title(self, soup: BeautifulSoup) -> str:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        return soup.select(".entry-title")[0].text

    # TODO: [REQUIRED] Parse and return the novel cover
    def parse_cover(self, soup: BeautifulSoup) -> str:
        links = soup.select("div.entry-content p:not([class]) a")
        seven_seas_url = [link.get("href") for link in links if link.text == "Seven Seas"][0]
        seven_seas_soup = self.post_soup(seven_seas_url)
        self.seven_seas_soup = seven_seas_soup
        all_imgs = seven_seas_soup.select("div.volumes-container a img")
        return all_imgs[0].get("src")

    # TODO: [OPTIONAL] Parse and return the novel authors
    def parse_authors(self, soup: BeautifulSoup) -> Generator[str, None, None]:
        author = soup.select("div.entry-content p:not([class])")[0].text.lstrip("Author: ")
        yield author
        pass

    # TODO: [OPTIONAL] Parse and return the novel categories or tags
    def parse_genres(self, soup: BeautifulSoup) -> Generator[str, None, None]:
        soup = self.seven_seas_soup
        meta = soup.select("div.info div#series-meta")[0]
        genre_tags = meta.find("b", string="Genre(s):")
        genres = []
        for tag in genre_tags.find_next_siblings():
            if tag.name == "a":
                genres.append(tag.text)
            else:
                break  # on s’arrête dès qu’on sort de la séquence de <a>
        yield from genres
        pass

    # TODO: [OPTIONAL] Parse and return the novel summary or synopsis
    def parse_summary(self, soup: BeautifulSoup) -> Generator[str, None, None]:
        soup = self.seven_seas_soup
        yield from soup.select("div.series-description div.entry p")[0].text
        pass

    # TODO: [REQUIRED] Parse and set the volumes and chapters
    def parse_chapter_list(self, soup: BeautifulSoup) -> Generator[Union[Chapter, Volume], None, None]:
        # The soup here is the result of `self.get_soup(self.novel_url)`
        chap_list = soup.select("div.entry-content p.has-text-align-justify.has-small-font-size a")
        seen_vol_ids = set()
        # print(chap_list)
        print("sending chapters")
        for i, chap in enumerate(chap_list):
            if i < len(chap_list) and chap_list[i + 1].get("href") == chap.get("href"):
                chap_title = chap_list[i+1].text
            elif chap_list[i - 1].get("href") == chap.get("href"):
                continue
            if "–" in chap.text:
                separated_title = chap.text.split("–")
                chap_title = chap.text.split("–")[1].strip()
            else:
                separated_title = chap.text.split("-")
                chap_title = "-".join(chap.text.split("-")[1:]).strip()
            try:
                chap_id = int(separated_title[0].strip())
                vol_id = 1 + chap_id // 100
            except Exception as e:
                result = re.sub(r"[A-Za-z]", "", separated_title[0].strip())
                chap_id = int(result)
                vol_title = re.sub(r"[1-9]", "", separated_title[0].strip())
                vol_id = 101 + chap_id // 100
            chap_url = chap.get("href")
            if "vol_title" not in locals():
                vol_title = vol_id
            yield Chapter(
                title=chap_title,
                id=chap_id,
                url=chap_url,
                volume=vol_id
            )
            if vol_id in seen_vol_ids:
                yield Volume(
                    id=vol_id,
                    title=vol_title
                )
            del vol_title
        # print(crawler.chapters, crawler.volumes)
        pass

    # TODO: [REQUIRED] Select the tag containing the chapter text
    def select_chapter_body(self, soup: BeautifulSoup) -> Tag:
        # The soup here is the result of `self.get_soup(chapter.url)`
        #
        print(soup)
        # Example: return soup.select_one(".m-read .txt")
        pass

    # TODO: [OPTIONAL] Return the index in self.chapters which contains a chapter URL
    def index_of_chapter(self, url: str) -> int:
        # To get more help, check the default implemention in the `Crawler` class.
        pass

