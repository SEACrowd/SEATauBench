# SEA-TAU Annotation Review

This package exports translated SEA-TAU artifacts to reviewer-friendly Excel
workbooks and imports reviewer corrections back into the translated asset
directory.

```text
data/tau2/domains/{domain}/{lang}/  --export-->  annotation_{lang}.xlsx
                                                     |
                                 reviewer fills name.{lang}.final
                                                     v
data/tau2/domains/{domain}/{lang}/  <--import--  annotation_{lang}.xlsx
```

The workflow reviews machine-translated assets for `l2_domain`; it does not
create or load `{lang}_loc` localization overlays.

## Commands

Export a workbook:

```bash
uv run python -m seatau.annotation export \
  --domains retail telecom --lang-id vi \
  -o data/seatau/annotations/annotation_vi_r1.xlsx \
  --reviewer alice --round-id r1
```

Import reviewed values:

```bash
uv run python -m seatau.annotation import \
  --workbook data/seatau/annotations/annotation_vi_r1.xlsx --lang vi
```

By default, import rejects rows with empty `name.{lang}.final`. For smoke tests
or identity round-trips, pass `--allow-machine-fallback` to reuse `name.{lang}`
when the final column is empty.

## Workbook Layout

Each artifact sheet has these columns:

| Column | Purpose |
| --- | --- |
| `address` | English source locator, such as `db.json::products/9523456873/name`. |
| `name` | English source text. |
| `address.{lang}` | Locator in the translated artifact. |
| `name.{lang}` | Machine-translation baseline. |
| `name.{lang}.final` | Reviewer-edited final value read by import. |
| `review_notes.{lang}` | Free-text reviewer notes. |

The workbook also includes `Annotation guideline` and `Examples` metadata sheets,
which are skipped during import.

## Import Behavior

For each artifact sheet, import:

1. Resolves the English source from `address`.
2. Reads reviewer text from `name.{lang}.final`.
3. Rebuilds the corresponding translated asset under
   `data/tau2/domains/{domain}/{lang}/`.
4. Updates `translation_manifest.json` with
   `pipeline="human-reviewed-translation"`, source fingerprints, reviewer, and
   review round metadata.

Markdown, JSON, TOML, Python tool docstrings, and Python schema artifacts are
handled by file-kind-specific writers.

## Validation

Import validates:

- Empty final values unless `--allow-machine-fallback` is set.
- Canonical ID-shaped tokens, unless `--no-canonical-check` is set.
- Manifest drift against the workbook export commit, unless
  `--no-manifest-check` is set.

## Programmatic API

```python
from pathlib import Path
from seatau.annotation import import_reviewed

report = import_reviewed(
    workbook=Path("data/seatau/annotations/annotation_vi_r1.xlsx"),
    lang="vi",
)
print(report.summary())
```
