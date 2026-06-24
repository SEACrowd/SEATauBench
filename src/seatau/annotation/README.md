# SEA-TAU annotation pipeline

Round-trip pipeline that turns translated artefacts into reviewer-friendly
Excel workbooks and back. The reviewer's edits land in
`data/tau2/domains/{domain}/{lang}_loc/`, which the tau2 runtime loads when
the `localized` experiment runs.

```
data/tau2/domains/{domain}/{lang}/  ─export──▶  annotation_{lang}.xlsx
                                                       │
                                       (reviewer fills name.{lang}.final)
                                                       ▼
data/tau2/domains/{domain}/{lang}_loc/  ◀─import──  annotation_{lang}.xlsx
```

## Module layout

```
src/seatau/annotation/
  __init__.py                      # exports import_reviewed
  __main__.py                      # `python -m seatau.annotation`
  cli.py                           # argparse dispatcher (subcommands: export, import)
  addresses.py                     # parse/format "filename::body" rows; file_kind helper
  markdown.py                      # ATX-heading split + rejoin (shared)
  python_tools.py                  # AST-based docstring extraction (shared)
  manifests.py                     # annotation .yaml + translation_manifest.json I/O
  validators.py                    # empty-final, address coverage, canonical tokens, drift
  export.py                        # NEW canonical exporter (artefact -> workbook)
  import_reviewed.py               # workbook -> {lang}_loc/ files (per-kind dispatch)
  export_annotation_sheet.py       # back-compat shim → export.py
  README.md                        # this file
```

`db_verify_structure.py` (translated-DB structural diff) moved to
[`../translation/db_verify_structure.py`](../translation/db_verify_structure.py)
since it verifies translation outputs, not annotation workbooks.

## Workbook layout (per-language)

`annotation_{lang}.xlsx` has one sheet per artefact, plus 2 metadata sheets:

| Sheet                            | Source artefact                                                   |
| -------------------------------- | ----------------------------------------------------------------- |
| `Annotation guideline`           | reviewer instructions (skipped on import)                         |
| `Examples`                       | sample rows (skipped on import)                                   |
| `airline_data_model`             | `src/tau2/domains/airline/data_model.py`                          |
| `airline_db`                     | `data/tau2/domains/airline/db.json`                               |
| `airline_policy`                 | `data/tau2/domains/airline/policy.md`                             |
| `airline_tasks`                  | `data/tau2/domains/airline/tasks.json`                            |
| `airline_tools`                  | `src/tau2/domains/airline/tools.py`                               |
| `retail_*`                       | mirrors airline                                                   |
| `telecom_data_model`             | `src/tau2/domains/telecom/data_model.py`                          |
| `telecom_user_data_model`        | `src/tau2/domains/telecom/user_data_model.py`                     |
| `telecom_db`                     | `data/tau2/domains/telecom/db.toml`                               |
| `telecom_user_db`                | `data/tau2/domains/telecom/user_db.toml` (often empty — no text)  |
| `telecom_main_policy`            | `data/tau2/domains/telecom/main_policy.md`                        |
| `telecom_main_policy_solo`       | `data/tau2/domains/telecom/main_policy_solo.md`                   |
| `telecom_tech_support_manual`    | `data/tau2/domains/telecom/tech_support_manual.md`                |
| `telecom_tech_support_workflow`  | `data/tau2/domains/telecom/tech_support_workflow.md`              |
| `telecom_tech_support_workflow_solo` | `data/tau2/domains/telecom/tech_support_workflow_solo.md`     |
| `telecom_tasks`                  | `data/tau2/domains/telecom/tasks.json`                            |
| `telecom_tools`                  | `src/tau2/domains/telecom/tools.py`                               |
| `telecom_user_tools`             | `src/tau2/domains/telecom/user_tools.py`                          |

Each artefact sheet has six columns:

