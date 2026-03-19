import json
import logging
import os
import time
import uuid
from datetime import datetime
from decimal import Decimal
from functools import cached_property
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, cast

import dotenv
import typer

T = TypeVar("T")

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.absolute()
APP_DIR = Path(
    os.getenv("LNCRAWL_DATA_PATH")
    or typer.get_app_dir(
        "LNCrawl",
        force_posix=True,
        roaming=True,
    )
).absolute()
DEFAULT_CONFIG_FILE = APP_DIR / "config.json"


# ------------------------------------------------------------------ #
#                            Utilitites                              #
# ------------------------------------------------------------------ #
def _serialize(obj: object) -> Any:
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    if isinstance(obj, (list, tuple, set)):
        return [_serialize(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)  # fallback for unknown types


def _deserialize(val: Any, typ: Type[T]) -> T:
    if val is None:
        return cast(T, None)
    if typ in (str, int, float, bool):
        return typ(val)  # type: ignore
    if typ == Decimal:
        return cast(T, Decimal(val))
    if typ == datetime:
        return cast(T, datetime.fromisoformat(val))
    if typ in (list, tuple, set):
        seq = json.loads(val) if isinstance(val, str) else val
        return cast(T, typ(seq))  # type: ignore
    if typ == dict:
        return cast(T, json.loads(val) if isinstance(val, str) else val)
    return cast(T, val)


def _traverse(obj: object) -> None:
    for name in dir(obj):
        if name.startswith("_"):
            continue
        attr = getattr(type(obj), name, None)
        if isinstance(attr, property) and attr.fset:
            value = getattr(obj, name)
            setattr(obj, name, value)
        elif isinstance(attr, cached_property):
            value = getattr(obj, name)
            if isinstance(value, _Section):
                _traverse(value)


def _merge(target: dict, source: dict) -> None:
    """Merge source into target, overriding existing values."""
    for key, value in source.items():
        if isinstance(target.get(key), dict) and isinstance(value, dict):
            _merge(target[key], value)
        else:
            target[key] = value


def _update(target: dict, source: dict) -> dict:
    """Update target with source, returning deprecated values."""
    deprecated = {}
    for key, value in source.items():
        if key in target:
            if isinstance(target[key], dict) and isinstance(value, dict):
                inner = _update(target[key], value)
                if inner:
                    deprecated[key] = inner
            elif type(value) is type(target[key]):
                target[key] = value
            else:
                deprecated[key] = value
        else:
            deprecated[key] = value
    return deprecated


# ------------------------------------------------------------------ #
#                             Root Config                            #
# ------------------------------------------------------------------ #
class Config(object):
    def __init__(self) -> None:
        dotenv.load_dotenv()
        self.config_file: Optional[Path] = None
        self._data: Dict[str, Any] = {}
        _traverse(self)
        self._defaults = self._data.copy()

    @cached_property
    def app(self):
        return AppConfig(self)

    @cached_property
    def db(self):
        return DatabaseConfig(self)

    @cached_property
    def crawler(self):
        return CrawlerConfig(self)

    @cached_property
    def server(self):
        return ServerConfig(self)

    @cached_property
    def mail(self):
        return MailConfig(self)

    # -------------------------------------------------------------- #

    def load(self, file: Optional[Path] = None) -> None:
        """
        Loads configurations from given file, env var or default config.

        - Loads from param `file` if provided
        - Loads from `LNCRAWL_CONFIG` env var if available
        - Loads from default config file otherwise
        """
        env_file = os.getenv("LNCRAWL_CONFIG")
        if not file and env_file:
            file = Path(env_file)

        file = file or DEFAULT_CONFIG_FILE
        if file == self.config_file:
            return

        if file.is_file():
            try:
                source = json.loads(file.read_text(encoding="utf-8"))
                assert isinstance(source, dict)

                self.config_file = None
                self._data = self._defaults.copy()
                old_deprecated = source.pop("__deprecated__", {})
                new_deprecated = _update(self._data, source)
                _merge(new_deprecated, old_deprecated)

                if new_deprecated:
                    self._data["__deprecated__"] = new_deprecated
            except Exception:
                logger.error(f"Failed to load config file: {file}", exc_info=True)
                return

        self.config_file = file
        logger.info(f"Config file: {file}")

        self.save()

    def save(self) -> None:
        if not self.config_file:
            return
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        tid = time.thread_time_ns() % 1000
        tmp = self.config_file.with_suffix(f".json.tmp{tid}")
        content = json.dumps(self._data, indent=2, ensure_ascii=False)
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, self.config_file)

    # -------------------------------------------------------------- #

    def get(self, section: str, key: str, default: Union[None, T, Callable[[], T]] = None) -> Any:
        sub: dict = self._data.setdefault(section, {})
        if key not in sub:
            if callable(default):
                sub[key] = default()
            elif default is not None:
                sub[key] = default
            else:
                raise ValueError(f"{section}.{key} is not set")
        return _deserialize(sub[key], type(sub[key]))

    def set(self, section: str, key: str, value: T) -> None:
        sub: dict = self._data.setdefault(section, {})
        if sub.get(key) is not None:
            value = _deserialize(value, type(sub[key]))
        sub[key] = _serialize(value)
        self.save()


