#!/usr/bin/env bash
# Step 1 of the mock domain translation pipeline.
#
# Converts db.json → db.xlsx.
# No nested columns require flattening in this domain — all fields are scalars.
# The resulting Excel is ready to be sent directly to translators.
#
# Translatable columns (edit values in-place per language):
#   tasks  : title, description
#   users  : name
#
# After this step, upload db.xlsx to each language translator and place
# the returned files under:
#   data/tau2/domains/mock/translated/<Language>/db.xlsx
#
# Then run mock_translate_2.sh to complete the pipeline.
#
# Usage:
#   bash scripts/mock_translate.sh

set -euo pipefail

DOMAIN_DIR="data/tau2/domains/mock"
ORIGINAL="$DOMAIN_DIR/db.json"
XLSX="$DOMAIN_DIR/db.xlsx"

# ── step 1: json → excel (no flatten needed) ──────────────────────────────────
echo "━━━ Step 1: db.json → db.xlsx ━━━"
uv run utils/db_json_to_excel.py \
    -i "$ORIGINAL" \
    -o "$XLSX" \
    --overwrite -v

echo ""
echo "Done: $XLSX"
echo ""
echo "Next: translate db.xlsx for each language and place results under:"
echo "  $DOMAIN_DIR/translated/Chinese/db.xlsx"
echo "  $DOMAIN_DIR/translated/Indonesian/db.xlsx"
echo "  $DOMAIN_DIR/translated/Thai/db.xlsx"
echo "  $DOMAIN_DIR/translated/Vietnamese/db.xlsx"
echo ""
echo "Then run: bash scripts/mock_translate_2.sh"
