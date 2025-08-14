"""Expose existing JSON artifacts as output files for archiving.

This binder does not generate content; it points to the pre-written
`meta.json` and per-chapter `json/*.json` files.
"""

import logging
from pathlib import Path
from typing import Generator

logger = logging.getLogger(__name__)


def make_jsons(app, data) -> Generator[str, None, None]:
    """Yield paths of metadata and chapter JSON files if present."""
    root_path = Path(app.output_path)
    yield str(root_path / 'meta.json')
    for vol in data:
        for chap in data[vol]:
            file_name = "%s.json" % str(chap["id"]).rjust(5, "0")
            file_path = root_path / "json" / file_name
            if file_path.is_file():
                yield str(file_path)
