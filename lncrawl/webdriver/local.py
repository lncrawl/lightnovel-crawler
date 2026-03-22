# https://cloudbytes.dev/snippets/run-selenium-and-chrome-on-wsl2
# https://github.com/ultrafunkamsterdam/undetected-chromedriver

import json
import logging
import os
from typing import Optional

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.remote.webdriver import WebDriver

from ..utils.platforms import Platform, Screen
from .elements import WebElement
from .job_queue import _acquire_queue, _release_queue
from .scripts import _override_get

logger = logging.getLogger(__name__)


def create_local(
    options: Optional[ChromeOptions] = None,
    timeout: Optional[float] = None,
    headless: bool = False,
    user_data_dir: Optional[str] = None,
    **kwargs,
) -> WebDriver:
    """
    Acquire a webdriver instane. There is a limit of how many webdriver
    instances you can keep open at a time. You must call quit() to cleanup
    existing one to obtain new ones.

    NOTE: You must call quit() to cleanup the queue.
    """
    _acquire_queue(timeout)
    is_debug = os.getenv("debug_mode")

    if not options:
        options = ChromeOptions()

    if not headless and not Platform.has_display:
        headless = True

    # Options for chrome driver
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-first-run")
    options.add_argument("--lang=en-US")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Configure window behavior
    if headless:
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--headless=new")
    else:
        width = max(640, Screen.view_width * 3 // 4)
        height = max(480, Screen.view_height * 3 // 4)
        width = int(os.getenv("CHROME_WIDTH", width))
        height = int(os.getenv("CHROME_HEIGHT", height))
        options.add_argument(f"--window-size={width},{height}")

    # Add capabilities
    options.set_capability("acceptInsecureCerts", True)

    # Chrome specific experimental options
    options.accept_insecure_certs = True
    options.strict_file_interactability = False
    options.unhandled_prompt_behavior = "dismiss"
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])

    # Configure user data dir
    if user_data_dir and os.access(user_data_dir, mode=os.F_OK):
        try:
            options.add_argument(f"--user-data-dir={user_data_dir}")
            prefs_path = os.path.join(user_data_dir, "Default", "Preferences")
            with open(prefs_path, encoding="latin1", mode="r+") as fp:
                cfg = json.load(fp)
                cfg["profile"]["exit_type"] = None
                fp.seek(0, 0)
                json.dump(cfg, fp)
                logger.debug("Cleared exit_type flag")
        except Exception as e:
            logger.debug("Could not clear any bad exit_type flag | %s", e)

    # Logging configs
    if is_debug:
        LOGGER.setLevel(logging.WARN)
        options.add_argument("--log-level=0")
    else:
        LOGGER.setLevel(logging.CRITICAL)
        options.add_argument("--silent")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-logging")

    # initialize instance
    chrome = Chrome(
        options=options,
        keep_alive=True,
    )
    logger.info("Created chrome instance > %s", chrome.session_id)
    chrome.set_window_position(0, 0)

    setattr(chrome, "_web_element_cls", WebElement)
    _override_get(chrome)
    _release_queue(chrome)

    return chrome
