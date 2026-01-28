# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
# Setup virtual environment (creates .venv-posix on Linux/Mac, .venv-win on Windows)
make setup

# Install Python and web dependencies
make install       # Both Python and web
make install-py    # Python only
make install-web   # Web frontend only

# Run development servers
make start         # Both backend (with watch) and frontend
make start-server  # Backend server only
make watch-server  # Backend with auto-reload
make start-web     # Frontend dev server (Vite)

# Build
make build         # Full build (web + wheel + exe)
make build-web     # Frontend build only
make build-wheel   # Python wheel only
make build-exe     # PyInstaller executable

# Linting
make lint          # Both Python and web
make lint-py       # Python (flake8)
make lint-web      # Web frontend (eslint)

# Run from source directly
python lncrawl     # Or: python -m lncrawl
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

Key services available on `ctx`: `config`, `db`, `http`, `sources`, `crawler`, `binder`, `jobs`, `novels`, `chapters`, `volumes`

### Web Frontend

**Location**: `lncrawl-web/`
- React 19 with TypeScript, Vite, Ant Design
- Redux Toolkit for state management
- SCSS for styling

## Creating a New Source Crawler

1. Create file in appropriate `sources/{lang}/` directory
2. Extend `Crawler` class from `lncrawl.core.crawler`
3. Set `base_url` class attribute (list of URL patterns)
4. Implement `read_novel_info()` to populate `self.novel` with title, cover, volumes, chapters
5. Implement `download_chapter_body(chapter)` returning HTML content
6. Optional: `search_novel(query)` returning list of `SearchResult`

## Code Style

- Python: flake8 with max-line-length 150, black formatting with line-length 120
- Web: ESLint with TypeScript rules
