# Architecture Overview

This document describes the architecture of the Lightnovel Crawler project.

## Entry Point & Application Context

- **`lncrawl/__main__.py`**: Entry point, calls `main()` from `lncrawl.app`
- **`lncrawl/context.py`**: `AppContext` singleton manages all services via lazy-loaded properties
- **`lncrawl/app.py`**: CLI setup using Typer, registers subcommands (crawl, search, server, sources, config)

## Source Crawlers

**Location**: `sources/` - Organized by language (`en/`, `zh/`, `ja/`, etc.), English further split alphabetically

### Key Base Classes

| Class | Location | Purpose |
|-------|----------|---------|
| `Crawler` | `lncrawl/core/crawler.py` | Base class for source crawlers |
| `Scraper` | `lncrawl/core/scraper.py` | HTTP requests, BeautifulSoup parsing, Cloudflare handling |
| `TaskManager` | `lncrawl/core/taskman.py` | ThreadPoolExecutor for concurrent operations |

### Crawler Registration

Located in `lncrawl/services/sources/service.py`:
- Crawlers are auto-discovered by importing Python files from source directories
- Each crawler has: `__id__`, `base_url`, `version` metadata
- Full-text search index for fast source lookup

## Server/API

**FastAPI Server**: `lncrawl/server/app.py`

- REST API at `/api`, frontend at `/`
- Endpoints organized in `lncrawl/server/api/`:
  - `novels` - Novel metadata and management
  - `chapters` - Chapter content
  - `volumes` - Volume organization
  - `jobs` - Background job management
  - `artifacts` - Generated files (EPUB, etc.)
  - `auth` - Authentication
  - `libraries` - User libraries

## Output Generation

### Binder Service

Located in `lncrawl/services/binder/`:

| Module | Purpose |
|--------|---------|
| `epub.py` | Native EPUB generation (primary format) |
| `calibre.py` | Converts EPUB to other formats (MOBI, PDF, DOCX, etc.) via Calibre |
| `json.py` | JSON format output |
| `text.py` | Plain text format output |

## Data Models

Located in `lncrawl/models/`:
- `Chapter` - Chapter content and metadata
- `Volume` - Volume grouping
- `Novel` - Novel metadata (title, author, cover, etc.)
- `SearchResult` - Search result representation
- `Session` - User session data

## Database Access

Located in `lncrawl/dao/`:
- Uses SQLAlchemy/SQLModel for ORM
- Database access objects for persistent storage

## Services (via AppContext)

Key services available on `ctx`:

| Service | Purpose |
|---------|---------|
| `config` | Application configuration |
| `db` | Database connection |
| `http` | HTTP client |
| `sources` | Source crawler registry |
| `crawler` | Active crawler instance |
| `binder` | Output format generation |
| `jobs` | Background job management |
| `novels` | Novel data access |
| `chapters` | Chapter data access |
| `volumes` | Volume data access |

## Web Frontend

**Location**: `lncrawl-web/`

### Technology Stack

- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **UI Library**: Ant Design
- **State Management**: Redux Toolkit
- **Styling**: SCSS

### Structure

```
lncrawl-web/
├── src/
│   ├── components/    # Reusable UI components
│   ├── pages/         # Page components
│   ├── store/         # Redux store and slices
│   ├── services/      # API client services
│   └── utils/         # Utility functions
├── public/            # Static assets
└── index.html         # Entry point
```

## Directory Structure

```
lightnovel-crawler/
├── lncrawl/                 # Main Python package
│   ├── core/                # Core classes (Crawler, Scraper, etc.)
│   ├── models/              # Data models
│   ├── dao/                 # Database access objects
│   ├── services/            # Business logic services
│   ├── server/              # FastAPI server
│   │   ├── api/             # API endpoints
│   │   └── web/             # Built frontend (generated)
│   └── VERSION              # Version file
├── sources/                 # Source crawler implementations
│   ├── en/                  # English sources (split by first letter)
│   ├── zh/                  # Chinese sources
│   ├── ja/                  # Japanese sources
│   └── ...                  # Other languages
├── lncrawl-web/             # React frontend source
├── scripts/                 # Build and deployment scripts
├── docs/                    # Documentation
└── Makefile                 # Build system
```
