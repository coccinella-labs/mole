"""Resolve the service version from packaging metadata.

``pyproject.toml`` is the single source of truth. Distribution metadata is
preferred because it works for any installed distribution, including a wheel
built from this project. The container and a bare checkout both run without
the distribution installed, so metadata is unavailable there; those fall back
to parsing ``pyproject.toml`` instead of a hardcoded literal, which would
silently drift from the real version.
"""

from __future__ import annotations

import tomllib
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as distribution_version
from pathlib import Path

DISTRIBUTION_NAME = "mol-platform"
_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _version_from_pyproject() -> str:
    """Read ``project.version`` from pyproject.toml."""
    with _PYPROJECT.open("rb") as handle:
        return str(tomllib.load(handle)["project"]["version"])


def resolve_version() -> str:
    """Return the installed distribution version, else the pyproject value.

    Raises RuntimeError only if neither source is readable, so the failure is
    visible rather than masked by a stale default.
    """
    try:
        return distribution_version(DISTRIBUTION_NAME)
    except PackageNotFoundError:
        return _version_from_pyproject()
