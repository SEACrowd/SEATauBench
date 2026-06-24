# SEA-TAU Annotation Artifacts

This directory stores the reviewer workbooks and their manifests for translated
SEA-TAU artifacts.

## Files

- `annotation_*.xlsx` - reviewer workbooks, one per target language
- `annotation_*.manifest.yaml` - export manifests with generation timestamp,
  reviewer metadata, source roots, and workbook provenance

## Notes

- The manifests live in this directory alongside the exported workbooks.
- `language_registry` entries point at `src/seatau/languages.json`.
