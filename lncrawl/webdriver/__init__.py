# https://cloudbytes.dev/snippets/run-selenium-and-chrome-on-wsl2
# https://github.com/ultrafunkamsterdam/undetected-chromedriver

import logging
import os
from typing import Optional

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver

from ..context import ctx

logger = logging.getLogger(__name__)


def create_new(
    options: Optional[ChromeOptions] = None,
    timeout: Optional[float] = None,
    user_data_dir: Optional[str] = None,
    headless: bool = False,
    **kwargs,
) -> WebDriver:
    """Create a new webdriver instance"""
    if not user_data_dir:
        user_data_dir = str(ctx.config.app.output_path / "webdriver")
        os.makedirs(user_data_dir, exist_ok=True)
    if ctx.config.crawler.selenium_grid:
        from .remote import create_remote
        return create_remote(
            address=ctx.config.crawler.selenium_grid,
            options=options,
            timeout=timeout,
        )
    else:
        from .local import create_local
        return create_local(
            options=options,
            timeout=timeout,
            user_data_dir=user_data_dir,
            headless=headless,
        )
