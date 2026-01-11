# Contributing to Lightnovel Crawler

Thank you for your interest in contributing! This guide will help you get started.

## Development Environment Setup

### Prerequisites

- **Python 3.8+** (3.10 recommended for Docker parity)
- **Node.js 20+** (for frontend development)
- **Calibre** (optional, required for non-EPUB output formats)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/lncrawl/lightnovel-crawler.git
cd lightnovel-crawler

# Setup and install dependencies
make setup
make install

# Start development servers (backend + frontend)
make start
```

### Available Commands

Run `make help` to see all available commands:

| Command | Description |
|---------|-------------|
| `make setup` | Create virtual environment |
| `make install` | Install all dependencies (Python + Web) |
| `make install-py` | Install Python dependencies only |
| `make install-web` | Install web dependencies only |
| `make start` | Start both backend and frontend servers |
| `make start-server` | Start backend server only |
| `make start-web` | Start frontend dev server only |
| `make lint` | Run all linters |
| `make lint-py` | Run Python linter (flake8) |
| `make lint-web` | Run web linter (eslint) |
| `make build` | Build everything (web + wheel + exe) |
| `make docker-build` | Build Docker image locally |

### Platform-Specific Notes

**Windows:**
- Uses `.venv-win` for virtual environment
- Run commands in PowerShell or Command Prompt

**Linux/macOS:**
- Uses `.venv-posix` for virtual environment
- If you have Node.js installed via NVM, it will be used automatically
- If you have Node.js installed via apt/brew/asdf, it works too

## Making Changes

### Code Style

- **Python**: flake8 with max-line-length 150, black formatting with line-length 120
- **Web**: ESLint with TypeScript rules

Always run `make lint` before committing to ensure your code passes all checks.

### Adding a Source Crawler

See [docs/CREATING_CRAWLERS.md](docs/CREATING_CRAWLERS.md) for detailed instructions on how to add support for new novel sources.

Quick overview:
1. Create a file in `sources/{lang}/` (e.g., `sources/en/m/mysite.py`)
2. Extend the `Crawler` class from `lncrawl.core.crawler`
3. Implement required methods: `read_novel_info()` and `download_chapter_body()`
4. Test your crawler locally

### Architecture Overview

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for a detailed overview of the codebase structure.

## Submitting Changes

### Pull Request Process

1. **Fork the repository** and create a feature branch from `dev`
2. **Make your changes** and ensure they pass linting: `make lint`
3. **Test your changes** locally
4. **Submit a PR** against the `dev` branch

### Commit Messages

Use clear, descriptive commit messages:
- `Add support for newsite.com` (new source)
- `Fix chapter parsing in novelsite.com` (bug fix)
- `Update dependencies` (maintenance)

### Code Review

All PRs require review before merging. Please be patient and responsive to feedback.

## Setting Up CI on Forks

If you want CI to run on your fork, see [.github/FORKING.md](.github/FORKING.md) for instructions.

## Getting Help

- **Bug reports**: Open an issue using the bug report template
- **New source requests**: Open an issue using the new source template
- **Questions**: Open a discussion or check existing issues

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
