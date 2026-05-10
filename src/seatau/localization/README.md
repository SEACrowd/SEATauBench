# SEA-TAU localization helpers

Reusable synthetic-data utilities for locale-aware annotation workbooks.
This package replaces the old notebook prototype with importable modules
and a small CLI:

- `seatau.localization.synthetic` generates deterministic fake values per
  language.
- `seatau.localization.workbook` scans and patches annotation workbooks.
- `python -m seatau.localization` exposes `generate`, `scan`, `propagate`,
  and `export` commands.
- `src/seatau/localization/reference_data/` contains reference-only seed
  lists and templates that show how a locale corpus can be structured at
  larger scale. They are not wired into the runtime.

## What this covers

The current workflow targets the value sets that can safely be randomized
in the annotation sheets:

- person names: `name`, `first_name`, `last_name`
- address components: `address1`, `address2`, `city`, `state`, `country`,
  `zip` / `postcode`
- contact info: `email`, `phone`, `phone_number`

The workbook patcher only touches the value-bearing `name*` columns in the
review sheets. Structural `address` columns stay intact.

## Commands

### 1. Generate a reusable fake-value catalog

```bash
uv run python -m seatau.localization generate \
  --lang vi \
  --count 32 \
  -o data/seatau/localization/fakes/vi.json
```

### 2. Inspect which workbook rows will be localized

```bash
uv run python -m seatau.localization scan \
  --lang vi \
  --workbook data/seatau/annotation/annotation_vi.xlsx
```

### 3. Patch an existing annotation workbook in place

```bash
uv run python -m seatau.localization propagate \
  --lang vi \
  --workbook data/seatau/annotation/annotation_vi.xlsx \
  --catalog data/seatau/localization/fakes/vi.json \
  -o data/seatau/annotation/annotation_vi.localized.xlsx
```

### 4. Export the workbook and localize it in one step

```bash
uv run python -m seatau.localization export \
  --domains retail telecom \
  --lang-id vi \
  -o data/seatau/annotation/annotation_vi.localized.xlsx \
  --reviewer alice \
  --round-id r1
```

That command first runs the canonical annotation exporter, then patches
the workbook so the translated text and synthetic names/addresses land in
the same file.

## Notes

- Output is deterministic per language unless you pass `--seed`.
- The generator uses Faker locales appropriate to the target language:
  `th_TH`, `vi_VN`, `id_ID`, `zh_CN`, and `en_PH` for Filipino.
- `en` is intentionally skipped because the notebook and the localized
  workflow only target non-English overlays.
