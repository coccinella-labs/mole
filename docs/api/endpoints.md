# API Endpoints

Detailed documentation of all API endpoints.

## Health Check

### GET /health

Returns the health status of the service.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## Molecule Generation

### POST /generate_molecule

Generates a new molecule by applying random mutations to a base molecule.

**Request Body:**
```json
{
  "base_smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
  "num_mutations": 3,
  "mutation_types": ["substituent", "bond_order", "atom_swap"]
}
```

**Parameters:**
- `base_smiles` (string, required): SMILES string of the base molecule
- `num_mutations` (integer, optional): Number of mutations to apply (default: 3)
- `mutation_types` (array, optional): Types of mutations to apply

**Response:**
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

| Field | Meaning |
|---|---|
| `requested_mutations` | Logical mutations requested, echoed from the request |
| `successful_mutations` | Mutations that made their intended structural change and passed sanitisation |
| `failed_mutations` | Mutations where no candidate made an intended, valid change |
| `mutated` | `true` when `successful_mutations` is greater than zero |

Counters are per logical mutation, not per candidate attempt. A single mutation
tries several candidate positions and keeps the first that RDKit accepts, so
`successful_mutations + failed_mutations` always equals `requested_mutations`
for a completed request.

**Success requires a real change, not just a valid molecule.** A candidate that
passes sanitisation without altering the structure is counted in
`failed_mutations`, not `successful_mutations`. This matters because RDKit
re-perceives aromaticity during sanitisation, so setting a bond inside an
aromatic ring to single or double is accepted and then silently undone, leaving
the structure identical. Treating those as successes would overstate real work;
before this was corrected, 90% of accepted `bond_order` candidates on caffeine
changed nothing.

Because of this, heavily aromatic molecules report a higher `failed_mutations`
than saturated ones. Caffeine fails about 7% of logical mutations this way, which
is an accurate report rather than a defect.

When `mutated` is `false`, no mutation was applied and `generated_smiles` is
identical to `original_smiles`. The request still returns `200`; the counters
are how a caller distinguishes that case from real work.

**Mutation Types:**
- `substituent`: Add random substituents
- `bond_order`: Modify bond orders
- `atom_swap`: Swap atoms

## Interactive Documentation

Visit `/docs` for interactive API documentation with the ability to test endpoints directly.
