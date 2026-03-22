import base64
import json
import logging
import os
import re
from functools import cached_property
from io import BytesIO
from typing import Any, Dict, MutableMapping, Optional, Tuple, Union
from urllib.parse import ParseResult, urlparse

from cloudscraper import create_scraper
from PIL import Image, UnidentifiedImageError
from requests import Response
from requests.exceptions import ProxyError
from requests.structures import CaseInsensitiveDict

from ..context import ctx
from .proxy import get_a_proxy, remove_faulty_proxy
from .soup import PageSoup
from .taskman import TaskManager

logger = logging.getLogger(__name__)


class Scraper(TaskManager):
    # ------------------------------------------------------------------------- #
    # Initializers
    # ------------------------------------------------------------------------- #
    def __init__(
        self,
        workers: Optional[int] = None,
        parser: Optional[str] = None,
    ) -> None:
        """
        Initializes a new instance of the Scraper class.

        This constructor sets up the Scraper, which is typically used as a base class for the
        Crawler. It configures the origin URL, the number of concurrent workers, and the parser
        to use for processing markup.

        Parameters:
            - origin (str): The base URL from which the scraper will operate.
            - workers (Optional[int], default=None): The number of concurrent worker threads or
                processes. If not specified, a default value (typically 10) is used.
            - parser (Optional[str], default=None): The desired parser or markup type.
                - Acceptable values include parser names ("lxml", "lxml-xml", "html.parser", "html5lib")
                - or, markup types ("html", "html5", "xml").

        Side Effects:
            - Sets up internal state, including proxy usage, user agent, parser, and executor
              for concurrent tasks.
        """
        super().__init__(workers)

        self.home_url = ""
        self.last_soup_url = ""
        self.parser = parser or "lxml"
        self.use_proxy = os.getenv("use_proxy")

    def close(self) -> None:
        super().close()
        self.scraper.close()

    @cached_property
    def scraper(self):
        """Check for option: https://github.com/VeNoMouS/cloudscraper"""
        # OPTIMAL CONFIGURATION for preventing your specific 403 issues
        scraper = create_scraper(
            debug=ctx.logger.is_debug,  # Enable for monitoring (disable in production)
            # KEY SETTINGS to prevent 403 errors
            min_request_interval=2.0,  # CRITICAL: Prevents TLS blocking
            max_concurrent_requests=1,  # CRITICAL: Prevents concurrent conflicts
            rotate_tls_ciphers=True,  # CRITICAL: Avoids cipher detection
            # Enhanced protection
            auto_refresh_on_403=False,  # Auto-recover from 403 errors
            max_403_retries=2,  # Max retry attempts
            session_refresh_interval=900,  # Session refresh time in seconds
            # Optimized stealth mode
            enable_stealth=True,
            stealth_options={
                "min_delay": 1.0,  # Reasonable delays
                "max_delay": 3.0,
                "human_like_delays": True,
                "randomize_headers": True,
                "browser_quirks": True,
            },
            # User agent filtering
            browser={
                "browser": "firefox",
                "platform": "windows",
                "desktop": True,
                "mobile": False,
            },
        )

        # Override close method to clear cached property
        original_close = scraper.close

        def _close():
            original_close()
            self.__dict__.pop("scraper", None)

        scraper.close = _close

        return scraper

    # ------------------------------------------------------------------------- #
    # Internal methods
    # ------------------------------------------------------------------------- #

    def __process_request(
        self,
        method: str,
        url: str,
        *args,
        **kwargs,
    ):
        _parsed = urlparse(url)

        kwargs.setdefault("allow_redirects", True)

        headers = CaseInsensitiveDict(kwargs.pop("headers", {}) or {})
        headers.setdefault("Origin", self.home_url.strip("/"))
        headers.setdefault("Referer", self.last_soup_url or self.home_url)
        kwargs["headers"] = headers

        if self.use_proxy and _parsed.scheme:
            proxies = kwargs.setdefault("proxies", {})
            proxies[_parsed.scheme] = get_a_proxy(_parsed.scheme)

        try:
            response = self.scraper.request(
                method,
                url,
                *args,
                **kwargs,
            )
            response.raise_for_status()

            self.cookies.update({x.name: x.value for x in response.cookies})

            response.encoding = "utf8"
            return response
        except ProxyError:
            if self.use_proxy and _parsed.scheme:
                remove_faulty_proxy(kwargs["proxies"][_parsed.scheme])
            raise

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
        if re.match(r"^https?://.*$", url):
            return url
        if page_url:
            return page_url.strip("/") + "/" + url
        return self.home_url + url

    # ------------------------------------------------------------------------- #
    # Downloaders
    # ------------------------------------------------------------------------- #

    def _ping_request(self, url: str, timeout=5, **kwargs):
        return self.__process_request("head", url, **kwargs, timeout=timeout)

    def get_response(
        self,
        url: str,
        timeout: Optional[Union[float, Tuple[float, float]]] = (7, 301),
        **kwargs,
    ) -> Response:
        """
        Fetches the content from the specified URL using a GET request and returns the response.

        Parameters:
            - url (str): The full URL to send the GET request to.
            - timeout (Optional[float | Tuple[float, float]]): Timeout setting for the request.
                - If a single float is provided, it is used for both the connect and read timeouts.
                - If a tuple of two floats is provided, the first is used for the connect timeout and the second
                  for the read timeout.
                - Defaults to (7, 301).
            - **kwargs: Additional keyword arguments to pass to the request.

        Returns:
            - Response: The response object resulting from the GET request.
        """
        return self.__process_request(
            "get",
            url,
            timeout=timeout,
            **kwargs,
        )

    def post_response(self, url: str, data: Optional[Union[MutableMapping, str, bytes]] = {}, **kwargs) -> Response:
        """Make a POST request and return the response"""
        return self.__process_request(
            "post",
            url,
            data=data,
            **kwargs,
        )

    def submit_form(
        self,
        url: str,
        data: Optional[Union[MutableMapping, str, bytes]] = None,
        multipart: bool = False,
        headers: Optional[MutableMapping] = {},
        **kwargs,
    ) -> Response:
        """Simulate submit form request and return the response"""
        headers = CaseInsensitiveDict(headers)
        headers.setdefault(
            "Content-Type",
            ("multipart/form-data" if multipart else "application/x-www-form-urlencoded; charset=UTF-8"),
        )
        return self.post_response(url, data=data, headers=headers, **kwargs)

    def download_file(self, url: str, output_file: str, **kwargs) -> None:
        """Download content of the url to a file"""
        response = self.__process_request("get", url, **kwargs)
        with open(output_file, "wb") as f:
            f.write(response.content)

    def download_image(self, url: str, headers: Optional[MutableMapping] = {}, **kwargs):
        """Download image from url"""
        if url.startswith("data:"):
            content = base64.b64decode(url.split("base64,")[-1])
            return Image.open(BytesIO(content))

        headers = CaseInsensitiveDict(headers)
        headers.setdefault("Origin", None)
        headers.setdefault("Referer", None)
        timeout = kwargs.pop("timeout", None) or (3, 30)

        try:
            response = self.__process_request(
                "get",
                url,
                headers=headers,
                timeout=timeout,
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

    def get_json(self, url: str, headers: Optional[MutableMapping] = {}, **kwargs) -> Any:
        """Fetch the content and return the content as JSON object"""
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
        data: Optional[Union[MutableMapping, str, bytes]] = {},
        headers: Optional[MutableMapping] = {},
        **kwargs,
    ) -> Any:
        """Make a POST request and return the content as JSON object"""
        headers = CaseInsensitiveDict(headers)
        headers.setdefault("Content-Type", "application/json")
        headers.setdefault(
            "Accept",
            "application/json,text/plain,*/*",
        )
        if isinstance(data, dict):
            data = json.dumps(data)
        response = self.post_response(
            url,
            data=data,
            headers=headers,
            **kwargs,
        )
        return response.json()

    def submit_form_json(
        self,
        url: str,
        data: Optional[Union[MutableMapping, str, bytes]] = None,
        headers: Optional[MutableMapping] = {},
        multipart: Optional[bool] = False,
        **kwargs,
    ) -> Any:
        """Simulate submit form request and return the content as JSON object"""
        headers = CaseInsensitiveDict(headers)
        headers.setdefault(
            "Accept",
            "application/json,text/plain,*/*",
        )
        if isinstance(data, dict):
            data = json.dumps(data)
        response = self.submit_form(url, data=data, headers=headers, multipart=bool(multipart), **kwargs)
        return response.json()

    def make_soup(
        self,
        data: Union[Response, bytes, str, Any],
        encoding: Optional[str] = None,
    ) -> PageSoup:
        return PageSoup.create(data, encoding, self.parser)

    def get_soup(
        self,
        url: str,
        headers: Optional[MutableMapping] = {},
        encoding: Optional[str] = None,
        **kwargs,
    ) -> PageSoup:
        """Fetch the content and return a PageSoup instance of the page"""
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
        data: Optional[Union[MutableMapping, str, bytes]] = None,
        headers: Optional[MutableMapping] = {},
        encoding: Optional[str] = None,
        **kwargs,
    ) -> PageSoup:
        """Make a POST request and return PageSoup instance of the response"""
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
        data: Optional[Union[MutableMapping, str, bytes]] = None,
        headers: Optional[MutableMapping] = {},
        multipart: Optional[bool] = False,
        encoding: Optional[str] = None,
        **kwargs,
    ) -> PageSoup:
        """Simulate submit form request and return a PageSoup instance of the response"""
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
