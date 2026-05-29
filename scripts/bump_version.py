#!/usr/bin/env python3
"""Bump alloc-context release version across tracked files."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Literal

BumpPart = Literal["patch", "minor", "major"]

_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def read_current_version(root: Path | None = None) -> str:
    root = root or repo_root()
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def parse_version(version: str) -> tuple[int, int, int]:
    match = _VERSION_RE.match(version.strip())
    if not match:
        raise ValueError(f"invalid semver: {version!r} (expected X.Y.Z)")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_version(current: str, part: BumpPart) -> str:
    major, minor, patch = parse_version(current)
    if part == "patch":
        patch += 1
    elif part == "minor":
        minor += 1
        patch = 0
    else:
        major += 1
        minor = 0
        patch = 0
    return f"{major}.{minor}.{patch}"


def _replace_pyproject_version(text: str, version: str) -> str:
    updated, count = re.subn(
        r'^(version = ")[^"]+(")',
        rf'\g<1>{version}\g<2>',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise RuntimeError("pyproject.toml: could not update version line")
    return updated


def _replace_init_version(text: str, version: str) -> str:
    updated, count = re.subn(
        r'^(__version__ = ")[^"]+(")',
        rf'\g<1>{version}\g<2>',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise RuntimeError("alloccontext/__init__.py: could not update __version__")
    return updated


def apply_version(version: str, root: Path | None = None) -> None:
    root = root or repo_root()
    parse_version(version)

    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        _replace_pyproject_version(pyproject.read_text(encoding="utf-8"), version),
        encoding="utf-8",
    )

    server_json = root / "server.json"
    server = json.loads(server_json.read_text(encoding="utf-8"))
    server["version"] = version
    server["packages"][0]["version"] = version
    server_json.write_text(
        json.dumps(server, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    init_py = root / "alloccontext" / "__init__.py"
    init_py.write_text(
        _replace_init_version(init_py.read_text(encoding="utf-8"), version),
        encoding="utf-8",
    )


def versions_in_sync(version: str, root: Path | None = None) -> bool:
    root = root or repo_root()
    try:
        if read_current_version(root) != version:
            return False
        server = json.loads((root / "server.json").read_text(encoding="utf-8"))
        if server["version"] != version:
            return False
        if server["packages"][0]["version"] != version:
            return False
        init_text = (root / "alloccontext" / "__init__.py").read_text(encoding="utf-8")
        match = re.search(r'^__version__ = "([^"]+)"', init_text, re.MULTILINE)
        return bool(match and match.group(1) == version)
    except (KeyError, OSError, json.JSONDecodeError):
        return False


def resolve_target_version(
    *,
    current: str,
    bump: BumpPart | None,
    exact: str | None,
) -> str:
    if exact:
        parse_version(exact)
        return exact
    if bump is None:
        raise ValueError("provide --bump or an exact version")
    return bump_version(current, bump)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "exact_version",
        nargs="?",
        help="Exact target version (e.g. 0.2.0); overrides --bump",
    )
    parser.add_argument(
        "--bump",
        choices=("patch", "minor", "major"),
        help="Increment from current pyproject.toml version",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Update version files (default: dry-run)",
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="Print the resolved version on stdout",
    )
    args = parser.parse_args(argv)

    current = read_current_version()
    target = resolve_target_version(
        current=current,
        bump=args.bump,
        exact=args.exact_version,
    )

    if not args.write:
        print(f"current={current} target={target} (dry-run; pass --write to apply)")
        if args.print:
            print(target)
        return 0

    if target == current:
        print(f"version already {current}", file=sys.stderr)
        return 1

    apply_version(target)
    if not versions_in_sync(target):
        print("version files out of sync after apply", file=sys.stderr)
        return 1

    if args.print:
        print(target)
    else:
        print(f"bumped {current} -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
