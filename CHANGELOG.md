# Changelog

All notable changes to Mole will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/specification/v1.0).

## [Unreleased]

Work merged after `v1.0.0` and not yet cut into a release. The version number is
not chosen: `backend/pyproject.toml` is the single source of truth for the
backend version, so `main.py` no longer needs editing when a release is cut.

### Added

- Bounds enforcement on `num_mutations` across all three callers: the API
  returns `400` outside `0..10`, the CLI rejects out-of-range input, and the
  frontend validates before sending.
- `MAX_MUTATIONS_PER_REQUEST = 10` in `backend/src/main.py`, answering a larger
  request with `400` rather than performing unbounded work.
- Accessible labels for the two form inputs. Both had a sibling `<label>` with
  no `htmlFor` and no `id` on the input, so neither had a programmatic accessible
  name.
- A Coccinella Labs favicon, previously `/favicon.png` returned `404`.
- Cypress coverage for the frontend: accessibility, mutation input, image
  layout, result-grid layout, and unchanged-behaviour regression specs.
- A merge-queue ruleset for the default branch, with conversation resolution
  required before merge.

### Fixed

- Validation errors are reported readably. FastAPI answers a schema violation
  with `422` and a list of error objects; the client only understood a string
  `detail`, so the real reason was replaced by the bare status code.
- Empty and malformed mutation input no longer reaches the API. The field held a
  number, so clearing it produced `NaN`, which serialised to `null` and was
  rejected with `422`.
- The mutations input `min` was `1` while the API accepts `0` and answers with
  `mutated=false`.
- Long SMILES values no longer overlap in the result panel. A two-column grid
  whose items had no `min-w-0` let unbroken SMILES tokens paint outside their
  track and collide with the neighbouring column.
- Failed mutations are reported instead of being silently discarded.
- API failures state their cause rather than one generic message.
- RDKit warnings are muted only during candidate validation, where they are
  expected.
- `CI` emits a valid sha tag on `pull_request` events.

### Changed

- **Frontend build moved from Create React App to Vite 8 with Tailwind CSS 4.**
  CRA hardcoded `tailwindcss` into its PostCSS pipeline and disabled
  project-level PostCSS config, so Tailwind 4 could not be adopted without
  replacing the build tooling. This resolves #93 and supersedes the dependabot
  bump in #91.
- Frontend entry points moved to `.jsx`, since Vite does not transform JSX in
  `.js` files.
- Frontend environment variables use the `VITE_` prefix (`VITE_BACKEND_URL`,
  `VITE_API_KEY`), set as build arguments in `docker-compose.yml`.
- The production frontend image runs `vite build` and serves `dist`.
- The service version is resolved from `pyproject.toml`, preferring installed
  distribution metadata. Previously `main.py` hardcoded its own copy, so
  `GET /health` could report a version that differed from the packaged one.
- The product was renamed to Mole and repository URLs updated.
- Release artifacts are named per target at `v1.1.0`; assets up to and
  including `v1.0.0` keep their existing names.
- e2e tests run on pull requests and in the merge queue, on Node 22.

### Removed

- **PostgreSQL, Redis and the Celery worker.** None were on the request path,
  and no module under `backend/src` read `DATABASE_URL` or the Celery settings.
  `src/tasks.py` held a second copy of the mutation code that predated the
  failure-reporting fixes, and the worker never imported it, so it registered
  only Celery built-ins.
- `react-router-dom`, which was unused.
- The CI step that ran `react-scripts test`; there are no JavaScript unit tests.
  Cypress is the frontend suite.
- `python-jose`, along with refreshed vulnerable transitive dependencies.

### Security

- `qs`, reached only through `@cypress/request` in the test runner, resolved to
  6.16.1, above the patched line for CVE-2026-8723. Dependabot alert #69.

### Known issues

- **The API key is embedded in the client bundle.** `VITE_API_KEY` is inlined
  at build time, so anyone loading the page can read it. Unresolved and tracked
  separately.

## [1.0.0] - 2025-12-28

### Released
- Official 1.0.0 release with all improvements

### Added
- Initial release of Mole: containerized microservice for molecular simulation
- Molecule generation with random mutations (substituents, bond orders, atom swaps)
- REST API with FastAPI backend
- React frontend with visualization
- Docker Compose setup with PostgreSQL, Redis, Celery
- Comprehensive testing (unit + e2e)
- Ruff linting and pre-commit hooks
- Input validation and error handling
- LRU caching for performance
- Environment configuration with .env.example
- Complete documentation
- CLI packaged as standalone binary with `mol-platform` command
- API key authentication for all endpoints
- Documentation for API authentication setup
- Workflow updates to use API_KEY secret

### Fixed
- Corrected SMILES string manipulation with proper RDKit molecular editing
- Added sanitization to prevent invalid molecules
- Replaced numpy random with built-in random for simplicity
- Fixed Docker dependencies and PYTHONPATH
- Resolved npm vulnerabilities
- Improved API health endpoint with version info
- Added comprehensive input validation

### Changed
- Stabilized Python version to 3.12 across all environments
- Updated dependencies for compatibility
- Enhanced error messages and logging

### Technical Improvements
- Type-safe random selections
- Modular mutation strategies
- Clean code with linting
- CI/CD pipeline with automated testing
- Production-ready containerization
