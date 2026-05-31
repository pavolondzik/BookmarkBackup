"""Locate frontend/ and frontend/dist for static serving and diagnostics."""

from __future__ import annotations

import os
from pathlib import Path

_FRONTEND_MARKERS = ("package.json",)


def _is_frontend_dir(path: Path) -> bool:
    return path.is_dir() and all((path / name).is_file() for name in _FRONTEND_MARKERS)


def find_frontend_dir() -> Path | None:
    """Search upward from cwd and this module for a directory named frontend/."""
    env_root = os.getenv("FRONTEND_ROOT")
    if env_root:
        candidate = Path(env_root).resolve()
        if _is_frontend_dir(candidate):
            return candidate

    seen: set[Path] = set()
    start_points = [Path.cwd().resolve(), Path(__file__).resolve()]
    for start in start_points:
        for base in (start, *start.parents):
            if base in seen:
                continue
            seen.add(base)
            candidate = base / "frontend"
            if _is_frontend_dir(candidate):
                return candidate.resolve()
    return None


def resolve_frontend_dist() -> Path | None:
    """Return frontend/dist if index.html exists, else None."""
    env_dist = os.getenv("FRONTEND_DIST")
    if env_dist:
        dist = Path(env_dist).resolve()
        if (dist / "index.html").is_file():
            return dist

    frontend = find_frontend_dir()
    if frontend is None:
        return None

    dist = (frontend / "dist").resolve()
    if (dist / "index.html").is_file():
        return dist
    return None
