# Creating Source Crawlers

This guide explains how to add support for new novel sources to Lightnovel Crawler.

## Quick Start

1. Create a file in `sources/{lang}/` (e.g., `sources/en/m/mysite.py`)
2. Extend the `Crawler` class
3. Implement required methods
4. Test locally

## File Location

Source crawlers are organized by language:
- `sources/en/` - English sources (further split alphabetically: `a/`, `b/`, etc.)
- `sources/zh/` - Chinese sources
- `sources/ja/` - Japanese sources
- `sources/multi/` - Multi-language sources

For English sources, place your file in the appropriate letter subdirectory based on the site name.

## Basic Structure

```python
# -*- coding: utf-8 -*-
import logging
from lncrawl.core.crawler import Crawler

logger = logging.getLogger(__name__)


class MySiteCrawler(Crawler):
    # Required: URL patterns this crawler handles
    base_url = [
        "https://mysite.com/",
        "https://www.mysite.com/",
    ]

    def read_novel_info(self):
        """Parse novel metadata from the novel's main page."""
        # Required implementation
        pass

    def download_chapter_body(self, chapter):
        """Download and return chapter content as HTML."""
        # Required implementation
        pass
```

## Required Methods

### `read_novel_info(self)`

Parses the novel's main page and populates:
- `self.novel_title` - Novel title (string)
- `self.novel_cover` - Cover image URL (string)
- `self.novel_author` - Author name (string, optional)
- `self.volumes` - List of volume dictionaries
- `self.chapters` - List of chapter dictionaries

**Example:**
```python
def read_novel_info(self):
    soup = self.get_soup(self.novel_url)

    # Get title and cover
    self.novel_title = soup.select_one("h1.title").text.strip()
    self.novel_cover = self.absolute_url(soup.select_one("img.cover")["src"])

    # Get author (optional)
    author_elem = soup.select_one("span.author")
    if author_elem:
        self.novel_author = author_elem.text.strip()

    # Parse chapters
    for idx, a in enumerate(soup.select("ul.chapters a"), 1):
        vol_id = (idx - 1) // 100 + 1
        if vol_id > len(self.volumes):
            self.volumes.append({"id": vol_id, "title": f"Volume {vol_id}"})

        self.chapters.append({
            "id": idx,
            "volume": vol_id,
            "title": a.text.strip(),
            "url": self.absolute_url(a["href"]),
        })
```

### `download_chapter_body(self, chapter)`

Downloads a single chapter and returns its content as HTML.

**Parameters:**
- `chapter` - Dictionary with chapter info (id, url, title, etc.)

**Returns:** HTML string of chapter content

**Example:**
```python
def download_chapter_body(self, chapter):
    soup = self.get_soup(chapter["url"])

    # Find the content container
    content = soup.select_one("div.chapter-content")

    # Clean and return the content
    return self.cleaner.extract_contents(content)
```

## Optional Methods

### `initialize(self)`

Called before any scraping. Use for setup tasks:
- Configure cleaner rules
- Set custom headers
- Initialize state

```python
def initialize(self):
    # Add CSS selectors for elements to remove
    self.cleaner.bad_css.update([
        "div.ads",
        "script",
        "iframe",
    ])

    # Add tags to remove
    self.cleaner.bad_tags.update(["h1", "hr"])
```

### `search_novel(self, query)`

Enables search functionality. Returns list of search results.

```python
def search_novel(self, query):
    url = f"https://mysite.com/search?q={query}"
    soup = self.get_soup(url)

    results = []
    for item in soup.select("div.search-result"):
        results.append({
            "title": item.select_one("h3").text.strip(),
            "url": self.absolute_url(item.select_one("a")["href"]),
            "info": item.select_one("span.info").text.strip(),  # Optional
        })
    return results
```

### `login(self, email, password)`

Enables authentication for sites requiring login.

