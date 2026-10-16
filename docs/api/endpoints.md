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
  }
}
```

**Mutation Types:**
- `substituent`: Add random substituents
- `bond_order`: Modify bond orders
- `atom_swap`: Swap atoms

## Interactive Documentation

Visit `/docs` for interactive API documentation with the ability to test endpoints directly.
