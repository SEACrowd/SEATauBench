from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


def to_project_relative_path(path: Path) -> Path:
    """Return ``path`` relative to the project root."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(
            f"Path {resolved} is outside project root {PROJECT_ROOT}"
        ) from exc


def resolve_project_path(path: str | Path) -> Path:
    """Resolve a manifest path relative to the project root when needed."""
    resolved = Path(path)
    if resolved.is_absolute():
        return resolved.resolve()
    return (PROJECT_ROOT / resolved).resolve()
