# Required variables
ifeq ($(OS),Windows_NT)
	PYTHON := python
	VENV := .venv-win
	PY := $(VENV)/Scripts/python
	FLAKE8 := $(VENV)/Scripts/flake8
	YARN := yarn --cwd lncrawl-web
else
	PYTHON := python3
	VENV := .venv-posix
	PY := $(VENV)/bin/python
	FLAKE8 := $(VENV)/bin/flake8
	# Use NVM if available, otherwise fall back to system yarn
	ifneq ($(wildcard $(NVM_DIR)/nvm-exec),)
		YARN := "$(NVM_DIR)/nvm-exec" yarn --cwd lncrawl-web
	else
		YARN := yarn --cwd lncrawl-web
	endif
endif

VERSION := $(shell $(PYTHON) -c "print(open('lncrawl/VERSION').read().strip())")

# Phony targets
.PHONY: help version clean setup install install-py install-web \
        build build-web build-wheel build-exe \
        start start-server watch-server start-web \
        lint lint-py lint-web \
        docker-build docker-up docker-down docker-logs \
        pull push-tag remove-tag push-tag-force

# Default target
_: help

help:
	@echo "Lightnovel Crawler Build System"
	@echo ""
	@echo "Setup & Install:"
	@echo "  make setup        Create virtual environment"
	@echo "  make install      Install all dependencies (Python + Web)"
	@echo "  make install-py   Install Python dependencies only"
	@echo "  make install-web  Install web dependencies only"
	@echo ""
	@echo "Development:"
	@echo "  make start        Start both backend and frontend servers"
	@echo "  make start-server Start backend server only"
	@echo "  make start-web    Start frontend dev server only"
	@echo "  make lint         Run all linters"
	@echo ""
	@echo "Build:"
	@echo "  make build        Full build (web + wheel + exe)"
	@echo "  make build-web    Build frontend only"
	@echo "  make build-wheel  Build Python wheel only"
	@echo "  make build-exe    Build PyInstaller executable"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build Build Docker image"
	@echo "  make docker-up    Start containers with docker compose"
	@echo "  make docker-down  Stop containers"
	@echo "  make docker-logs  View container logs"
	@echo ""
	@echo "Other:"
	@echo "  make version      Show current version"
	@echo "  make clean        Remove build artifacts and venvs"

version:
	@echo Current version: $(VERSION)

# Clean target
clean:
ifeq ($(OS),Windows_NT)
	@powershell -Command "try { Remove-Item -ErrorAction SilentlyContinue -Recurse -Force $(VENV), logs, build, dist } catch {}; exit 0"
	@powershell -Command "Get-ChildItem -ErrorAction SilentlyContinue -Recurse -Directory -Filter '*.egg-info' | Remove-Item -Recurse -Force"
	@powershell -Command "Get-ChildItem -ErrorAction SilentlyContinue -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force"
	@powershell -Command "Get-ChildItem -ErrorAction SilentlyContinue -Recurse -Directory -Filter 'node_modules' | Remove-Item -Recurse -Force"
else
	@rm -rf $(VENV) logs build dist
	@find . -name '*.egg-info' -type d -exec rm -rf '{}'
	@find . -name '__pycache__' -type d -exec rm -rf '{}'
	@find . -name 'node_modules' -type d -exec rm -rf '{}'
endif


# Setup virtual environment in .venv
setup:
ifeq ($(wildcard $(VENV)/pyvenv.cfg),)
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install -q -U pip
else
	$(info $(VENV) already exists.)
endif

# Install dependencies in .venv
install-py: setup
	$(PY) -m pip install -r requirements.txt

# Install node modules in lncrawl-web
install-web:
	$(YARN) install

install: install-py install-web

# Build wheel package and executable
build-web:
	$(YARN) build

build-wheel:
	$(PY) -m build -w

build-exe:
	$(PY) setup_pyi.py

build: version install build-web build-wheel build-exe

# Lint project files
start-server:
	$(PY) -m lncrawl -ll server

watch-server:
	$(PY) -m lncrawl -ll server --watch

start-web:
	$(YARN) dev

start:
	+$(MAKE) -j2 watch-server start-web

# Lint project files
lint-py:
	$(FLAKE8) --config .flake8 -v --count --show-source --statistics

lint-web:
	$(YARN) lint

lint: lint-py lint-web

# Push tag
pull:
	git pull --rebase --autostash

remove-tag:
	git push --delete origin "v$(VERSION)"
	git tag -d "v$(VERSION)"

push-tag: pull
	git tag "v$(VERSION)"
	git push --tags

push-tag-force: pull
	git push --delete origin "v$(VERSION)"
	git tag -d "v$(VERSION)"
	git tag "v$(VERSION)"
	git push --tags

# Docker targets
docker-build:
	docker build -t lncrawl .

docker-up:
	docker compose -f scripts/local-compose.yml up -d

docker-down:
	docker compose -f scripts/local-compose.yml down

docker-logs:
	docker compose -f scripts/local-compose.yml logs -f
