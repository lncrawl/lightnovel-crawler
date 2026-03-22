import logging

from lncrawl.core.soup import PageSoup

from lncrawl.templates.madara import MadaraTemplate

logger = logging.getLogger(__name__)


class SonicMTLCrawler(MadaraTemplate):
    has_mtl = True
    base_url = [
        "https://sonicmtl.com",
        "https://www.sonicmtl.com/",
    ]

    def initialize(self):
        super().initialize()
        self.cleaner.bad_css.update(
            {
                ".ad",
                ".c-ads",
                ".custom-code",
                ".body-top-ads",
                ".before-content-ad",
                ".autors-widget",
            }
        )

    def select_chapter_body(self, soup: PageSoup) -> PageSoup:
        return soup.select_one(".reading-content .text-left")