# ------------------------------------------------------------------ #
#                            Section Base                            #
# ------------------------------------------------------------------ #
class _Section(object):
    section: str

    def __init__(self, parent: Config) -> None:
        self.root = parent
        if not self.section:
            raise ValueError(f"section is not defined for {self}")

    def _get(self, key: str, default: Union[T, Callable[[], Any]]) -> T:
        return self.root.get(self.section, key, default)

    def _set(self, key: str, value: Any) -> None:
        self.root.set(self.section, key, value)


# ------------------------------------------------------------------ #
#                             App Section                            #
# ------------------------------------------------------------------ #
class AppConfig(_Section):
    section = "app"
    name = "Lightnovel Crawler"

    @cached_property
    def version(self) -> str:
        return (ROOT_DIR / "VERSION").read_text(encoding="utf8").strip()

    @cached_property
    def output_path(self) -> Path:
        return APP_DIR

    @property
    def openai_key(self) -> str:
        return self._get("openai_api_key", "")

    @openai_key.setter
    def openai_key(self, v: str) -> None:
        self._set("openai_api_key", v)


# ------------------------------------------------------------------ #
#                          Database Section                          #
# ------------------------------------------------------------------ #
class DatabaseConfig(_Section):
    section = "database"

    def __url(self) -> str:
        env_url = os.getenv("DATABASE_URL")
        sqlite_url = f"sqlite:///{(APP_DIR / 'sqlite.db').resolve().as_posix()}"
        return env_url or sqlite_url

    @property
    def url(self) -> str:
        """
        Database URL.

        Example:
        - postgresql+psycopg://pguser:pgpass@postgres:5432/lncrawl
        - mysql+pymysql://user:password@mysql:3306/lncrawl
        - sqlite:////home/user/sqlite.db
        - sqlite:///sqlite.db
        """
        return self._get("url", self.__url)

    @url.setter
    def url(self, v: str) -> None:
        self._set("url", v)

    @property
    def pool_size(self) -> int:
        """Number of connections to maintain in the pool"""
        return self._get("pool_size", 10)

    @pool_size.setter
    def pool_size(self, v: int) -> None:
        self._set("pool_size", v)

    @property
    def pool_timeout(self) -> int:
        """Seconds to wait before giving up on getting a connection"""
        return self._get("pool_timeout", 30)

    @pool_timeout.setter
    def pool_timeout(self, v: int) -> None:
        self._set("pool_timeout", v)

    @property
    def pool_recycle(self) -> int:
        """Recycle connections after this many seconds (prevents stale connections)"""
        return self._get("pool_recycle", 3600)

    @pool_recycle.setter
    def pool_recycle(self, v: int) -> None:
        self._set("pool_recycle", v)

    @property
    def connect_timeout(self) -> int:
        """Timeout for database connection in seconds"""
        return self._get("connect_timeout", 10)

    @connect_timeout.setter
    def connect_timeout(self, v: int) -> None:
        self._set("connect_timeout", v)

    @property
    def admin_email(self) -> str:
        """Admin email"""
        return self._get("admin_email", "admin")

    @admin_email.setter
    def admin_email(self, v: str) -> None:
        self._set("admin_email", v)

    @property
    def admin_password(self) -> str:
        """Admin password"""
        return self._get("admin_password", "admin")

    @admin_password.setter
    def admin_password(self, v: str) -> None:
        self._set("admin_password", v)


