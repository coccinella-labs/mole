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
   - There is no frontend unit-test step. The repository has no JavaScript unit
     tests; `frontend/cypress/e2e/` is the frontend test suite and runs in the
     separate `e2e` workflow described below.

   There is no separate lint step in any workflow. The `pre-commit` hook runs
   across the repository and is what enforces formatting.

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
curl -LO https://github.com/coccinella-labs/mole/releases/download/v1.1.0/mole-linux
chmod +x mole-linux
./mole-linux --api-key your-key --health
```

**Asset names are per-target.** Every release from `v1.1.0` onwards publishes
`mole-linux`, `mole-macos` and `mole-windows.exe`. Earlier releases used
different names, and those assets keep them: a URL pinned to any tag keeps
resolving to the file that tag actually published.
`releases/latest/download/mole-*` resolves to the newest release, so it
changes target whenever a new release lands; pin the tag for a build that does
not move.

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
