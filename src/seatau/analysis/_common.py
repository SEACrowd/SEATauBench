"""Shared helpers for experiment analysis modules."""

from __future__ import annotations

import json
from pathlib import Path


def resolve_paths(paths: list[Path]) -> list[Path]:
    """Resolve files and run directories to concrete results.json paths."""
    resolved: list[Path] = []
    for p in paths:
        if p.is_file():
            resolved.append(p)
        elif p.is_dir():
            rj = p / "results.json"
            if rj.exists():
                resolved.append(rj)
            else:
                for sub in sorted(p.iterdir()):
                    if (sub / "results.json").exists():
                        resolved.append(sub / "results.json")
    return resolved


def load_simulations(results_json: Path) -> tuple[dict, list[dict]]:
    """Load run metadata and simulations from a results.json file."""
    data = json.loads(results_json.read_text())
    sims = data.get("simulations") or []
    sims_dir = results_json.parent / "simulations"
    if sims_dir.is_dir() and not sims:
        for f in sorted(sims_dir.glob("*.json")):
            sims.append(json.loads(f.read_text()))
    return data.get("info", {}), sims

