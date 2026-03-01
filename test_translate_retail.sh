## DOMAIN 2: RETAIL
uv run utils/db_analyze_flatten.py data/tau2/domains/retail/db.json --detail

## v1: flatten users.name, users.address, users.saved_items, orders.items
# uv run utils/db_json_to_excel.py --input data/tau2/domains/retail/db.json \
#   --output data/excel_database/retail_db.xlsx \
#   --flatten users.name \
#   --flatten users.address \
#   --flatten users.saved_items \
#   --flatten orders.items \
#   --overwrite -v

# uv run utils/db_json_to_excel.py \
#     -i data/tau2/domains/retail/db.json \
#     -o data/excel_database/retail_db.xlsx \
#   --flatten users.name \
#   --flatten users.address \
#   --flatten users.saved_items \
#   --flatten orders.items \
#   --flatten reservations.payment_history \
#   --overwrite -v