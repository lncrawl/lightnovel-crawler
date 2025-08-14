"""Task queue and concurrency utilities.

Provides a thin wrapper around ThreadPoolExecutor with progress bars, domain
gating, rate limiting, and helpers to resolve futures as generators or lists.
"""

import atexit
import logging
import os
from abc import ABC
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from threading import Event, Semaphore, Thread
from typing import Any, Dict, Generator, Iterable, List, Optional

from tqdm import tqdm

from ..utils.ratelimit import RateLimiter
from .exeptions import LNException

logger = logging.getLogger(__name__)

MAX_REQUESTS_PER_DOMAIN = 5

_resolver = Semaphore(1)
_host_semaphores: Dict[str, Semaphore] = {}


class TaskManager(ABC):
    def __init__(
        self,
        workers: Optional[int] = None,
        ratelimit: Optional[float] = None,
    ) -> None:
        """Initialize executor and optional rate limiter."""
        self.init_executor(workers, ratelimit)

    def close(self) -> None:
        self.shutdown()

    @property
    def executor(self) -> ThreadPoolExecutor:
        return self._executor

    @property
    def futures(self) -> List[Future]:
        return self._futures

    @property
    def workers(self):
        return self._executor._max_workers

    def shutdown(self, wait=False):
        if hasattr(self, "_executor"):
            self._submit = None
            self._executor.shutdown(wait)
        if hasattr(self, "_limiter"):
            self._limiter.shutdown()

    def init_executor(
        self,
        workers: Optional[int] = None,
        ratelimit: Optional[float] = None,
    ):
        """Create a fresh executor and configure rate limiting if requested."""
        self._futures: List[Future] = []
        self.close()  # cleanup previous initialization

        if ratelimit and ratelimit > 0:
            workers = 1  # use single worker if ratelimit is being applied
            self._limiter = RateLimiter(ratelimit)
        elif hasattr(self, "_limiter"):
            del self._limiter

        self._executor = ThreadPoolExecutor(
            max_workers=workers,
            thread_name_prefix="lncrawl_scraper",
        )

        self._submit = self._executor.submit
        setattr(self._executor, "submit", self.submit_task)

    def submit_task(self, fn, *args, **kwargs) -> Future:
        """Submit a task (respecting rate limit if configured) and track it."""
        if hasattr(self, "_limiter"):
            fn = self._limiter.wrap(fn)
        if not self._submit:
            raise Exception("No executor is available")
        future = self._submit(fn, *args, **kwargs)
        self._futures.append(future)
        return future

    @staticmethod
    def progress_bar(
        iterable: Optional[Iterable] = None,
        unit: Optional[str] = None,
        desc: Optional[str] = None,
        total: Optional[float] = None,
        disable: bool = False,
    ) -> tqdm:
        if os.getenv("debug_mode"):
            disable = True

        if not disable:
            # Since we are showing progress bar, it is not good to
            # resolve multiple list of futures at once
            if not _resolver.acquire(True, 30):
                pass

        bar = tqdm(
            iterable=iterable,
            desc=desc or '',
            unit=unit or 'item',
            total=total,
            disable=disable,
        )

        original_close = bar.close
        atexit.register(original_close)

        def extended_close() -> None:
            atexit.unregister(original_close)
            if not bar.disable:
                _resolver.release()
            original_close()

        bar.close = extended_close  # type: ignore
        return bar

    def domain_gate(self, hostname: Optional[str]):
        """Provide a per-host semaphore to limit concurrent requests."""
        if hostname is None:
            hostname = ''
        if hostname not in _host_semaphores:
            _host_semaphores[hostname] = Semaphore(MAX_REQUESTS_PER_DOMAIN)
        return _host_semaphores[hostname]

    def cancel_futures(self, futures: Iterable[Future]) -> None:
        """Cancel any not-yet-done futures in the provided iterable."""
        if not futures:
            return
        for future in futures:
            if not future.done():
                future.cancel()

    def resolve_as_generator(
        self,
        futures: Iterable[Future],
        disable_bar: bool = False,
        desc: Optional[str] = None,
        unit: Optional[str] = None,
        fail_fast: bool = False,
        signal=Event(),
    ) -> Generator[Any, None, None]:
        """Yield results as futures complete, updating a progress bar."""
        futures = list(futures)
        if not futures:
            return

        bar = self.progress_bar(
            total=len(futures),
            desc=desc,
            unit=unit,
            disable=disable_bar,
        )
        try:
            for future in as_completed(futures):
                if signal.is_set():
                    return  # canceled
                if fail_fast:
                    yield future.result()
                    bar.update()
                    continue
                try:
                    yield future.result()
                except KeyboardInterrupt:
                    signal.set()
                    raise
                except LNException as e:
                    bar.clear()
                    print(str(e))
                except Exception as e:
                    yield None
                    if bar.disable:
                        logger.exception("Failure to resolve future")
                    else:
                        bar.clear()
                        logger.warning(f"{type(e).__name__}: {e}")
                finally:
                    bar.update()
        except KeyboardInterrupt:
            signal.set()
            raise
        finally:
            Thread(
                target=self.cancel_futures,
                kwargs=dict(futures=futures),
                # daemon=True,
            ).start()
            bar.close()

    def resolve_futures(
        self,
        futures: Iterable[Future],
        disable_bar: bool = False,
        desc: Optional[str] = None,
        unit: Optional[str] = None,
        fail_fast: bool = False,
        signal=Event(),
    ) -> list:
        """Resolve all futures and return their results as a list."""

        return list(
            self.resolve_as_generator(
                futures=futures,
                disable_bar=disable_bar,
                desc=desc,
                unit=unit,
                fail_fast=fail_fast,
                signal=signal,
            )
        )
