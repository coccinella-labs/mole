# CI/CD

Continuous Integration and Deployment pipeline for Mole.

## GitHub Actions Workflows

### CI Workflow (.github/workflows/ci.yml)

Runs on pushes and PRs to main:

1. **Setup Environment**
   - Python 3.12, 3.13 and 3.14, as a matrix, so every backend step runs three times
   - Node.js 22, matching `frontend/Dockerfile` and `e2e.yml`. Cypress 16 requires Node 22 or newer.

2. **Backend Testing**
   - Install dependencies from `backend/requirements.txt`
   - Run unit tests, `tests/test_molecule_generation.py`
   - Run e2e tests, `tests/e2e/`

3. **Frontend Testing**
   - Install dependencies with `npm ci`
   - Run `react-scripts test --watchAll=false --passWithNoTests`

   There is no separate lint step in any workflow. Create React App runs ESLint
   as part of `react-scripts build`, which happens in `docker.yml`, not here.
   Because `docker build` does not inherit the runner environment, `CI` is not
   set inside that build, so ESLint warnings do not fail the build.

4. **Build Check**
   - `docker-compose build`

### Docker Workflow (.github/workflows/docker.yml)

Builds and pushes Docker images to GitHub Container Registry:

- Triggered on pushes and PRs
- Builds backend and frontend images
- Pushes to `ghcr.io`

### Docs Workflow (.github/workflows/docs.yml)

Builds the documentation site and publishes it to GitHub Pages.

- Triggered on pushes and pull requests
- Concurrency group `pages`, with `cancel-in-progress: false`, so a queued
  publish is never cancelled halfway

### Release Workflow (.github/workflows/release.yml)

Triggered by a tag matching `v*`. Builds a single-file CLI binary and attaches
it to a GitHub release.

- `pip install pyinstaller`, then
  `pyinstaller --onefile src/cli.py --name mole-${{ matrix.target }}`
- Runs on a per-OS matrix. Assets are named per target, so they do not collide:

  | Runner | Asset |
  |---|---|
  | `ubuntu-latest` | `mole-linux` |
  | `macos-latest` | `mole-macos` |
  | `windows-latest` | `mole-windows.exe` |

- Attached via `softprops/action-gh-release`, with generated release notes

This is the fastest way to get the CLI, since it skips building a wheel and
needs no Python environment:

```
curl -LO https://github.com/coccinella-labs/mole/releases/download/v1.0.0/mol-platform
chmod +x mol-platform
./mol-platform --api-key your-key --health
```

`v1.0.0` is the only release so far. It publishes a single un-suffixed
`mol-platform`, plus `mol-platform.exe`, and the surviving binary is a Linux
build. From `v1.1.0` the per-target names `mole-linux`, `mole-macos` and
`mole-windows.exe` apply instead.

**Note on `v1.0.0`.** That release predates both the per-target rename and the
product rename. Because both the Linux and macOS jobs uploaded a file called
`mol-platform`, they overwrote each other and the surviving asset is the Linux
build. Verified: downloading it on macOS gives `exec format error`. There is
currently no macOS binary for `v1.0.0`.

**Asset names change at `v1.1.0`.** Assets up to and including `v1.0.0` are
named `mol-platform` and `mol-platform.exe`; assets from `v1.1.0` onwards are
named `mole-<target>`. Existing assets are not renamed or moved, so a link
pinned to an older tag must keep the old name, and
`releases/latest/download/mole-*` does not resolve until `v1.1.0` is published.

### E2E Workflow (.github/workflows/e2e.yml)

Full end-to-end testing:

- Builds Docker containers
- Starts services
- Runs Cypress e2e tests
- Manual trigger available

## Pre-commit Hooks

Local quality checks using pre-commit:

- Ruff linting and formatting
- Commit message validation

Install:
```bash
pip install pre-commit
pre-commit install
```

## Quality Gates

### Code Quality
- **Linting:** Ruff (Python)
- **Formatting:** Ruff format
- **Type checking:** Basic validation

### Testing
- **Unit tests:** pytest
- **E2E tests:** Cypress
- **Coverage:** Not enforced but monitored

### Security
- **Dependencies:** Automated scanning
- **Vulnerabilities:** npm audit, pip security

## Deployment

### Manual Deployment

```bash
# Build images
docker-compose build

# Deploy
docker-compose up -d
```

### Automated Deployment

Configure your platform (Heroku, AWS, etc.) to:
1. Pull images from GitHub Container Registry
2. Use docker-compose.yml for orchestration
3. Set environment variables from secrets

## Monitoring

- Health check endpoint: `GET /health`
- Application logs in Docker
- GitHub Actions run history
