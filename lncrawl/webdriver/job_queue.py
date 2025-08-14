"""Limit concurrent WebDriver instances and track lifecycle for cleanup."""
import atexit
import logging
from threading import Semaphore, Thread
from typing import List, Optional

from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)

MAX_BROWSER_INSTANCES = 8

__open_browsers: List[WebDriver] = []
__semaphore = Semaphore(MAX_BROWSER_INSTANCES)


def __override_quit(driver: WebDriver):
    """Wrap `driver.quit` to release the semaphore and remove from tracking."""
    __open_browsers.append(driver)
    original = Thread(target=driver.quit, daemon=True)

    def override():
        if driver in __open_browsers:
            __semaphore.release()
            __open_browsers.remove(driver)
            logger.info("Destroyed instance: %s", driver.session_id)
        if not original._started.is_set():  # type:ignore
            original.start()

    driver.quit = override  # type:ignore


def _acquire_queue(timeout: Optional[float] = None):
    """Acquire a slot for creating a WebDriver, respecting a timeout."""
    acquired = __semaphore.acquire(True, timeout)
    if not acquired:
        raise TimeoutError("Failed to acquire semaphore")


def _release_queue(driver: WebDriver):
    """Register the driver and override its quit for tracked release."""
    __override_quit(driver)



def check_active(driver: Optional[WebDriver]) -> bool:
    """Return True if the driver is still tracked as active."""
    if not isinstance(driver, WebDriver):
        return False
    return driver in __open_browsers


def cleanup_drivers():
    """Close and quit all tracked drivers at process exit."""
    for driver in __open_browsers:
        driver.close()
        driver.quit()


atexit.register(cleanup_drivers)