```python
def login(self, email, password):
    response = self.submit_form(
        "https://mysite.com/login",
        data={"email": email, "password": password}
    )
    return "Welcome" in response.text
```

## Useful Properties and Methods

### HTTP Requests

| Method | Description |
|--------|-------------|
| `self.get_soup(url)` | GET request, returns BeautifulSoup |
| `self.post_soup(url, data)` | POST request, returns BeautifulSoup |
| `self.get_json(url)` | GET request, returns JSON |
| `self.post_json(url, data)` | POST request, returns JSON |
| `self.submit_form(url, data)` | Submit form data |

### URL Handling

| Method | Description |
|--------|-------------|
| `self.absolute_url(path)` | Convert relative URL to absolute |
| `self.novel_url` | The novel's main URL |

### Content Cleaning

The `self.cleaner` object helps clean HTML content:

```python
# Remove specific CSS selectors
self.cleaner.bad_css.update(["div.ads", "span.watermark"])

# Remove specific tags
self.cleaner.bad_tags.update(["script", "style"])

# Extract clean content
html = self.cleaner.extract_contents(soup_element)
```

## Using Templates

For sites with common structures, templates are available in `lncrawl/templates/`:

```python
from lncrawl.templates.novelfull import NovelFullTemplate

class MySiteCrawler(NovelFullTemplate):
    base_url = "https://mysite.com/"

    # Override methods as needed
```

## Testing Your Crawler

1. **Install in development mode:**
   ```bash
   make setup && make install
   ```

2. **Test with a specific URL:**
   ```bash
   python -m lncrawl -s "https://mysite.com/novel/example" --first 3 -f
   ```

3. **Check source registration:**
   ```bash
   python -m lncrawl sources list | grep mysite
   ```

## Best Practices

1. **Use logging** for debug information:
   ```python
   logger.info("Found %d chapters", len(self.chapters))
   ```

2. **Handle errors gracefully** - Sites may have inconsistent HTML

3. **Respect rate limits** - Don't hammer the server

4. **Test edge cases**:
   - Novels with many chapters
   - Novels with special characters in titles
   - Novels without covers or authors

5. **Clean content thoroughly** - Remove ads, navigation, etc.

## Example: Complete Crawler

```python
# -*- coding: utf-8 -*-
import logging
from lncrawl.core.crawler import Crawler

logger = logging.getLogger(__name__)


class ExampleCrawler(Crawler):
    base_url = ["https://example-novel-site.com/"]

    def initialize(self):
        self.cleaner.bad_css.update([
            "div.advertisement",
            "div.social-share",
        ])

    def search_novel(self, query):
        soup = self.get_soup(f"{self.home_url}search?q={query}")
        results = []
        for item in soup.select("div.search-item"):
            a = item.select_one("a.title")
            results.append({
                "title": a.text.strip(),
                "url": self.absolute_url(a["href"]),
            })
        return results

    def read_novel_info(self):
        soup = self.get_soup(self.novel_url)

        self.novel_title = soup.select_one("h1.novel-title").text.strip()

        cover = soup.select_one("img.novel-cover")
        if cover:
            self.novel_cover = self.absolute_url(cover["src"])

        author = soup.select_one("span.author-name")
        if author:
            self.novel_author = author.text.strip()

        for idx, a in enumerate(soup.select("ul.chapter-list a"), 1):
            vol_id = (idx - 1) // 100 + 1
            if vol_id > len(self.volumes):
                self.volumes.append({"id": vol_id, "title": f"Volume {vol_id}"})

            self.chapters.append({
                "id": idx,
                "volume": vol_id,
                "title": a.text.strip(),
                "url": self.absolute_url(a["href"]),
            })

        logger.info("Found %d chapters", len(self.chapters))

    def download_chapter_body(self, chapter):
        soup = self.get_soup(chapter["url"])
        content = soup.select_one("div.chapter-content")
        return self.cleaner.extract_contents(content)
```
