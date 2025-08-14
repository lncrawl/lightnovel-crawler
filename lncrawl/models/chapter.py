"""Chapter entity model.

Represents a chapter with metadata, HTML body, image map, and status.
Uses `Box` for attribute/dict-style access and JSON friendliness.
"""

from typing import Dict, Optional

from box import Box


class Chapter(Box):
    """A single chapter and its content/images.

    Fields:
    - id: 1-based chapter index
    - url: source URL
    - title: title text
    - volume: owning volume id
    - volume_title: owning volume title
    - body: cleaned HTML string
    - images: map of local filename -> original URL
    - success: whether the chapter content was successfully fetched
    """
    def __init__(
        self,
        id: int,
        url: str = "",
        title: str = "",
        volume: Optional[int] = None,
        volume_title: Optional[str] = None,
        body: Optional[str] = None,
        images: Dict[str, str] = dict(),
        success: bool = False,
        **kwargs,
    ) -> None:
        self.id = id
        self.url = url
        self.title = title
        self.volume = volume
        self.volume_title = volume_title
        self.body = body
        self.images = images
        self.success = success
        self.update(kwargs)

    @staticmethod
    def without_body(item: "Chapter") -> "Chapter":
        """Return a shallow copy of the chapter with `body` cleared."""
        result = item.copy()
        result.body = None
        return result
