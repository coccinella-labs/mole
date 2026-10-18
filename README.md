<p align="center">
  <img src="https://raw.githubusercontent.com/coccinella-labs/mole/main/.github/assets/thumbnail.png" alt="molplatform" width="100%">
</p>

# Mole

A containerized microservice for molecular generation and analysis. Generates molecular variants through random mutations using RDKit. Features a REST API, web interface, and CLI tool with secure API key authentication.

---

## Prerequisites

* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/)

## Components

`docker-compose up` starts three services, not one:

| Service | Role | Exposed port |
|---|---|---|
| `backend` | FastAPI service, serves `/docs` and `/generate_molecule` | 8000 |
| `frontend` | web interface | 3000 |
| `nginx` | reverse proxy over `backend` and `frontend` | 80 |

`node_modules` is a named volume, not a service.

Generation is handled inline in the request: `/generate_molecule` calls
`MoleculeGenerator` directly, synchronously.

The stack previously carried Postgres, Redis and a Celery worker. None were on
the request path, and no module under `backend/src` read `DATABASE_URL` or the
Celery settings. `src/tasks.py` held a second copy of the mutation code that
predated the fixes in [#94](https://github.com/coccinella-labs/mole/pull/94), and the worker never imported it, so it registered
only Celery built-ins. Running that copy directly produced results RDKit could
not parse in 156 of 300 runs, and silently returned the input unchanged in 29.
Registering those tasks would have exposed a second, less reliable mutation
path, so the stack was removed rather than wired up. See issue [#101](https://github.com/coccinella-labs/mole/issues/101).

---

## Frontend Build

The web interface is built with Vite and Tailwind CSS 4, not Create React App.
CRA hardcoded Tailwind into its PostCSS pipeline and disabled project-level
PostCSS config, so Tailwind 4 could not be adopted without replacing the build
tooling. The migration is [#110](https://github.com/coccinella-labs/mole/pull/110);
the blocker it removed is recorded in [#93](https://github.com/coccinella-labs/mole/issues/93).

The production image serves the static `dist` output from nginx. For local
frontend work:

```bash
cd frontend
npm ci
npm run dev     # Vite dev server on http://localhost:3000
npm run build   # production build into dist/
```

The container build remains the reference: it runs `npm ci` followed by
`vite build`, and serves `dist`. Frontend environment variables use the `VITE_`
prefix (`VITE_BACKEND_URL`, `VITE_API_KEY`), set as build arguments in
`docker-compose.yml`.

## Execution

To initiate the platform:

```bash
docker-compose up --build
```

## Command Line Testing

For testing without the web interface, use the CLI. The quickest route is the
prebuilt binary attached to each tagged release, which needs no Python at all:

```bash
# Linux
curl -LO https://github.com/coccinella-labs/mole/releases/download/v1.0.0/mol-platform
chmod +x mol-platform
```

That is the current `v1.0.0` asset, which predates the per-target naming, so it
is a Linux build with no macOS or Windows equivalent. See `docs/cicd.md`.

Asset names change at `v1.1.0`. That release will publish `mole-linux`,
`mole-macos` and `mole-windows.exe`. Existing assets are not renamed or moved, so
links pinned to an existing tag keep their current names, and
`releases/latest/download/mole-*` does not resolve until `v1.1.0` exists.

To build and install it from source instead:

```bash
cd backend
python3 -m venv venv && source venv/bin/activate && pip install build && python -m build
pipx install dist/mol_platform-1.0.0-py3-none-any.whl

# Test health
mol-platform --api-key your-key --health

# Generate molecule
mol-platform --api-key your-key --generate "CC(=O)OC1=CC=CC=C1C(=O)O"
```

## Access Points

- **API Documentation:** http://localhost:8000/docs
- **Frontend Interface:** http://localhost (through nginx) or http://localhost:3000 (frontend container directly)

The API key is required on both `/health` and `/generate_molecule`. `GET /health`
returns `401` without it.

---

## API Reference

### Molecule Generation

**Endpoint:** `POST /generate_molecule`

Facilitates the creation of molecular variants through random mutations.

**Request Structure**

```json
{
  "base_smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
  "num_mutations": 3,
  "mutation_types": ["substituent", "bond_order", "atom_swap"]
}
```

**Parameters:**
- `base_smiles`: SMILES representation (required)
- `num_mutations`: Mutation count (optional, default: 3, maximum: 10)
- `mutation_types`: Permitted mutation categories (optional)

`num_mutations` outside the range 0 to 10 is rejected with `400`. The upper
bound is a request-level limit, not a preference: each mutation searches up to
32 candidate positions, so the work a single request performs grows with the
count, and the endpoint is declared `async`, so that work blocks the event loop
for its duration. The maximum of 10 matches the ceiling the frontend already
enforces on this input.

**Response Structure:**
```json
{
  "original_smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
  "generated_smiles": "CC(=O)Oc1cSCN)cccc1C(=O)O",
  "molecular_image": "base64_encoded_png",
  "properties": {
    "Molecular Weight": 180.16,
    "LogP": 1.31,
    "H-Bond Donors": 1,
    "H-Bond Acceptors": 3,
    "Topological Polar Surface Area": 63.6
  },
  "requested_mutations": 3,
  "successful_mutations": 3,
  "failed_mutations": 0,
  "mutated": true
}
```

**Mutation Counters:**

`requested_mutations`, `successful_mutations` and `failed_mutations` count
logical mutations, not candidate attempts. One requested mutation examines
several candidate positions and accepts the first that both passes RDKit
sanitisation and makes the structural change that mutation type promises, so
`successful_mutations + failed_mutations == requested_mutations` always holds
for a completed request.

A mutation counts as successful only if it really changed the structure. A
candidate that sanitises but leaves the molecule unchanged does **not** count
as successful, because RDKit re-perceives aromaticity during sanitisation and
can silently undo a bond order edit inside an aromatic ring. Such a candidate
is counted in `failed_mutations` instead.

`mutated` is `true` when at least one mutation changed the structure; when it is
`false`, no mutation was applied and the returned molecule has the same
structure as the input. `generated_smiles` is canonicalised, so its string
representation may differ from `original_smiles` even in that case. The
response still returns `200` in every completed case: the counters, not the
status code, distinguish real work from a no-op.

**Available Mutations:**
- `substituent`: Introduces substituent groups
- `bond_order`: Adjusts bonding configurations
- `atom_swap`: Exchanges atomic elements

### Health Verification

**Endpoint:** `GET /health`

Provides service status confirmation.

**Response Structure:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```
