"""Helpers for loading SEA-Tau result files."""

from __future__ import annotations

import json
from pathlib import Path


def resolve_result_paths(paths: list[Path]) -> list[Path]:
    """Resolve files and run directories to concrete results.json paths."""

    resolved: list[Path] = []
    for path in paths:
        if path.is_file():
            resolved.append(path)
        elif path.is_dir():
            results_json = path / "results.json"
            if results_json.exists():
                resolved.append(results_json)
            else:
                resolved.extend(sorted(path.rglob("results.json")))
    return resolved


def load_simulations(results_json: Path) -> tuple[dict, list[dict]]:
    """Load run metadata and simulations from a results.json file."""

    data = json.loads(results_json.read_text())
    simulations = data.get("simulations") or []
    simulations_dir = results_json.parent / "simulations"
    if simulations_dir.is_dir() and not simulations:
        for simulation_path in sorted(simulations_dir.glob("*.json")):
            simulations.append(json.loads(simulation_path.read_text()))
    return data.get("info", {}), simulations
