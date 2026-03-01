#!/usr/bin/env bash
# Step 1 of the retail domain translation pipeline.
#
# Converts db.json → db.xlsx with flattened nested columns,
# ready to be sent to translators.
#
# After this step, upload db.xlsx to each language translator and place
# the returned files under:
#   data/tau2/domains/retail/translated/<Language>/db.xlsx
#
# Then run retail_translate_2.sh to complete the pipeline.
#
# Usage:
#   bash scripts/retail_translate.sh

set -euo pipefail

DOMAIN_DIR="data/tau2/domains/retail"
ORIGINAL="$DOMAIN_DIR/db.json"
XLSX="$DOMAIN_DIR/db.xlsx"

# ── step 1: json → excel (flatten) ────────────────────────────────────────────
echo "━━━ Step 1: db.json → db.xlsx (flatten) ━━━"
uv run utils/db_json_to_excel.py \
    -i "$ORIGINAL" \
    -o "$XLSX" \
    --flatten users.name \
    --flatten users.address \
    --flatten orders.address \
    --flatten orders.fulfillments \
    --flatten orders.payment_history \
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
echo "Then run: bash scripts/retail_translate_2.sh"
