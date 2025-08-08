import logging

from lncrawl.templates.mangastream import MangaStreamTemplate

logger = logging.getLogger(__name__)


class Dobytranslations(MangaStreamTemplate):
    has_mtl = False
    has_manga = False
    base_url = ["https://dobytranslations.com/"]
