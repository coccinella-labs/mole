"""Tests for version resolution.

Covers both runtime shapes the project actually uses:

- an installed distribution, where importlib.metadata answers
- a bare checkout with no installed distribution, which is how the container
  and the test suite run, where pyproject.toml is the only source
"""

from src.version import DISTRIBUTION_NAME, _version_from_pyproject, resolve_version


def test_resolves_from_pyproject_when_package_is_not_installed():
    """The container installs requirements.txt only, so metadata is absent.

    This is the shape the deployed image and this test suite both run in, and
    it must not raise or fall back to a stale literal.
    """
    from importlib.metadata import PackageNotFoundError, version

    try:
        installed = version(DISTRIBUTION_NAME)
    except PackageNotFoundError:
        installed = None

    resolved = resolve_version()

    assert resolved
    if installed is None:
        assert resolved == _version_from_pyproject()
    else:
        assert resolved == installed


def test_pyproject_is_the_source_of_truth():
    """pyproject.toml parses and carries a non-empty project.version."""
    parsed = _version_from_pyproject()

    assert isinstance(parsed, str)
    assert parsed
    assert parsed.count(".") >= 1


def test_app_version_matches_resolver():
    """The FastAPI app must expose the resolved version, not a literal.

    Guards the drift this change exists to remove: /health reported whatever
    string was typed into main.py while the package carried a different one.
    """
    from src.main import app

    assert app.version == resolve_version()


def test_health_endpoint_reports_resolved_version():
    """GET /health returns the resolved version in its payload."""
    from fastapi.testclient import TestClient

    from src.config import settings
    from src.main import app

    client = TestClient(app)
    response = client.get("/health", headers={"Authorization": f"Bearer {settings.API_KEY}"})

    assert response.status_code == 200
    assert response.json()["version"] == resolve_version()