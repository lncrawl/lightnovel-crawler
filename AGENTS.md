# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

The [Makefile](Makefile) wraps [uv](https://docs.astral.sh/uv/); `make install` / `make sync` use `uv sync --extra dev`.

```bash
# Setup and install
make setup            # Sync submodules and install uv
make install          # setup + uv sync (default target: `make` or `make all`)
make sync             # uv sync only
make upgrade          # setup + uv sync --upgrade

# Development servers and tooling
make start            # Backend server only
make watch            # Backend with auto-reload
make lint             # ruff format and check
make add-source       # Guided CLI to add a new source crawler

# Version (writes lncrawl/VERSION via scripts/bump.py)
make patch            # bump patch
make minor            # bump minor
make major            # bump major

# Build
make build            # print version + install + wheel + exe
make build-wheel      # Python wheel (python -m build -w)
make build-exe        # PyInstaller (setup_pyi.py)

# Dependencies (second word is the package name)
make add-dep <package>   # e.g. make add-dep httpx
make add-dev <package>   # add to optional extra `dev`
make rm-dep <package>
make rm-dev <package>

# Docker (uses compose.yml in repo root unless you pass -f elsewhere)
make docker-build     # Base image, then app image
make docker-base      # Base image only (Calibre + deps)
make docker-up        # docker compose up -d
make docker-down      # docker compose down
make docker-logs      # docker compose logs -f

# Other
make version          # Print version from lncrawl/VERSION
make clean            # Remove .venv, logs, build, dist, *.egg-info, __pycache__
make submodule        # git submodule sync + update (init, recursive, remote)


# Update repo + submodules without make
git pull && make submodule

# Run CLI from source
uv run python -m lncrawl
```

## Architecture Overview

### Entry Point & Application Context

- **`lncrawl/__main__.py`**: Entry point, calls `main()` from `lncrawl.app`
- **`lncrawl/context.py`**: `AppContext` singleton manages all services via lazy-loaded properties
- **`lncrawl/app.py`**: CLI setup using Typer, registers subcommands (crawl, search, server, sources, config)

### Source Crawlers

**Location**: `sources/` - Organized by language (`en/`, `zh/`, `ja/`, etc.), English further split alphabetically

**Key Base Classes**:

- `lncrawl/core/crawler.py`: `Crawler` class - extend this to create new source crawlers
  - Required: `read_novel_info()`, `download_chapter_body()`
  - Optional: `initialize()`, `login()`, `search_novel()`
- `lncrawl/core/scraper.py`: `Scraper` base - HTTP requests, BeautifulSoup parsing, Cloudflare handling
- `lncrawl/core/taskman.py`: `TaskManager` - ThreadPoolExecutor for concurrent operations

**Crawler Registration**: `lncrawl/services/sources/service.py`

- Crawlers auto-discovered by importing Python files from source directories
- Each crawler has: `__id__`, `base_url`, `version` metadata
- Full-text search index for fast source lookup

### Server/API

**FastAPI Server**: `lncrawl/server/app.py`

- REST API at `/api`, frontend at `/`
- Endpoints in `lncrawl/server/api/`: novels, chapters, volumes, jobs, artifacts, auth, libraries

### Output Generation

**Binder Service**: `lncrawl/services/binder/`

- `epub.py`: Native EPUB generation (primary format)
- `calibre.py`: Converts EPUB to other formats (MOBI, PDF, DOCX, etc.) via Calibre
- `json.py`, `text.py`: JSON and plain text formats

### Data Models

- **`lncrawl/models/`**: Chapter, Volume, Novel, SearchResult, Session
- **`lncrawl/dao/`**: Database access objects (SQLAlchemy/SQLModel)

### Services (via AppContext)

`lncrawl` is structured around a set of **services**, each responsible for a major piece of application functionality. All core services are accessed via the singleton `AppContext` (usually as `ctx` in code). This allows shared, on-demand initialization and simple dependency management throughout the app.

**Key services available from the app context:**

- **config**: Configuration manager (loads and saves user settings, environment variables, CLI flags)
- **db**: Database access (SQLModel, manages library, jobs, novels, chapters)
- **http**: HTTP client (handles web requests, session, caching, retries, Cloudflare support)
- **sources**: Source crawler registry/discovery (loads all available crawlers, search/index)
- **crawler**: The currently selected/active crawler instance (handles all scraping logic for a selected source)
- **binder**: Output/binding manager (handles EPUB generation, invoking Calibre for conversions, text export)
- **jobs**: Background job/task queue (for crawling, downloads, conversions)
- **novels**: Novel library management (add/remove novels, metadata)
- **chapters**: Chapters manager (fetch/save chapter data)
- **volumes**: Volumes manager (volume/chapter grouping, manipulation)

All services are **lazily loaded** as properties of the context to optimize performance and resource use.

For command-line tools, FastAPI server endpoints, and crawlers, you should always access shared services via `ctx` for consistency and compatibility.

## Creating a New Source Crawler

**Full guide:** [.github/docs/CREATING_CRAWLERS.md](.github/docs/CREATING_CRAWLERS.md)

**Recommended:** Copy **`sources/_examples/_01_general_soup.py`** and use **`GeneralSoupTemplate`** (`lncrawl.templates.soup.general`). Implement:

- **Required:** `parse_title(soup)`, `parse_cover(soup)`, `parse_chapter_list(soup)` (yield `Chapter`/`Volume`), `select_chapter_body(soup)` (return the chapter text Tag).
- **Optional:** `parse_authors(soup)`, `parse_summary(soup)`, `get_novel_soup()`, `initialize()`, `login()`.

For search use `_02_searchable_soup.py` (SearchableSoupTemplate)

For volumes use `_05_with_volume_soup.py` or `_07_optional_volume_soup.py`

For JS-heavy sites use browser examples (`_09`–`_17`).

Alternative: base **`Crawler`** with `read_novel_info()` and `download_chapter_body()` via `_00_basic.py`.

Test: `uv run python -m lncrawl -s "URL" --first 3 -f` and `uv run python -m lncrawl sources list | grep mysite`.
