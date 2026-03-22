from pathlib import Path

IMAGES_DIR = Path(__file__).parent


def favicon_icon() -> Path:
    """
    Returns the path to the favicon.ico image file, if it exists.
    """
    return IMAGES_DIR / "favicon.ico"
