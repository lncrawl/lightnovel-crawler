# https://cloudbytes.dev/snippets/run-selenium-and-chrome-on-wsl2
# https://github.com/ultrafunkamsterdam/undetected-chromedriver

import logging
from typing import Optional

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver

from ..context import ctx
from ..core.soup import SoupMaker

logger = logging.getLogger(__name__)


def create_new(
    options: Optional[ChromeOptions] = None,
    timeout: Optional[float] = None,
    user_data_dir: Optional[str] = None,
    soup_maker: Optional[SoupMaker] = None,
    headless: bool = False,
    **kwargs,
) -> WebDriver:
    if ctx.config.crawler.selenium_grid:
        from .remote import create_remote
        return create_remote(
            address=ctx.config.crawler.selenium_grid,
            options=options,
            timeout=timeout,
            soup_maker=soup_maker,
        )
    else:
        from .local import create_local
        return create_local(
            options=options,
            timeout=timeout,
            soup_maker=soup_maker,
            user_data_dir=user_data_dir,
            headless=headless,
        )
