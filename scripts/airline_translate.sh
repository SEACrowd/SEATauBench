#!/usr/bin/env bash
# End-to-end translation pipeline for the airline domain.
#
# Steps:
#   1. [domain_translate.sh] db.json        → db.xlsx          (flatten nested columns for translator)
#   2. [domain_translate_2.sh] db.xlsx + translated/<lang>/db.xlsx → db_merged.xlsx  (merge translations)
#   3. [domain_translate_2.sh] db_merged.xlsx → db_{id}.json     (one JSON per language)
#   4. [domain_translate_2.sh] Verify structure of each translated JSON against original db.json
#
# Prerequisites:
#   Translated Excel files must already exist under translated/<lang>/db.xlsx
#   (Chinese, Indonesian, Thai, Vietnamese)
#
# Usage:
#   bash scripts/airline_translate.sh

set -euo pipefail

DOMAIN_DIR="data/tau2/domains/airline"
ORIGINAL="$DOMAIN_DIR/db.json"
XLSX="$DOMAIN_DIR/db.xlsx"
MERGED="$DOMAIN_DIR/db_merged.xlsx"
TRANSLATED_ROOT="$DOMAIN_DIR/translated"

# Map: translated folder name → ISO lang-id
declare -A LANG_ID=(
    [Chinese]=zh
    [Indonesian]=id
    [Thai]=th
    [Vietnamese]=vi
)


# ── step 1: json → excel (flatten) ────────────────────────────────────────────
echo "━━━ Step 1: db.json → db.xlsx (flatten) ━━━"
uv run utils/db_json_to_excel.py \
    -i "$ORIGINAL" \
    -o "$XLSX" \
    --flatten users.name \
    --flatten users.address \
    --flatten users.saved_passengers \
    --flatten reservations.flights \
    --flatten reservations.passengers \
    --flatten reservations.payment_history \
    --overwrite -v

# ── step 1b: translate .xlsx to target languages using Google Translate (https://translate.google.com/?sl=en&tl=th&op=docs)  ────────────────────────────────────────────