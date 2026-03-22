import logging

from lncrawl.core import PageSoup
from lncrawl.exceptions import LNException
from lncrawl.templates.mangastream import MangaStreamTemplate

logger = logging.getLogger(__name__)


class Arcanetranslations(MangaStreamTemplate):
    has_mtl = False
    has_manga = False
    base_url = ["https://arcanetranslations.com/"]

    def select_chapter_body(self, soup: PageSoup) -> PageSoup:
        result = super().select_chapter_body(soup)
        if not result:
            raise LNException("No chapter content")
        if "Login to buy access to this content" in result.text:
            raise LNException("This content is behind a paywall. Please login to access it.")
        return result
