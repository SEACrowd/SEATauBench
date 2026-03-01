## DOMAIN 1: AIRLINE
# uv run utils/db_analyze_flatten.py data/tau2/domains/airline/db.json --detail

## v1: flatten users.name, users.address, users.saved_passengers, reservations.passengers
# uv run utils/db_json_to_excel.py --input data/tau2/domains/airline/db.json \
#   --output data/excel_database/airline_db.xlsx \
#   --flatten users.name \
#   --flatten users.address \
#   --flatten users.saved_passengers \
#   --flatten reservations.passengers \
#   --overwrite -v

uv run utils/db_json_to_excel.py \
    -i data/tau2/domains/airline/db.json \
    -o data/excel_database/airline_db.xlsx \
  --flatten users.name \
  --flatten users.address \
  --flatten users.saved_passengers \
  --flatten reservations.flights \
  --flatten reservations.passengers \
  --flatten reservations.payment_history \
  --overwrite -v