from abc import abstractmethod
from typing import Generator, Union

from ...core.soup import PageSoup
from ...models import Chapter, Volume
from .general import GeneralSoupTemplate


class ChapterWithVolumeSoupTemplate(GeneralSoupTemplate):
    def parse_chapter_list(self, soup: PageSoup) -> Generator[Union[Chapter, Volume], None, None]:
        vol_id = 0
        chap_id = 0
        for vol in self.select_volume_tags(soup):
            vol_id += 1
            vol_item = self.parse_volume_item(vol, vol_id)
            yield vol_item
            for tag in self.select_chapter_tags(vol, vol_item, soup):
                chap_id += 1
                item = self.parse_chapter_item(tag, chap_id, vol_item)
                item.volume = vol_id
                yield item

    @abstractmethod
    def select_volume_tags(self, soup: PageSoup) -> Generator[PageSoup, None, None]:
        """Select volume list item tags from the page soup"""
        raise NotImplementedError()

    def parse_volume_item(self, tag: PageSoup, id: int) -> Volume:
        """Parse a single volume from volume list item tag"""
        return Volume(id=id, title=tag.text)

    @abstractmethod
    def select_chapter_tags(self, tag: PageSoup, vol: Volume, soup: PageSoup) -> Generator[PageSoup, None, None]:
        """Select chapter list item tags from volume tag"""
        raise NotImplementedError()

    def parse_chapter_item(self, tag: PageSoup, id: int, vol: Volume) -> Chapter:
        """Parse a single chapter from chapter list item tag"""
        return Chapter(
            id=id,
            volume=vol.id,
            title=tag.text,
            url=self.absolute_url(tag["href"]),
        )