| Column                  | Purpose                                                  |
| ----------------------- | -------------------------------------------------------- |
| `address`               | English source locator, e.g. `db.json::products/9523456873/name` |
| `name`                  | English source text                                      |
| `address.{lang}`        | Locator in the translated artefact                       |
| `name.{lang}`           | Machine-translation baseline                             |
| `name.{lang}.final`     | **Reviewer-edited final value (this is what import reads)** |
| `review_notes.{lang}`   | Free-text reviewer notes                                 |

## Address taxonomy

| Source kind   | Address shape                                                |
| ------------- | ------------------------------------------------------------ |
| markdown      | `policy.md::001_retail-agent-policy_1` (ordinal slug)        |
| JSON          | `db.json::products/9523456873/name` (tuple-path)             |
| TOML          | `db.toml::plans/0/name` (tuple-path)                         |
| python tools  | `tools.py::cancel_pending_order` (function name)             |
| python schema | `data_model.py::models/User/fields/name/description` (tuple-path inside JSON-shaped schema) |

`addresses.parse(addr_str)` returns an `Address(filename, body)`. For
markdown, see `markdown.split` / `markdown.rejoin`.

## Commands

### Export — workbook from current artefacts

```bash
# Preferred: unified CLI
uv run python -m seatau.annotation export \
  --domains retail telecom --lang-id vi \
  -o data/seatau/annotation/annotation_vi.xlsx \
  --reviewer alice --round-id r1

# Equivalent (direct module access)
uv run python -m seatau.annotation.export ...

# Legacy (back-compat shim, still works)
uv run python -m seatau.annotation.export_annotation_sheet ...
```

Other useful flags: `--overwrite`, `--annotation-metadata-dir`,
`--data-domains-root`, `--src-domains-root`. Run with `-h` for the
full list.

The exporter writes a `*.manifest.yaml` to `data/seatau/annotation/`
with reviewer ID, round ID, language, git commit, and per-sheet row
counts; the importer reads this back to detect drift.

### Import — workbook back into `{lang}_loc/`

```bash
# Production: reject empty name.{lang}.final (forces an explicit decision)
uv run python -m seatau.annotation import \
  --workbook data/seatau/annotation/annotation_vi.xlsx --lang vi

# Identity / smoke test: fall back to name.{lang} when .final is empty
uv run python -m seatau.annotation import \
  --workbook data/seatau/annotation/annotation_vi.xlsx --lang vi \
  --allow-machine-fallback

# Skip a validator (use sparingly)
uv run python -m seatau.annotation import \
  --workbook ... --lang vi \
  --no-canonical-check    # don't verify ID-shaped tokens survive
  --no-manifest-check     # don't compare workbook git_commit to HEAD
```

The CLI exits non-zero if any sheet has errors (default canonical-token
violations or empty `.final` rows under production mode).

For each artefact sheet, the importer:

1. Parses the first row's `address` to locate the English source.
2. Reads `name.{lang}.final` per row, falling back to `name.{lang}` when
   `.final` is empty (current default; see "Production gaps" below).
