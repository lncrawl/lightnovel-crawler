.PHONY: all version clean setup install upgrade add-dep add-dev rm-dep rm-dev build-wheel build-exe build add-source start watch lint pull remove-tag push-tag push-tag-force docker-build docker-up docker-down docker-logs
all: version install

VERSION := $(shell python -c "print(open('lncrawl/VERSION').read().strip())")

# Use uv from PATH, or from default install location after make setup
ifeq ($(OS),Windows_NT)
UV := $(shell powershell -NoProfile -Command "if (Get-Command uv -ErrorAction SilentlyContinue) { (Get-Command uv).Source } else { Join-Path $env:USERPROFILE '.local\bin\uv.exe' }")
else
UV := $(shell command -v uv 2>/dev/null || echo "$(HOME)/.local/bin/uv")
endif

version:
	@echo Lightnovel Crawler: $(VERSION)

clean:
ifeq ($(OS),Windows_NT)
	@powershell -Command "try { Remove-Item -ErrorAction SilentlyContinue -Recurse -Force .venv, logs, build, dist } catch {}; exit 0"
	@powershell -Command "Get-ChildItem -ErrorAction SilentlyContinue -Recurse -Directory -Filter '*.egg-info' | Remove-Item -Recurse -Force"
	@powershell -Command "Get-ChildItem -ErrorAction SilentlyContinue -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force"
else
	@rm -rf .venv logs build dist
	@find . -depth -name '*.egg-info' -type d -exec rm -rf '{}' \; 2>/dev/null || true
	@find . -depth -name '__pycache__' -type d -exec rm -rf '{}' \; 2>/dev/null || true
endif

setup:
	@git submodule sync
	@git submodule update --force --init --recursive --remote
ifeq ($(OS),Windows_NT)
	@$(UV) --version || powershell -NoProfile -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
else
	@$(UV) --version || (curl -LsSf https://astral.sh/uv/install.sh | sh)
endif

install: setup
	$(UV) sync --extra dev

upgrade: setup
	$(UV) sync --upgrade --extra dev

lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .

start:
	$(UV) run python -m lncrawl -ll server

watch:
	$(UV) run python -m lncrawl -ll server --watch

add-source:
	$(UV) run python -m lncrawl -ll lncrawl sources create

build-wheel:
	$(UV) run python -m build -w

build-exe:
	$(UV) run python setup_pyi.py

build: version install build-wheel build-exe

add-dep: setup
	$(UV) add $(word 2,$(MAKECMDGOALS))
	$(UV) sync --extra dev

add-dev: setup
	$(UV) add --optional dev $(word 2,$(MAKECMDGOALS))
	$(UV) sync --extra dev

rm-dep: setup
	$(UV) remove $(word 2,$(MAKECMDGOALS))
	$(UV) sync --extra dev

rm-dev: setup
	$(UV) remove --optional dev $(word 2,$(MAKECMDGOALS))
	$(UV) sync --extra dev

pull:
	git pull --rebase --autostash
	git submodule update --remote --merge

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

docker-base:
	docker build -t lncrawl-base -f Dockerfile.base .

docker-build: docker-base
	docker build -t lncrawl --build-arg BASE_IMAGE=lncrawl-base .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f
