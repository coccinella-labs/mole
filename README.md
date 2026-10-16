<p align="center">
  <img src="https://raw.githubusercontent.com/Coccinella-Labs/molplatform/main/.github/assets/thumbnail.png" alt="molplatform" width="100%">
</p>

# molplatform

A containerized microservice for molecular generation and analysis. Generates molecular variants through systematic mutations using RDKit. Features a REST API, web interface, and CLI tool with secure API key authentication.

---

## Prerequisites

* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/)

## Components

`docker-compose up` starts six services, not one:

| Service | Role | Exposed port |
|---|---|---|
| `backend` | FastAPI service, serves `/docs` and `/generate_molecule` | 8000 |
| `frontend` | web interface | 3000 |
| `nginx` | reverse proxy over `backend` and `frontend` | 80 |
| `database` | Postgres 15, image `postgres:15-alpine` | none, internal only |
| `redis` | broker for the Celery worker | 6379 |
| `celery_worker` | Celery app, present for planned async work | none |

`postgres_data` and `node_modules` are named volumes, not services.

Generation is handled inline in the request: `/generate_molecule` calls
`MoleculeGenerator` directly and does not enqueue to Celery. `config.py` labels
the Celery settings as being for future async processing, so Redis and the
worker are wired up but not yet on the request path.

`DATABASE_URL` is injected into both `backend` and `celery_worker` by
`docker-compose.yml` and is documented in `docs/configuration.md`, though no
module under `backend/src` reads it yet.

---

## Execution

To initiate the platform:

```bash
docker-compose up --build
```

## Command Line Testing

For testing without the web interface, install and use the provided CLI tool:

```bash
# Build and install CLI (one-time)
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
- **Frontend Interface:** http://localhost:3000 (directly) or http://localhost:80 (through nginx)

---

## API Reference

### Molecule Generation

**Endpoint:** `POST /generate_molecule`

Facilitates the creation of molecular variants through systematic mutations.

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
- `num_mutations`: Mutation count (optional, default: 3)
- `mutation_types`: Permitted mutation categories (optional)

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
  }
}
```

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