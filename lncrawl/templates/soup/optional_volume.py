from abc import abstractmethod
from typing import Generator, Union

from ...core.soup import PageSoup
from ...models import Chapter, Volume
from .general import GeneralSoupTemplate


class OptionalVolumeSoupTemplate(GeneralSoupTemplate):
    def parse_chapter_list(
        self, soup: PageSoup
    ) -> Generator[Union[Chapter, Volume], None, None]:
        vol_id = 0
        chap_id = 0
        for vol in self.select_volume_tags(soup):
            vol_id += 1
            vol_item = self.parse_volume_item(vol, vol_id)
            yield vol_item
            for tag in self.select_chapter_tags(vol):
                chap_id += 1
                item = self.parse_chapter_item(tag, chap_id, vol_item)
                item.volume = vol_id
                yield item

        if chap_id > 0:
            return

        parent = soup.select_one("html")
        if not parent:
            return

        vol_id = 1
        vol_item = self.parse_volume_item(parent, vol_id)
        yield vol_item

        chap_id = 1
        for tag in self.select_chapter_tags(parent):
            if chap_id % 100 == 0:
                vol_id += 1
                vol_item = self.parse_volume_item(parent, vol_id)
                yield vol_item
            item = self.parse_chapter_item(tag, chap_id, vol_item)
            item.volume = vol_id
            chap_id += 1
            yield item

    def select_volume_tags(self, soup: PageSoup) -> Generator[PageSoup, None, None]:
        yield from ()

    def parse_volume_item(self, tag: PageSoup, id: int) -> Volume:
        return Volume(id=id)

    @abstractmethod
    def select_chapter_tags(self, parent: PageSoup) -> Generator[PageSoup, None, None]:
        raise NotImplementedError()

    @abstractmethod
    def parse_chapter_item(self, tag: PageSoup, id: int, vol: Volume) -> Chapter:
        raise NotImplementedError()
