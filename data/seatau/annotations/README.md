# SEA-TAU Annotation Artifacts

This directory stores reviewer workbooks and manifests for translated SEA-TAU
artifact review.

## Files

- `annotation_*.xlsx` - reviewer workbooks, one per target language
- `annotation_*.manifest.yaml` - export manifests with generation timestamp,
  reviewer metadata, review round, source roots, and workbook provenance

## Notes

- The manifests live in this directory alongside the exported workbooks.
- `language_registry` entries point at `data/seatau/languages.json`.