# ------------------------------------------------------------------ #
#                           Crawler Section                          #
# ------------------------------------------------------------------ #
class CrawlerConfig(_Section):
    section = "crawler"

    @cached_property
    def local_sources(self) -> Path:
        for dir in [ROOT_DIR, ROOT_DIR.parent]:
            folder = dir / "sources"
            if folder.is_dir():
                return folder
        raise ValueError("No local sources")

    @cached_property
    def local_index_file(self) -> Path:
        return self.local_sources / "_index.json"

    @cached_property
    def user_sources(self) -> Path:
        return APP_DIR / "sources"

    @cached_property
    def user_index_file(self) -> Path:
        return self.user_sources / "_index.json"

    @property
    def can_use_browser(self) -> bool:
        return self._get("can_use_browser", True)

    @can_use_browser.setter
    def can_use_browser(self, v: bool) -> None:
        self._set("can_use_browser", v)

    @property
    def selenium_grid(self) -> str:
        return self._get("selenium_grid", os.getenv("SELENIUM_GRID", ""))

    @selenium_grid.setter
    def selenium_grid(self, url: str) -> None:
        self._set("selenium_grid", url)

    @property
    def index_file_download_url(self) -> str:
        return "https://raw.githubusercontent.com/lncrawl/lightnovel-crawler/dev/sources/_index.zip"

    @property
    def ignore_images(self) -> bool:
        return self._get("ignore_images", False)

    @ignore_images.setter
    def ignore_images(self, v: bool) -> None:
        self._set("ignore_images", v)

    @property
    def runner_concurrency(self) -> int:
        """Scheduler concurrency"""
        return self._get("runner_concurrency", 5)

    @runner_concurrency.setter
    def runner_concurrency(self, v: int) -> None:
        self._set("runner_concurrency", v)

    @property
    def runner_cooldown(self) -> int:
        """Crawler job cooldown in seconds"""
        return self._get("runner_cooldown", 1)

    @runner_cooldown.setter
    def runner_cooldown(self, v: int) -> None:
        self._set("runner_cooldown", v)

    @property
    def scrubber_cooldown(self) -> int:
        """Scrubber job cooldown in seconds"""
        return self._get("cleaner_cooldown", 30 * 60)

    @scrubber_cooldown.setter
    def scrubber_cooldown(self, v: int) -> None:
        self._set("cleaner_cooldown", v)

    @property
    def runner_reset_interval(self) -> int:
        """Scheduler restart interval in seconds"""
        return self._get("runner_reset_interval", 4 * 3600)

    @runner_reset_interval.setter
    def runner_reset_interval(self, v: int) -> None:
        self._set("runner_reset_interval", v)

    @property
    def disk_size_limit(self) -> int:
        """Maximum disk size limit of crawled data in bytes"""
        mb = self._get("disk_size_limit_mb", 0)
        return mb * 1024 * 1024

    @disk_size_limit.setter
    def disk_size_limit(self, bytes_val: int) -> None:
        mb = None if bytes_val is None else bytes_val // (1024 * 1024)
        self._set("disk_size_limit_mb", mb)


# ------------------------------------------------------------------ #
#                           Server Section                           #
# ------------------------------------------------------------------ #
class ServerConfig(_Section):
    section = "server"

    @property
    def base_url(self) -> str:
        return self._get("base_url", "http://localhost:8080").strip("/")

    @base_url.setter
    def base_url(self, v: str) -> None:
        self._set("base_url", v)

    @property
    def token_secret(self) -> str:
        return self._get("token_secret", lambda: str(uuid.uuid4()))

    @token_secret.setter
    def token_secret(self, v: str) -> None:
        self._set("token_secret", v)

    @property
    def token_algo(self) -> str:
        return self._get("token_algorithm", "HS256")

    @token_algo.setter
    def token_algo(self, v: str) -> None:
        self._set("token_algorithm", v)

    @property
    def token_expiry(self) -> int:
        return self._get("token_expiry_minutes", lambda: 7 * 24 * 60)

    @token_expiry.setter
    def token_expiry(self, v: int) -> None:
        self._set("token_expiry_minutes", v)


# ------------------------------------------------------------------ #
#                            Mail Section                            #
# ------------------------------------------------------------------ #
class MailConfig(_Section):
    section = "mail"

    @property
    def smtp_server(self) -> str:
        return self._get("smtp_server", "localhost")

    @smtp_server.setter
    def smtp_server(self, v: str) -> None:
        self._set("smtp_server", v)

    @property
    def smtp_port(self) -> int:
        return self._get("smtp_port", 1025)

    @smtp_port.setter
    def smtp_port(self, v: int) -> None:
        self._set("smtp_port", v)

    @property
    def smtp_username(self) -> str:
        return self._get("smtp_username", "")

    @smtp_username.setter
    def smtp_username(self, v: str) -> None:
        self._set("smtp_username", v)

    @property
    def smtp_password(self) -> str:
        return self._get("smtp_password", "")

    @smtp_password.setter
    def smtp_password(self, v: str) -> None:
        self._set("smtp_password", v)

    @property
    def smtp_sender(self) -> str:
        return self._get("smtp_sender", "")

    @smtp_sender.setter
    def smtp_sender(self, v: str) -> None:
        self._set("smtp_sender", v)
