from urllib.parse import urlparse

from .text_tools import normalize


def normalize_url(url: str) -> str:
    """Normalizes the URL string"""
    return normalize(url).encode("idna").decode("ascii")


def validate_url(url: str, allowed_schemes=["http", "https"]) -> bool:
    """Return True if `url` is a syntactically valid URL for the given schemes."""
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc, parsed.scheme in allowed_schemes])


def extract_base(url: str) -> str:
    """Extracts the base url."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def extract_host(url: str) -> str:
    """Normalize and extracts host with port from a URL-like string."""
    parsed = urlparse(url)

    host = parsed.hostname
    port = parsed.port
    if not host:
        return ""

    host = normalize_url(host)
    if host.startswith("www."):
        host = host[4:]
    if port:
        host += f":{port}"
    return host
