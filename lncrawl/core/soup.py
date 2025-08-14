"""BeautifulSoup factory and helpers used by the scraper/crawler."""

import logging
from abc import ABC
from typing import Optional, Union

from bs4 import BeautifulSoup, Tag
from requests import Response

from .exeptions import LNException

logger = logging.getLogger(__name__)


DEFAULT_PARSER = "lxml"


class SoupMaker(ABC):
    def __init__(
        self,
        parser: Optional[str] = None,
    ) -> None:
        """Configure parser preference (defaults to lxml)."""
        self._parser = parser or DEFAULT_PARSER

    def close(self) -> None:
        pass

    def make_soup(
        self,
        data: Union[Response, bytes, str],
        encoding: Optional[str] = None,
    ) -> BeautifulSoup:
        """Parse bytes/str/Response into a BeautifulSoup instance."""
        if isinstance(data, Response):
            return self.make_soup(data.content, encoding)
        elif isinstance(data, bytes):
            html = data.decode(encoding or "utf8", "ignore")
        elif isinstance(data, str):
            html = data
        else:
            raise LNException("Could not parse response")
        return BeautifulSoup(html, features=self._parser)

    def make_tag(
        self,
        data: Union[Response, bytes, str],
        encoding: Optional[str] = None,
    ) -> Tag:
        """Create a first child `Tag` from a body for convenience."""
        soup = self.make_soup(data, encoding)
        return next(soup.find("body").children)
