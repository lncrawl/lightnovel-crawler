# Setting Up CI on Forks

This guide explains how to configure GitHub Actions workflows when working with a fork of lightnovel-crawler.

## Workflows That Work on Forks (No Setup Required)

The following workflows will run automatically on your fork for pull requests and pushes:

| Workflow | File | Description |
|----------|------|-------------|
| Lint & Test (Python) | `lint-py.yml` | Runs flake8, builds wheel, tests installation |
| Lint & Test (Web) | `lint-web.yml` | Runs eslint, builds frontend |

These workflows require no additional setup and will run with the default `GITHUB_TOKEN`.

## Workflows That Require Secrets

The following workflows require secrets and won't work on forks without additional setup:

| Workflow | File | Required Secrets |
|----------|------|------------------|
| Build and Publish | `release.yml` | `PYPI_API_TOKEN`, `SHLINK_API_KEY` |
| Server Deployment | `deploy.yml` | `SSH_SECRET`, `SSH_HOST`, `DEPLOY_SERVER` |

### Setting Up Release Workflow

If you want to publish releases from your fork:

1. Go to your fork's **Settings** > **Secrets and variables** > **Actions**
2. Add the following secrets:
   - `PYPI_API_TOKEN`: Your PyPI API token (for publishing to PyPI)
   - `SHLINK_API_KEY`: Optional, for updating short links

Note: Release builds will automatically push Docker images to GHCR using your fork's namespace.

### Setting Up Deploy Workflow

The deploy workflow is designed for the main project's infrastructure. For your own deployment:

1. Modify `scripts/server-compose.yml` with your configuration
2. Add your deployment secrets:
   - `SSH_SECRET`: Private SSH key for deployment server
   - `SSH_HOST`: Hostname of your deployment server
   - `DEPLOY_SERVER`: SSH connection string (e.g., `user@host`)

## Docker Image Publishing

Docker workflows automatically use your fork's namespace:

- Base image: `ghcr.io/<your-username>/lncrawl-base`
- App image: `ghcr.io/<your-username>/lightnovel-crawler`

The workflows automatically lowercase usernames to ensure compatibility with Docker registries.
y
### Building Your Own Base Image

If you need to customize the base image:

1. Modify `Dockerfile.base` as needed
2. Push to trigger the `docker-base.yml` workflow, or run manually:
   ```bash
   docker build -f Dockerfile.base -t ghcr.io/<your-username>/lncrawl-base .
   docker push ghcr.io/<your-username>/lncrawl-base
   ```

3. Update `Dockerfile` to use your base image:
   ```bash
   docker build --build-arg BASE_IMAGE=ghcr.io/<your-username>/lncrawl-base -t lncrawl .
   ```

## Common Issues

### Workflow Won't Run

1. Ensure GitHub Actions is enabled in your fork's Settings
2. Check that the workflow file hasn't been modified to break triggers
3. Verify that the paths filter matches your changes (for path-filtered workflows)

### Permission Denied for GHCR

1. Go to your GitHub account's **Settings** > **Developer settings** > **Personal access tokens**
2. Ensure your token has `write:packages` scope, or
3. Use the default `GITHUB_TOKEN` which should have packages permission by default for forks

### Build Fails on ARM64

ARM64 builds use QEMU emulation and may take longer. If builds timeout:
1. The base image must be built for ARM64 first
2. Calibre installation on ARM64 may have different dependencies

## Questions?

If you encounter issues setting up CI on your fork, please open a discussion in the main repository.
