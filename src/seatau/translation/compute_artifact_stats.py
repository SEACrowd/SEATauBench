#!/usr/bin/env python3
"""Compute reproducible summary statistics for the translation appendix.

The script derives its numbers from source files, translated artifacts, and
translation manifests in the current repository state. It can emit either a
Markdown report
or a JSON blob for downstream automation.

uv run python src/seatau/translation/compute_artifact_stats.py \
    --format markdown \
    --write-csv-dir data/seatau/stats

"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
import tomllib
from pathlib import Path
from typing import Any

from paths import (
    LANGUAGES_PATH,
    TAU2_DOMAINS_DATA,
    TAU2_DOMAINS_SRC,
    resolve_project_path,
)
from seatau.constants import get_l2_language_codes
from seatau.experiment_matrix import list_supported_domains

DOMAINS = tuple(list_supported_domains())
LANGUAGE_CODES = get_l2_language_codes()
LANGUAGES_PATH = resolve_project_path(LANGUAGES_PATH)
TAU2_DOMAINS_DATA = resolve_project_path(TAU2_DOMAINS_DATA)
TAU2_DOMAINS_SRC = resolve_project_path(TAU2_DOMAINS_SRC)
TOOL_DECORATORS = {"is_tool", "is_discoverable_tool"}
PLACEHOLDER_RE = re.compile(r"\{[^{}]+\}")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_toml(path: Path) -> Any:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def render_row(row: list[str]) -> str:
        cells = [f" {cell.ljust(widths[idx])} " for idx, cell in enumerate(row)]
        return "|" + "|".join(cells) + "|"

    separator = "|" + "|".join("-" * (width + 2) for width in widths) + "|"
    lines = [render_row(headers), separator]
    lines.extend(render_row(row) for row in rows)
    return "\n".join(lines)


def _fmt(value: int) -> str:
    return f"{value:,}"


def _csv_write(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def _count_string_leaves(node: Any) -> tuple[int, int]:
    count = 0
    chars = 0
    if isinstance(node, dict):
        for value in node.values():
            child_count, child_chars = _count_string_leaves(value)
            count += child_count
            chars += child_chars
    elif isinstance(node, list):
        for value in node:
            child_count, child_chars = _count_string_leaves(value)
            count += child_count
            chars += child_chars
    elif isinstance(node, str):
        count += 1
        chars += len(node)
    return count, chars


def _root_md_files(domain: str) -> list[Path]:
    return sorted(
        path for path in (TAU2_DOMAINS_DATA / domain).glob("*.md") if path.is_file()
    )


def _parse_tool_decorator(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return _parse_tool_decorator(node.func)
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def _count_tool_docstrings(path: Path) -> dict[str, int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    count = 0
    chars = 0

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not any(
            _parse_tool_decorator(decorator) in TOOL_DECORATORS
            for decorator in node.decorator_list
        ):
            continue
        docstring = ast.get_docstring(node, clean=True) or ""
        if not docstring:
            continue
        count += 1
        chars += len(docstring)

    return {"count": count, "chars": chars}


def _extract_tool_return_messages(path: Path) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        target: ast.AST | None = None
        value: ast.AST | None = None
        if isinstance(node, ast.AnnAssign):
            target = node.target
            value = node.value
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            value = node.value
        if (
            isinstance(target, ast.Name)
            and target.id == "TOOL_RETURN_MESSAGES"
            and isinstance(value, ast.Dict)
        ):
            messages: dict[str, str] = {}
            for key_node, value_node in zip(value.keys, value.values, strict=False):
                if (
                    isinstance(key_node, ast.Constant)
                    and isinstance(key_node.value, str)
                    and isinstance(value_node, ast.Constant)
                    and isinstance(value_node.value, str)
                ):
                    messages[key_node.value] = value_node.value
            return messages
    return {}


def _tool_return_stats(domain: str) -> dict[str, int]:
    if domain != "telecom":
        return {
            "exact_count": 0,
            "template_count": 0,
            "total_count": 0,
            "chars": 0,
        }
    messages = _extract_tool_return_messages(TAU2_DOMAINS_SRC / domain / "tools.py")
    exact_count = 0
    template_count = 0
    chars = 0
    for value in messages.values():
        chars += len(value)
        if PLACEHOLDER_RE.search(value):
            template_count += 1
        else:
            exact_count += 1
    return {
        "exact_count": exact_count,
        "template_count": template_count,
        "total_count": len(messages),
        "chars": chars,
    }


def _manifest_assets(domain: str, language: str) -> list[str]:
    manifest_path = TAU2_DOMAINS_DATA / domain / language / "translation_manifest.json"
    if not manifest_path.exists():
        return []
    manifest = _load_json(manifest_path)
    assets = manifest.get("assets", {})
    if not isinstance(assets, dict):
        return []
    return sorted(str(key) for key in assets.keys())


def _coverage_rows() -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    total = 0
    known_languages = list(
        json.loads(LANGUAGES_PATH.read_text(encoding="utf-8")).keys()
    )
    ordered_languages = [lang for lang in LANGUAGE_CODES if lang in known_languages] + [
        lang for lang in known_languages if lang not in LANGUAGE_CODES
    ]

    for domain in DOMAINS:
        langs = [lang for lang in ordered_languages if _manifest_assets(domain, lang)]
        artifact_names: list[str] = []
        artifact_count = 0
        for lang in langs:
            assets = _manifest_assets(domain, lang)
            artifact_count = max(artifact_count, len(assets))
            total += len(assets)
            for asset in assets:
                if asset not in artifact_names:
                    artifact_names.append(asset)
        rows.append(
            {
                "domain": domain,
                "languages": langs,
                "artifact_count": artifact_count,
                "artifact_names": artifact_names,
                "total": artifact_count * len(langs),
            }
        )
    return rows, total


def _task_stats(domain: str) -> dict[str, int]:
    path = TAU2_DOMAINS_DATA / domain / "tasks.json"
    data = _load_json(path)
    tasks = data if isinstance(data, list) else []
    string_fields = 0
    chars = 0
    for task in tasks:
        child_count, child_chars = _count_string_leaves(task)
        string_fields += child_count
        chars += child_chars
    if domain == "telecom":
        split_path = TAU2_DOMAINS_DATA / domain / "split_tasks.json"
        split_tasks = _load_json(split_path)
        base_ids = split_tasks.get("base", []) if isinstance(split_tasks, dict) else []
        task_ids = {
            task["id"]
            for task in tasks
            if isinstance(task, dict) and isinstance(task.get("id"), str)
        }
        task_count = sum(
            1
            for task_id in base_ids
            if isinstance(task_id, str) and task_id in task_ids
        )
    else:
        task_count = len(tasks)
    return {
        "tasks": task_count,
        "string_fields": string_fields,
        "chars": chars,
    }


def _policy_stats(domain: str) -> dict[str, Any]:
    files = _root_md_files(domain)
    words = 0
    for path in files:
        words += len(path.read_text(encoding="utf-8").split())
    return {"files": len(files), "words": words}


def _tool_doc_stats(domain: str) -> dict[str, Any]:
    src_root = TAU2_DOMAINS_SRC / domain
    agent_stats = _count_tool_docstrings(src_root / "tools.py")
    user_path = src_root / "user_tools.py"
    user_stats = (
        _count_tool_docstrings(user_path)
        if user_path.exists()
        else {
            "count": 0,
            "chars": 0,
        }
    )
    return {
        "agent_tools": agent_stats["count"],
        "user_tools": user_stats["count"],
        "total": agent_stats["count"] + user_stats["count"],
        "chars": agent_stats["chars"] + user_stats["chars"],
    }


def _schema_artifact_stats(domain: str, language: str) -> dict[str, Any]:
    lang_root = TAU2_DOMAINS_DATA / domain / language
    stats: dict[str, Any] = {}
    for filename, prefix in (
        ("data_model.json", "agent"),
        ("user_data_model.json", "user"),
    ):
        path = lang_root / filename
        if not path.exists():
            stats[f"{prefix}_models"] = 0
            stats[f"{prefix}_value_sets"] = 0
            stats[f"{prefix}_localized_values"] = 0
            continue
        artifact = _load_json(path)
        models = artifact.get("models", {})
        value_sets = artifact.get("value_sets", {})
        localized_values = 0
        if isinstance(value_sets, dict):
            for value_set in value_sets.values():
                if not isinstance(value_set, dict):
                    continue
                values = value_set.get("values", [])
                if not isinstance(values, list):
                    continue
                for entry in values:
                    if isinstance(entry, dict) and entry.get("localized"):
                        localized_values += 1
        stats[f"{prefix}_models"] = len(models) if isinstance(models, dict) else 0
        stats[f"{prefix}_value_sets"] = (
            len(value_sets) if isinstance(value_sets, dict) else 0
        )
        stats[f"{prefix}_localized_values"] = localized_values
    return stats


def _db_collection_summary(data: Any) -> tuple[int, list[tuple[str, int]]]:
    collections: list[tuple[str, int]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                collections.append((str(key), len(value)))
            elif isinstance(value, list):
                collections.append((str(key), len(value)))
    return len(collections), collections


def _db_stats(domain: str) -> dict[str, Any]:
    root = TAU2_DOMAINS_DATA / domain
    files: list[Path] = []
    if (root / "db.json").exists():
        files.append(root / "db.json")
    if (root / "db.toml").exists():
        files.append(root / "db.toml")
    if (root / "user_db.json").exists():
        files.append(root / "user_db.json")
    if (root / "user_db.toml").exists():
        files.append(root / "user_db.toml")

    collection_total = 0
    collection_parts: list[str] = []
    formats: list[str] = []
    for path in files:
        if path.suffix == ".json":
            data = _load_json(path)
        else:
            data = _load_toml(path)
        count, collections = _db_collection_summary(data)
        collection_total += count
        formats.append(path.name)
        collection_label = path.name
        collection_text = ", ".join(f"{name}: {size:,}" for name, size in collections)
        collection_parts.append(f"{collection_label}: {collection_text}")

    return {
        "formats": ", ".join(formats),
        "collections": collection_total,
        "records": "; ".join(collection_parts),
    }


def build_report() -> dict[str, Any]:
    coverage_rows, coverage_total = _coverage_rows()
    languages = [lang for lang in LANGUAGE_CODES if lang in _available_languages()]
    report: dict[str, Any] = {
        "languages": languages,
        "coverage": {
            "rows": coverage_rows,
            "total": coverage_total,
        },
        "domains": {},
    }

    for domain in DOMAINS:
        representative_language = next(
            (lang for lang in LANGUAGE_CODES if _manifest_assets(domain, lang)),
            "",
        )
        report["domains"][domain] = {
            "tasks": _task_stats(domain),
            "tool_docs": _tool_doc_stats(domain),
            "tool_returns": _tool_return_stats(domain),
            "policies": _policy_stats(domain),
            "schemas": _schema_artifact_stats(domain, representative_language)
            if representative_language
            else {
                "agent_models": 0,
                "agent_value_sets": 0,
                "agent_localized_values": 0,
                "user_models": 0,
                "user_value_sets": 0,
                "user_localized_values": 0,
            },
            "db": _db_stats(domain),
            "manifest_assets": {
                lang: _manifest_assets(domain, lang)
                for lang in _available_languages()
                if _manifest_assets(domain, lang)
            },
        }

    return report


def _available_languages() -> list[str]:
    registry = json.loads(LANGUAGES_PATH.read_text(encoding="utf-8"))
    return [lang for lang in LANGUAGE_CODES if lang in registry] + [
        lang for lang in registry if lang not in LANGUAGE_CODES
    ]


def _as_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("## Translation corpus statistics")
    lines.append("")
    lines.append("The canonical summary tables are exported as CSV files under")
    lines.append("`data/seatau/stats/` and can be regenerated with:")
    lines.append("")
    lines.append("```bash")
    lines.append("uv run python src/seatau/translation/compute_artifact_stats.py \\")
    lines.append("  --format markdown \\")
    lines.append("  --write-csv-dir data/seatau/stats")
    lines.append("```")
    lines.append("")
    lines.append(
        "The Markdown tables below mirror those CSV files for convenience in the paper\n"
        "draft. All translations were produced with **Vertex AI Gemini Flash Lite**"
    )
    lines.append("(`vertex_ai/gemini-3.1-flash-lite-preview`).")
    lines.append("")
    lines.append("### Coverage")
    lines.append("")
    lines.append(
        _markdown_table(
            [
                "Domain",
                "Languages translated",
                "Artifact files per language",
                "Total translated files",
            ],
            [
                [
                    row["domain"].capitalize(),
                    f"{', '.join(row['languages'])} ({len(row['languages'])})",
                    f"{row['artifact_count']} ({', '.join(row['artifact_names'])})",
                    _fmt(row["total"]),
                ]
                for row in report["coverage"]["rows"]
            ]
            + [
                [
                    "**Total**",
                    f"**{len(report['languages'])} languages × {len(DOMAINS)} domains**",
                    "—",
                    f"**{report['coverage']['total']}**",
                ]
            ],
        )
    )
    lines.append("")
    lines.append("### Artifact composition")
    lines.append("")
    lines.append(
        "**Tasks** (scenario definitions, persona instructions, natural-language\n"
        "assertions, and visible message history):"
    )
    lines.append("")
    lines.append(
        "Telecom task counts below use the 114 base tasks referenced by the benchmark. "
        "The source string-field and character totals are computed on the expanded task "
        "JSON currently stored in `data/tau2/domains/telecom/tasks.json` and the base "
        "split in `data/tau2/domains/telecom/split_tasks.json`."
    )
    lines.append("")
    lines.append(
        _markdown_table(
            [
                "Domain",
                "Tasks in source",
                "Source string fields",
                "Source chars",
                "Translated task instances (×5 langs)",
            ],
            [
                [
                    domain.capitalize(),
                    _fmt(stats["tasks"]),
                    _fmt(stats["string_fields"]),
                    _fmt(stats["chars"]),
                    _fmt(stats["tasks"] * len(report["languages"])),
                ]
                for domain, stats in (
                    (domain, report["domains"][domain]["tasks"]) for domain in DOMAINS
                )
            ],
        )
    )
    lines.append("")
    lines.append(
        "**Tool docstrings** (translated tool-facing descriptions emitted as JSON):"
    )
    lines.append("")
    lines.append(
        _markdown_table(
            [
                "Domain",
                "Agent tools",
                "User tools",
                "Total translated docstrings per language",
                "Approx. source docstring chars",
            ],
            [
                [
                    domain.capitalize(),
                    _fmt(stats["agent_tools"]),
                    _fmt(stats["user_tools"]),
                    _fmt(stats["total"]),
                    _fmt(stats["chars"]),
                ]
                for domain, stats in (
                    (domain, report["domains"][domain]["tool_docs"])
                    for domain in DOMAINS
                )
            ],
        )
    )
    lines.append("")
    lines.append(
        "**Tool-return messages** (telecom runtime responses translated into `tool_returns.json`):"
    )
    lines.append("")
    lines.append(
        _markdown_table(
            [
                "Domain",
                "Exact messages",
                "Template messages",
                "Source messages",
                "Approx. source chars",
                "Translated instances (×5 langs)",
            ],
            [
                [
                    domain.capitalize(),
                    _fmt(stats["exact_count"]),
                    _fmt(stats["template_count"]),
                    _fmt(stats["total_count"]),
                    _fmt(stats["chars"]),
                    _fmt(stats["total_count"] * len(report["languages"])),
                ]
                for domain, stats in (
                    (domain, report["domains"][domain]["tool_returns"])
                    for domain in DOMAINS
                )
            ],
        )
    )
    lines.append("")
    lines.append(
        "**Policy and workflow documents** (full-document markdown translation):"
    )
    lines.append("")
    lines.append(
        _markdown_table(
            [
                "Domain",
                "Source markdown files",
                "Approx. English word count",
                "Translated document instances (×5 langs)",
            ],
            [
                [
                    domain.capitalize(),
                    _fmt(stats["files"]),
                    _fmt(stats["words"]),
                    _fmt(stats["files"] * len(report["languages"])),
                ]
                for domain, stats in (
                    (domain, report["domains"][domain]["policies"])
                    for domain in DOMAINS
                )
            ],
        )
    )
    lines.append("")
    lines.append(
        "**Schema artifacts** (localized descriptions and literal inventories):"
    )
    lines.append("")
    lines.append(
        _markdown_table(
            [
                "Domain",
                "Agent models",
                "Agent value sets",
                "Agent localized values",
                "User models",
                "User value sets",
                "User localized values",
            ],
            [
                [
                    domain.capitalize(),
                    _fmt(stats["agent_models"]),
                    _fmt(stats["agent_value_sets"]),
                    _fmt(stats["agent_localized_values"]),
                    _fmt(stats["user_models"]),
                    _fmt(stats["user_value_sets"]),
                    _fmt(stats["user_localized_values"]),
                ]
                for domain, stats in (
                    (domain, report["domains"][domain]["schemas"]) for domain in DOMAINS
                )
            ],
        )
    )
    lines.append("")
    lines.append(
        "**Database artifacts** (structure preserved; only selected natural-language leaf\n"
        "fields translated):"
    )
    lines.append("")
    lines.append(
        _markdown_table(
            ["Domain", "Formats", "Collections", "Record breakdown"],
            [
                [
                    domain.capitalize(),
                    stats["formats"],
                    _fmt(stats["collections"]),
                    stats["records"],
                ]
                for domain, stats in (
                    (domain, report["domains"][domain]["db"]) for domain in DOMAINS
                )
            ],
        )
    )
    return "\n".join(lines)


def _csv_tables(report: dict[str, Any]) -> dict[str, tuple[list[str], list[list[str]]]]:
    coverage_rows = [
        [
            row["domain"].capitalize(),
            ", ".join(row["languages"]),
            str(row["artifact_count"]),
            ", ".join(row["artifact_names"]),
            str(row["total"]),
        ]
        for row in report["coverage"]["rows"]
    ]
    coverage_rows.append(
        [
            "Total",
            f"{len(report['languages'])} languages x {len(DOMAINS)} domains",
            "",
            "",
            str(report["coverage"]["total"]),
        ]
    )

    return {
        "coverage.csv": (
            [
                "Domain",
                "Languages translated",
                "Artifact files per language",
                "Artifact names",
                "Total translated files",
            ],
            coverage_rows,
        ),
        "tasks.csv": (
            [
                "Domain",
                "Tasks in source",
                "Source string fields",
                "Source chars",
                "Translated task instances (x5 langs)",
            ],
            [
                [
                    domain.capitalize(),
                    str(stats["tasks"]),
                    str(stats["string_fields"]),
                    str(stats["chars"]),
                    str(stats["tasks"] * len(report["languages"])),
                ]
                for domain, stats in (
                    (domain, report["domains"][domain]["tasks"]) for domain in DOMAINS
                )
            ],
        ),
        "tool_docstrings.csv": (
            [
                "Domain",
                "Agent tools",
                "User tools",
                "Total translated docstrings per language",
                "Approx source docstring chars",
            ],
            [
                [
                    domain.capitalize(),
                    str(stats["agent_tools"]),
                    str(stats["user_tools"]),
                    str(stats["total"]),
                    str(stats["chars"]),
                ]
                for domain, stats in (
                    (domain, report["domains"][domain]["tool_docs"])
                    for domain in DOMAINS
                )
            ],
        ),
        "tool_return_messages.csv": (
            [
                "Domain",
                "Exact messages",
                "Template messages",
                "Source messages",
                "Approx source chars",
                "Translated instances x5 langs",
            ],
            [
                [
                    domain.capitalize(),
                    str(stats["exact_count"]),
                    str(stats["template_count"]),
                    str(stats["total_count"]),
                    str(stats["chars"]),
                    str(stats["total_count"] * len(report["languages"])),
                ]
                for domain, stats in (
                    (
                        domain,
                        report["domains"][domain]["tool_returns"],
                    )
                    for domain in DOMAINS
                )
            ],
        ),
        "policies.csv": (
            [
                "Domain",
                "Source markdown files",
                "Approx English word count",
                "Translated document instances x5 langs",
            ],
            [
                [
                    domain.capitalize(),
                    str(stats["files"]),
                    str(stats["words"]),
                    str(stats["files"] * len(report["languages"])),
                ]
                for domain, stats in (
                    (domain, report["domains"][domain]["policies"])
                    for domain in DOMAINS
                )
            ],
        ),
        "schemas.csv": (
            [
                "Domain",
                "Agent models",
                "Agent value sets",
                "Agent localized values",
                "User models",
                "User value sets",
                "User localized values",
            ],
            [
                [
                    domain.capitalize(),
                    str(stats["agent_models"]),
                    str(stats["agent_value_sets"]),
                    str(stats["agent_localized_values"]),
                    str(stats["user_models"]),
                    str(stats["user_value_sets"]),
                    str(stats["user_localized_values"]),
                ]
                for domain, stats in (
                    (domain, report["domains"][domain]["schemas"]) for domain in DOMAINS
                )
            ],
        ),
        "databases.csv": (
            ["Domain", "Formats", "Collections", "Record breakdown"],
            [
                [
                    domain.capitalize(),
                    stats["formats"],
                    str(stats["collections"]),
                    stats["records"],
                ]
                for domain, stats in (
                    (domain, report["domains"][domain]["db"]) for domain in DOMAINS
                )
            ],
        ),
    }


def write_csv_tables(report: dict[str, Any], output_dir: Path) -> list[Path]:
    written: list[Path] = []
    for filename, (headers, rows) in _csv_tables(report).items():
        path = output_dir / filename
        _csv_write(path, headers, rows)
        written.append(path)
    return written


def _as_json(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute summary statistics for the translation appendix."
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the report to a file instead of stdout.",
    )
    parser.add_argument(
        "--write-csv-dir",
        type=Path,
        help="Write per-table CSV files to this directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report()
    rendered = _as_markdown(report) if args.format == "markdown" else _as_json(report)
    if args.write_csv_dir:
        write_csv_tables(report, args.write_csv_dir)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
