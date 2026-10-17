import pytest
from fastapi.testclient import TestClient

from src.config import settings
from src.main import MAX_MUTATIONS_PER_REQUEST, app

client = TestClient(app)


headers = {"Authorization": f"Bearer {settings.API_KEY}"}


def test_health_endpoint():
    response = client.get("/health", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_generate_molecule_endpoint():
    payload = {"base_smiles": "CC(=O)OC1=CC=CC=C1C(=O)O", "num_mutations": 1}
    response = client.post("/generate_molecule", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "generated_smiles" in data
    assert "molecular_image" in data
    assert "properties" in data


def test_generate_molecule_validation():
    # Test empty base_smiles
    payload = {"base_smiles": "", "num_mutations": 1}
    response = client.post("/generate_molecule", json=payload, headers=headers)
    assert response.status_code == 400

    # Test negative num_mutations
    payload = {"base_smiles": "CCO", "num_mutations": -1}
    response = client.post("/generate_molecule", json=payload, headers=headers)
    assert response.status_code == 400


@pytest.mark.parametrize("num_mutations", [0, 1, MAX_MUTATIONS_PER_REQUEST])
def test_num_mutations_boundaries_are_accepted(num_mutations):
    """The boundary values must still work, including the limit itself."""
    payload = {"base_smiles": "CCO", "num_mutations": num_mutations}
    response = client.post("/generate_molecule", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["requested_mutations"] == num_mutations


@pytest.mark.parametrize(
    "num_mutations", [-1, MAX_MUTATIONS_PER_REQUEST + 1, 100, 10_000]
)
def test_num_mutations_outside_the_limit_is_rejected(num_mutations):
    """Excessive values must be refused, not silently accepted and executed.

    This is the request-level bound. Without it, cost scales with the requested
    count and the CPU-bound work blocks the event loop, because the endpoint is
    declared async.
    """
    payload = {"base_smiles": "CCO", "num_mutations": num_mutations}
    response = client.post("/generate_molecule", json=payload, headers=headers)
    # 400, not 422: both bounds fail the same way, and the negative case already
    # had a tested 400 contract that a pydantic bound would change.
    assert response.status_code == 400
    assert "num_mutations" in response.json()["detail"]
