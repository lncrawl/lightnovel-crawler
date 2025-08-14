"""HTTP scraping helpers with retry, proxying, and HTML/JSON utilities.

`Scraper` mixes `TaskManager` and `SoupMaker` to provide high-level
request helpers, retries on common transient failures, and utilities to
download files, images, forms, and parse into BeautifulSoup.
"""

import base64
import logging
import os
import random
import re
import ssl
from io import BytesIO
from typing import Any, Callable, Dict, MutableMapping, Optional, Tuple, Union
from urllib.parse import ParseResult, urlparse

from bs4 import BeautifulSoup
from cloudscraper import CloudScraper, User_Agent  # type:ignore
from PIL import Image, UnidentifiedImageError
from requests import Response, Session
from requests.exceptions import ProxyError
from requests.structures import CaseInsensitiveDict
from tenacity import (RetryCallState, retry, retry_if_exception_type,
                      stop_after_attempt, wait_random_exponential)

from ..assets.user_agents import user_agents
from ..utils.ssl_no_verify import no_ssl_verification
from .exeptions import RetryErrorGroup
from .proxy import get_a_proxy, remove_faulty_proxies
from .soup import SoupMaker
from .taskman import TaskManager

logger = logging.getLogger(__name__)


class Scraper(TaskManager, SoupMaker):
    # ------------------------------------------------------------------------- #
    # Initializers
    # ------------------------------------------------------------------------- #
    def __init__(
        self,
        origin: str,
        workers: Optional[int] = None,
        parser: Optional[str] = None,
    ) -> None:
        """Initialize base scraper state and helpers."""
        self.home_url = origin
        self.last_soup_url = ""
        self.use_proxy = os.getenv("use_proxy")

        self.init_scraper()
        self.change_user_agent()
        self.init_parser(parser)
        self.init_executor(workers)

    def close(self) -> None:
        if hasattr(self, "scraper"):
            self.scraper.close()
        super().close()

    def init_parser(self, parser: Optional[str] = None):
        self._soup_tool = SoupMaker(parser)
        self.make_tag = self._soup_tool.make_tag  # type:ignore
        self.make_soup = self._soup_tool.make_soup  # type:ignore

    def init_scraper(self, session: Optional[Session] = None):
        """Initialize underlying requests session (prefer CloudScraper)."""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            self.scraper = CloudScraper.create_scraper(
                session,
                # debug=True,
                # delay=10,
                ssl_context=ctx,
                # interpreter="nodejs",
            )
        except Exception:
            logger.exception("Failed to initialize cloudscraper")
            self.scraper = session or Session()

    # ------------------------------------------------------------------------- #
    # Internal methods
    # ------------------------------------------------------------------------- #

    def __get_proxies(self, scheme, timeout: float = 0):
        """Pick a proxy for the scheme if proxying is enabled."""
        if self.use_proxy and scheme:
            return {scheme: get_a_proxy(scheme, timeout)}
        return {}

    def __process_request(
        self,
        method: str,
        url: str,
        *args,
        max_retries: Optional[int] = None,
        headers: Optional[MutableMapping] = {},
        **kwargs,
    ):
        """Low-level request wrapper with headers, proxies, and retry logic."""
        method_call: Callable[..., Response] = getattr(self.scraper, method)
        if not callable(method_call):
            raise Exception(f"No request method: {method}")

        _parsed = urlparse(url)

        kwargs = kwargs or dict()
        kwargs.setdefault("allow_redirects", True)
        kwargs["proxies"] = self.__get_proxies(_parsed.scheme)

        headers = CaseInsensitiveDict(headers)
        headers.setdefault("Origin", self.home_url.strip("/"))
        headers.setdefault("Referer", self.last_soup_url or self.home_url)
        headers.setdefault("User-Agent", self.user_agent)

        def _after_retry(retry_state: RetryCallState):
            """Called after a retry-able error to rotate proxy when needed."""
            future = retry_state.outcome
            if future:
                e = future.exception()
                if isinstance(e, RetryErrorGroup):
                    logger.debug(f"{repr(e)} | Retrying...", e)
                    if isinstance(e, ProxyError):
                        for proxy_url in kwargs.get("proxies", {}).values():
                            remove_faulty_proxies(proxy_url)
                        kwargs["proxies"] = self.__get_proxies(_parsed.scheme, 5)

        @retry(
            stop=stop_after_attempt(max_retries or 2),
            wait=wait_random_exponential(multiplier=0.5, max=60),
            retry=retry_if_exception_type(RetryErrorGroup),
            after=_after_retry,
            reraise=True,
        )
        def _do_request():
            with self.domain_gate(_parsed.hostname):
                with no_ssl_verification():
                    response = method_call(
                        url,
                        *args,
                        **kwargs,
                        headers=headers,
                    )
                    response.raise_for_status()
                    response.encoding = "utf8"

            self.cookies.update({x.name: x.value for x in response.cookies})
            return response

        logger.debug(
            f"[{method.upper()}] {url}\n"
            + "\n".join([f"    {k} = {v}" for k, v in kwargs.items()])
        )
        return _do_request()

    # ------------------------------------------------------------------------- #
    # Helpers
    # ------------------------------------------------------------------------- #

    @property
    def origin(self) -> ParseResult:
        """Parsed self.home_url"""
        return urlparse(self.home_url)

    @property
    def headers(self) -> Dict[str, Union[str, bytes]]:
        """Default request headers"""
        return dict(self.scraper.headers)

    def set_header(self, key: str, value: str) -> None:
        """Set default headers for next requests"""
        self.scraper.headers[key] = value

    @property
    def cookies(self) -> Dict[str, Optional[str]]:
        """Current session cookies"""
        return {x.name: x.value for x in self.scraper.cookies}

    def set_cookie(self, name: str, value: str) -> None:
        """Set a session cookie"""
        self.scraper.cookies.set(name, value)

    def absolute_url(self, url: Any, page_url: Optional[str] = None) -> str:
        """Make a URL absolute w.r.t. `home_url` or provided page URL."""
        url = str(url or "").strip().rstrip("/")
        if not url:
            return url
        if url.startswith("data:"):
            return url
        if not page_url:
            page_url = str(self.last_soup_url or self.home_url)
        if url.startswith("//"):
            return self.home_url.split(":")[0] + ":" + url
        if url.startswith("/"):
            return self.home_url.strip("/") + url
        if re.match(r'^https?://.*$', url):
            return url
        if page_url:
            return page_url.strip("/") + "/" + url
        return self.home_url + url

    def change_user_agent(self):
        """Rotate the user agent for the underlying session."""
        self.user_agent = random.choice(user_agents)
        if isinstance(self.scraper, CloudScraper):
            self.scraper.user_agent = User_Agent(
                allow_brotli=self.scraper.allow_brotli,
                browser={"custom": self.user_agent},
            )
        elif isinstance(self.scraper, Session):
            self.set_header("User-Agent", self.user_agent)

    # ------------------------------------------------------------------------- #
    # Downloaders
    # ------------------------------------------------------------------------- #

    def _ping_request(self, url: str, timeout=5, **kwargs):
        return self.__process_request("head", url, **kwargs, max_retries=2, timeout=timeout)

    def get_response(
        self,
        url: str,
        timeout: Optional[Union[float, Tuple[float, float]]] = (7, 301),
        **kwargs,
    ) -> Response:
        """GET and return the raw `Response` with sane defaults and retries."""
        return self.__process_request(
            "get",
            url,
            timeout=timeout,
            **kwargs,
        )

    def post_response(
        self,
        url: str,
        data: Optional[MutableMapping] = {},
        max_retries: Optional[int] = 0,
        **kwargs
    ) -> Response:
        """POST and return the raw `Response`."""
        return self.__process_request(
            "post",
            url,
            data=data,
            max_retries=max_retries,
            **kwargs,
        )

    def submit_form(
        self,
        url: str,
        data: Optional[MutableMapping] = None,
        multipart: bool = False,
        headers: Optional[MutableMapping] = {},
        **kwargs
    ) -> Response:
        """Submit a form-like request and return the response."""
        headers = CaseInsensitiveDict(headers)
        headers.setdefault(
            "Content-Type",
            (
                "multipart/form-data"
                if multipart
                else "application/x-www-form-urlencoded; charset=UTF-8"
            ),
        )
        return self.post_response(url, data=data, headers=headers, **kwargs)

    def download_file(
        self,
        url: str,
        output_file: str,
        **kwargs
    ) -> None:
        """Download content directly to a file path."""
        response = self.__process_request("get", url, **kwargs)
        with open(output_file, "wb") as f:
            f.write(response.content)

    def download_image(
        self,
        url: str,
        headers: Optional[MutableMapping] = {},
        **kwargs
    ):
        """Download image and return a PIL Image object.

        Retries with broader Accept header when PIL cannot identify the image.
        """
        if url.startswith("data:"):
            content = base64.b64decode(url.split("base64,")[-1])
            return Image.open(BytesIO(content))

        headers = CaseInsensitiveDict(headers)
        headers.setdefault("Origin", None)
        headers.setdefault("Referer", None)
        timeout = kwargs.pop('timeout', None) or (3, 30)

        try:
            response = self.__process_request(
                "get",
                url,
                headers=headers,
                timeout=timeout,
                max_retries=1,
                **kwargs,
            )
            content = response.content
            return Image.open(BytesIO(content))
        except UnidentifiedImageError:
            headers.setdefault(
                "Accept",
                "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.9",
            )
            response = self.__process_request("get", url, headers=headers, **kwargs)
            content = response.content
            return Image.open(BytesIO(content))

    def get_json(
        self,
        url: str,
        headers: Optional[MutableMapping] = {},
        **kwargs
    ) -> Any:
        """GET and parse JSON content."""
        headers = CaseInsensitiveDict(headers)
        headers.setdefault(
            "Accept",
            "application/json,text/plain,*/*",
        )
        response = self.get_response(url, headers=headers, **kwargs)
        return response.json()

    def post_json(
        self,
        url: str,
        data: Optional[MutableMapping] = {},
        headers: Optional[MutableMapping] = {},
        **kwargs,
    ) -> Any:
        """POST and parse JSON content."""
        headers = CaseInsensitiveDict(headers)
        headers.setdefault("Content-Type", "application/json")
        headers.setdefault(
            "Accept",
            "application/json,text/plain,*/*",
        )
        response = self.post_response(url, data=data, headers=headers, **kwargs)
        return response.json()

    def submit_form_json(
        self,
        url: str,
        data: Optional[MutableMapping] = {},
        headers: Optional[MutableMapping] = {},
        multipart: Optional[bool] = False,
        **kwargs
    ) -> Any:
        """Submit a form and parse a JSON response."""
        headers = CaseInsensitiveDict(headers)
        headers.setdefault(
            "Accept",
            "application/json,text/plain,*/*",
        )
        response = self.submit_form(
            url,
            data=data,
            headers=headers,
            multipart=bool(multipart),
            **kwargs
        )
        return response.json()

    def get_soup(
        self,
        url: str,
        headers: Optional[MutableMapping] = {},
        encoding: Optional[str] = None,
        **kwargs,
    ) -> BeautifulSoup:
        """GET and parse an HTML page into BeautifulSoup, tracking last URL."""
        headers = CaseInsensitiveDict(headers)
        headers.setdefault(
            "Accept",
            "text/html,application/xhtml+xml,application/xml;q=0.9",
        )
        response = self.get_response(
            url,
            headers=headers,
            **kwargs,
        )
        self.last_soup_url = url
        return self.make_soup(response, encoding)

    def post_soup(
        self,
        url: str,
        data: Optional[MutableMapping] = {},
        headers: Optional[MutableMapping] = {},
        encoding: Optional[str] = None,
        **kwargs
    ) -> BeautifulSoup:
        """POST and parse the response HTML into BeautifulSoup."""
        headers = CaseInsensitiveDict(headers)
        headers.setdefault(
            "Accept",
            "text/html,application/xhtml+xml,application/xml;q=0.9",
        )
        response = self.post_response(
            url,
            data=data,
            headers=headers,
            **kwargs,
        )
        return self.make_soup(response, encoding)

    def submit_form_for_soup(
        self,
        url: str,
        data: Optional[MutableMapping] = {},
        headers: Optional[MutableMapping] = {},
        multipart: Optional[bool] = False,
        encoding: Optional[str] = None,
        **kwargs
    ) -> BeautifulSoup:
        """Submit a form and parse the response HTML into BeautifulSoup."""
        headers = CaseInsensitiveDict(headers)
        headers.setdefault(
            "Accept",
            "text/html,application/xhtml+xml,application/xml;q=0.9",
        )
        response = self.submit_form(
            url,
            data=data,
            headers=headers,
            multipart=bool(multipart),
            **kwargs,
        )
        return self.make_soup(response, encoding)
