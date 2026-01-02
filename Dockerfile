ARG BASE_IMAGE=ghcr.io/dipu-bd/lncrawl-base:latest

##
# Web assets
##
FROM node:20-alpine AS web

WORKDIR /app/lncrawl-web

COPY lncrawl-web/package.json lncrawl-web/yarn.lock ./
RUN yarn install --frozen-lockfile

COPY lncrawl-web .
RUN yarn build

##
# Application
##
ARG BASE_IMAGE=ghcr.io/dipu-bd/lncrawl-base:latest
FROM ${BASE_IMAGE} AS app

WORKDIR /app

# Install requirements
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-cache -r requirements.txt

# Copy files
COPY sources ./sources
COPY lncrawl ./lncrawl
COPY --from=web /app/lncrawl/server/web ./lncrawl/server/web

# Custom data path
ENV LNCRAWL_DATA_PATH=/data

ENTRYPOINT ["python", "-m", "lncrawl"]
