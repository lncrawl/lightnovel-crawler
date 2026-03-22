import html
import logging
import math
import os
import re
import unicodedata
from pathlib import Path
from typing import Dict

from PIL.Image import Image

from ...context import ctx
from ...core.crawler import Crawler
from ...models import Chapter, Volume
from ...utils.imgen import generate_cover_image
from ...utils.text_tools import normalize

logger = logging.getLogger(__name__)

DEFAULT_CHAPTER_PER_VOLUME = 100

_RE_SPACES = re.compile(r"\s+")


def format_title(text):
    name = html.unescape(str(text or ""))
    name = unicodedata.normalize("NFKC", name)
    return _RE_SPACES.sub(" ", name).strip().title()


def __format_volume(crawler: Crawler, vol_id_map: Dict[int, int]):
    if crawler.volumes:
        crawler.volumes = [vol if isinstance(vol, Volume) else Volume(**vol) for vol in crawler.volumes]
        next_id = crawler.volumes[-1].id + 1
        crawler.volumes.append(Volume(id=next_id, title="Others"))
        crawler.volumes.sort(key=lambda x: x.id)
    else:
        vol_count = math.ceil(len(crawler.chapters) / DEFAULT_CHAPTER_PER_VOLUME)
        crawler.volumes = [Volume(id=i + 1) for i in range(vol_count)]

    for index, item in enumerate(crawler.volumes):
        vol_id_map[item.id] = index
        item.id = index + 1
        item.chapter_count = 0
        item.extra["crawler_version"] = getattr(crawler, "version")
        item.title = format_title(item.title) or f"Volume {item.id}"


def __format_chapters(crawler: Crawler, vol_id_map: Dict[int, int]):
    crawler.chapters = [chap if isinstance(chap, Chapter) else Chapter(**chap) for chap in crawler.chapters]
    crawler.chapters.sort(key=lambda x: x.id)
    for index, item in enumerate(crawler.chapters):
        item.id = index + 1
        item.extra["crawler_version"] = getattr(crawler, "version")
        item.title = format_title(item.title) or f"Chapter {item.id}"

        default_vol = 1 + (index // DEFAULT_CHAPTER_PER_VOLUME)
        vol_index = vol_id_map.get(item.volume or default_vol)
        if vol_index is None:
            vol_index = vol_id_map.get(default_vol)
        if vol_index is None:
            vol_index = -1

        volume = crawler.volumes[vol_index]
        volume.chapter_count += 1
        item.volume = volume.id


def format_novel(crawler: Crawler):
    vol_id_map: Dict[int, int] = {}
    __format_volume(crawler, vol_id_map)
    __format_chapters(crawler, vol_id_map)
    crawler.volumes = [x for x in crawler.volumes if x.chapter_count]

    crawler.novel_title = format_title(crawler.novel_title)
    crawler.novel_author = format_title(crawler.novel_author)
    crawler.novel_tags = list(filter(None, map(normalize, set(crawler.novel_tags))))


def __save_image(img: Image, file: Path) -> None:
    if img.mode not in ("L", "RGB", "YCbCr", "RGBX"):
        if img.mode == "RGBa":
            img = img.convert("RGBA").convert("RGB")
        else:
            img = img.convert("RGB")

    file.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(file.as_posix()), "JPEG", optimized=True)


def download_image(crawler: Crawler, url: str, image_file: Path):
    if not url:
        return

    if image_file.is_file():
        os.utime(image_file)
        return

    try:
        img = crawler.download_image(url)
        __save_image(img, image_file)
        logger.info(f"Image saved: {url} -> {image_file}")
    except Exception as e:
        logger.error(
            f"Failed to download image: {repr(e)}",
            stack_info=ctx.logger.is_debug,
        )


def download_cover(crawler: Crawler, cover_file: Path):
    url = crawler.novel_cover
    if not url:
        return

    try:
        img = crawler.download_image(url)
        __save_image(img, cover_file)
        logger.info(f"Cover saved: {url} -> {cover_file}")
        return
    except Exception as e:
        logger.error(
            f"Failed to download cover: {repr(e)}",
            stack_info=ctx.logger.is_debug,
        )

    if cover_file.is_file():
        os.utime(cover_file)
        return

    try:
        img = generate_cover_image()
        __save_image(img, cover_file)
        logger.info(f"Cover generated: {cover_file}")
    except Exception as e:
        logger.error(
            f"Failed to generate cover: {repr(e)}",
            stack_info=ctx.logger.is_debug,
        )
