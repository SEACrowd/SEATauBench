#!/usr/bin/env bash
# End-to-end translation pipeline for the airline domain.
#
# Steps:
#   1. [domain_translate.sh]db.json        → db.xlsx          (flatten nested columns for translator)
#   2. [domain_translate_2.sh] db.xlsx + translated/<lang>/db.xlsx → db_merged.xlsx  (merge translations)
#   3. [domain_translate_2.sh] db_merged.xlsx → db_{id}.json     (one JSON per language)
#   4. [domain_translate_2.sh] Verify structure of each translated JSON against original db.json
#
# Prerequisites:
#   Translated Excel files must already exist under translated/<lang>/db.xlsx
#   (Chinese, Indonesian, Thai, Vietnamese)
#
# Usage:
#   bash scripts/airline_translate_2.sh

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

# ── prerequisites check ────────────────────────────────────────────────────────
echo "━━━ Checking prerequisites ━━━"
missing=0
if [[ ! -f "$ORIGINAL" ]]; then
    echo "[ERROR] original not found: $ORIGINAL"
    missing=1
fi
if [[ ! -d "$TRANSLATED_ROOT" ]]; then
    echo "[ERROR] translated root not found: $TRANSLATED_ROOT"
    echo "        Expected layout:"
    for LANG in "${!LANG_ID[@]}"; do
        echo "          $TRANSLATED_ROOT/$LANG/db.xlsx"
    done
    missing=1
else
    for LANG in "${!LANG_ID[@]}"; do
        EXPECTED="$TRANSLATED_ROOT/$LANG/db.xlsx"
        if [[ ! -f "$EXPECTED" ]]; then
            echo "[ERROR] missing translated file: $EXPECTED"
            missing=1
        fi
    done
fi
if [[ $missing -eq 1 ]]; then
    exit 1
fi
echo "[OK] all prerequisites satisfied"
echo ""

# ── step 2: merge translations → db_merged.xlsx ───────────────────────────────
echo ""
echo "━━━ Step 2: merge translations → db_merged.xlsx ━━━"
uv run utils/db_excel_merge_translations.py \
    -i "$XLSX" \
    --translated-root "$TRANSLATED_ROOT" \
    -o "$MERGED" \
    --merge users.name \
    --merge users.address \
    --merge users.saved_passengers \
    --merge reservations.passengers \
    --keep  users.address.country \
    --keep  users.address.state \
    --keep  users.address.zip \
    --keep  users.saved_passengers.dob \
    --keep  reservations.passengers.dob \
    --overwrite -v

# ── step 3: db_merged.xlsx → db_{id}.json per language ────────────────────────
echo ""
echo "━━━ Step 3: db_merged.xlsx → db_{id}.json ━━━"
for LANG in "${!LANG_ID[@]}"; do
    ID="${LANG_ID[$LANG]}"
    OUT="$DOMAIN_DIR/db_${ID}.json"
    echo "[$ID] $LANG → $OUT"
    uv run utils/db_excel_to_json.py \
        -i "$MERGED" \
        -o "$OUT" \
        --language "$LANG" \
        --overwrite
done

echo ""
echo "Output files:"
for LANG in "${!LANG_ID[@]}"; do
    echo "  $DOMAIN_DIR/db_${LANG_ID[$LANG]}.json"
done

# ── step 4: verify structure ───────────────────────────────────────────────────
echo ""
echo "━━━ Step 4: verify structure ━━━"
TRANSLATED_PATHS=()
for LANG in "${!LANG_ID[@]}"; do
    TRANSLATED_PATHS+=("$DOMAIN_DIR/db_${LANG_ID[$LANG]}.json")
done

uv run utils/db_verify_structure.py \
    --original "$ORIGINAL" \
    --translated "${TRANSLATED_PATHS[@]}"
