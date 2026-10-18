#!/usr/bin/env python3
"""Promote the changelog's Unreleased section to a released version heading.

Run when a version tag is pushed. Rewrites

    ## [Unreleased]

into

    ## [<version>] - <date>

and opens a fresh, empty Unreleased section above it, so the next round of
changes has somewhere to accumulate.

The heading carries no `v` prefix, matching the existing `## [1.0.0] -
2025-12-28`, even though the tag does.

The repo carries the changelog twice: CHANGELOG.md at the root, which
GitHub renders, and docs/changelog.md, which mkdocs.yml publishes. Both are
rewritten here, because the changelog-copies-match pre-commit hook fails
whenever they differ.

Exits non-zero rather than silently doing nothing, so a push that fails to
promote is visible instead of looking like a no-op.
"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import sys
import tomllib

UNRELEASED_HEADING = "## [Unreleased]"
NEXT_VERSION_HEADING = re.compile(r"^## \[")
PYPROJECT_VERSION = re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE)

FRESH_UNRELEASED = """## [Unreleased]

Work merged after `{tag}` and not yet cut into a release.
"""


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def promote(text: str, version: str, date: str, tag: str) -> str:
    """Return `text` with Unreleased promoted to `version`."""
    lines = text.split("\n")

    starts = [i for i, line in enumerate(lines) if line.strip() == UNRELEASED_HEADING]
    if not starts:
        fail(f"no {UNRELEASED_HEADING!r} heading found, nothing to promote")
    if len(starts) > 1:
        fail(f"{len(starts)} {UNRELEASED_HEADING!r} headings found, expected exactly 1")
    start = starts[0]

    # A re-run of the same tag would otherwise promote the fresh, near-empty
    # Unreleased section into a second heading for a version that already
    # exists. Refuse instead, so re-running a workflow is a no-op rather
    # than a way to corrupt the file.
    released_heading = f"## [{version}]"
    duplicates = [
        i for i, line in enumerate(lines) if line.strip().startswith(released_heading)
    ]
    if duplicates:
        fail(
            f"{released_heading} already present at line {duplicates[0] + 1}, "
            f"so {tag} has already been promoted. Delete this run's pull request "
            f"if it was created, or close and re-tag."
        )

    end = len(lines)
    for i in range(start + 1, len(lines)):
        if NEXT_VERSION_HEADING.match(lines[i]):
            end = i
            break

    body = "\n".join(lines[start + 1 : end]).strip("\n")

    released: list[str] = [f"## [{version}] - {date}"]
    if body:
        released.append("")
        released.extend(body.split("\n"))

    fresh = FRESH_UNRELEASED.format(tag=tag).rstrip("\n").split("\n")
    return "\n".join(lines[:start] + fresh + [""] + released + [""] + lines[end:])


def pyproject_version(root: pathlib.Path) -> str | None:
    path = root / "backend" / "pyproject.toml"
    if not path.is_file():
        return None
    try:
        found = (
            tomllib.loads(path.read_text(encoding="utf-8"))
            .get("project", {})
            .get("version")
        )
    except tomllib.TOMLDecodeError as exc:
        fail(f"could not parse {path}: {exc}")
    if not isinstance(found, str):
        return None
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="release version, no v prefix")
    parser.add_argument("--tag", required=True, help="full git tag, e.g. v1.1.0")
    parser.add_argument(
        "--date", default=None, help="release date, defaults to today (UTC)"
    )
    parser.add_argument("--root", default=".", type=pathlib.Path)
    parser.add_argument(
        "--report", default=None, type=pathlib.Path, help="markdown report path"
    )
    args = parser.parse_args()

    if args.version.startswith("v"):
        fail(f"--version should not carry the v prefix, got {args.version!r}")

    date = args.date or dt.datetime.now(dt.UTC).date().isoformat()
    root = args.root.resolve()

    changelog = root / "CHANGELOG.md"
    if not changelog.is_file():
        fail(f"{changelog} not found")

    original = changelog.read_text(encoding="utf-8")
    updated = promote(original, args.version, date, args.tag)
    if updated == original:
        fail("promotion produced no change, refusing to open an empty pull request")

    changelog.write_text(updated, encoding="utf-8")

    published = root / "docs" / "changelog.md"
    if published.is_file():
        published.write_text(updated, encoding="utf-8")
        published_note = "Rewrote `docs/changelog.md` to match."
    else:
        published_note = (
            "`docs/changelog.md` not found, only the root file was rewritten."
        )

    declared = pyproject_version(root)
    if declared is None:
        version_note = (
            "Could not read `backend/pyproject.toml`, version not cross-checked."
        )
    elif declared == args.version:
        version_note = (
            f"`backend/pyproject.toml` declares `{declared}`, matching the tag."
        )
    else:
        version_note = (
            f"`backend/pyproject.toml` declares `{declared}` but the tag is `{args.version}`. "
            f"The binaries built from this tag will report `{declared}` from `/health`."
        )

    if args.report:
        lines = [
            f"`## [Unreleased]` was promoted to `## [{args.version}] - {date}`.",
            "",
            "A fresh `## [Unreleased]` section was opened above it.",
            "",
            published_note,
            "",
            version_note,
            "",
            "Generated by `.github/scripts/promote_changelog.py`. The only manual step is merging this.",
        ]
        args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"promoted Unreleased to {args.version} dated {date}")
    print(published_note)
    print(version_note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