3. Dispatches by source file kind:
   - **markdown**: split source by ATX heading, replace each section's body
     by `section_id`, rejoin → write `<name>.md`.
   - **JSON**: re-extract segments from English source, build
     `{segment_id: final}` map, run `apply_json_updates` → write `<name>.json`.
   - **TOML**: same as JSON, with `apply_toml_updates` → write `<name>.toml`.
   - **python tools**: write a flat `{function_name: docstring}` JSON
     to `{lang}_loc/<stem>.json` (matches the tau2 loader's expected shape).
   - **python schema**: apply tuple-path updates to the baseline
     `{lang}/data_model.json` (the schema source-of-truth is `.py` but the
     runtime reads JSON) → write `{lang}_loc/<stem>.json`. Requires the
     baseline machine translation to exist; if missing, run
     `seatau.translation.cli ... --components schema` first.
4. Writes to `data/tau2/domains/{domain}/{lang}_loc/<file>` preserving
   filename + format + structure.

Output paths exactly mirror the source layout, so the existing tau2
runtime loader picks them up under `--seatau-experiment localized` with
no code changes:

```
data/tau2/domains/retail/vi_loc/
  data_model.json   db.json   policy.md   tasks.json   tools.json

data/tau2/domains/telecom/vi_loc/
  data_model.json   user_data_model.json
  db.toml           user_db.toml
  main_policy.md    main_policy_solo.md
  tech_support_manual.md
  tech_support_workflow.md   tech_support_workflow_solo.md
  tasks.json        tools.json   user_tools.json
```

### Verify — DB structural integrity

The DB structural-diff utility moved to the translation package since
it verifies translation outputs:

```bash
uv run python -m seatau.translation.db_verify_structure \
  --original data/tau2/domains/retail/db.json \
  --translated data/tau2/domains/retail/vi/db.json
```

## Round-trip verification

The dispatcher has been verified end-to-end on real artefacts (see
`experiments/REPORT.md` §3b for the executed test):

- **Identity round-trip** (export → copy `name.{lang}` → `name.{lang}.final`
  → import): 7/16 artefacts byte-identical to the `{lang}/` baseline;
  remaining 9 are structurally identical (same JSON shape, same TOML keys,
  same heading count) with cosmetic whitespace differences.
- **Runtime load**: `retail/vi_loc/` artefacts load successfully under
  `tau2 run --seatau-experiment localized --lang-id vi --domain retail`;
  agent receives Vietnamese policy, tool descriptions, and DB values.

## Production behaviour (now implemented)

What was once on the TODO list and is now wired in:

- **Manifest writing** — importer writes `{lang}_loc/translation_manifest.json`
  with `pipeline="human-localized"`, source-file SHAs, reviewer/round
  metadata pulled from the workbook's annotation manifest. The runtime's
  stale-warning machinery now treats `{lang}_loc/` like `{lang}/`.
- **Empty-final policy** — by default, rows with empty `name.{lang}.final`
  cause the sheet to fail validation and the file is **not** written.
  Pass `--allow-machine-fallback` to fall back to `name.{lang}`.
- **Canonical-token validator** — for every written file, ID-shaped
  tokens from the English source (`#W\d+`, `gift_card_\d+`,
  `credit_card_\d+`, `P\d{4,}`) must appear in the localized output.
  Disable with `--no-canonical-check`.
- **Manifest drift check** — `git_commit` in the workbook's
  `*.manifest.yaml` is compared to current `HEAD`; mismatches are
  reported as warnings. Disable with `--no-manifest-check`.
- **`tools.json` filtering** — importer filters by the public-tool
  set defined in `python_tools.extract_tool_docstrings`, matching the
  translation pipeline's view.
- **Empty-sheet handling** — sheets with 0 rows (e.g. `telecom_user_db`)
  copy the English source verbatim into `{lang}_loc/` so the directory
  is a complete overlay.

## Programmatic API

```python
from pathlib import Path
from seatau.annotation import import_reviewed

report = import_reviewed(
    workbook=Path("data/seatau/annotation/annotation_vi.xlsx"),
    lang="vi",
    allow_machine_fallback=False,    # default: reject empty .final
    require_canonical_tokens=True,   # default: verify IDs survive
    require_manifest=True,           # default: cross-check git_commit
)
print(report.summary())
# report.written:  list[(sheet_name, output_path, row_count)]
# report.skipped:  list[str]
# report.errors:   list[str]   — non-empty means CLI exits 1
# report.warnings: list[str]
# report.manifest_path: Path   — last per-domain translation_manifest.json
```

## Cross-references

- Round-trip design rationale: `experiments/REPORT.md` §3a, §3b.
- Translation pipeline (the producer of `{lang}/` baselines):
  [`../translation/README.md`](../translation/README.md).
- How the runtime consumes `{lang}_loc/`:
  [`../README.md#how---lang-id-flows-through-the-runtime`](../README.md).
