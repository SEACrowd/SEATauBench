# Translation Corpus Stats

This directory is the canonical machine-readable source for the translation
corpus statistics used in `src/seatau/translation/pipeline.md`.

Regenerate the files with:

```bash
uv run python src/seatau/translation/compute_artifact_stats.py \
  --format markdown \
  --write-csv-dir data/seatau/stats
```

Files:

- `coverage.csv`
- `tasks.csv`
- `tool_docstrings.csv`
- `tool_return_messages.csv`
- `policies.csv`
- `schemas.csv`
- `databases.csv`

The CSV layout is intentionally simple so it can be imported into spreadsheet
software or converted into TeX `tabular` rows with minimal cleanup.
