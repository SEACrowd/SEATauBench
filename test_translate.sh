## bash

uv run utils/db_json_to_excel.py --input data/tau2/domains/airline/db.json \
  --output data/excel_database/airline_db.xlsx \
  --flatten users.name \
  --flatten users.address \
  --flatten users.saved_passengers \
  --flatten reservations.passengers \
  --overwrite -v