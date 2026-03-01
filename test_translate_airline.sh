## DOMAIN 1: AIRLINE
# uv run utils/db_analyze_flatten.py data/tau2/domains/airline/db.json --detail

## v1: flatten users.name, users.address, users.saved_passengers, reservations.passengers
uv run utils/db_json_to_excel.py --input data/tau2/domains/airline/db.json \
  --output data/tau2/domains/airline/db.xlsx \
  --flatten users.name \
  --flatten users.address \
  --flatten users.saved_passengers \
  --flatten reservations.passengers \
  --overwrite -v

# bug: reservations.flights is flattened


# uv run utils/db_excel_merge_translations.py \
#     -i data/tau2/domains/airline/db.xlsx \
#     --translated-root data/tau2/domains/airline/translated \
#     -o data/tau2/domains/airline/db_merged.xlsx \
#     --merge users.name \
#     --merge users.address \
#     --merge users.saved_passengers \
#     --merge reservations.passengers \
#     --keep  users.address.zip \
#     --keep  users.saved_passengers.dob \
#     --keep  reservations.passengers.dob \
#     --overwrite -v

## v2: flatten users.name, users.address, users.saved_passengers, reservations.flights, reservations.passengers, reservations.payment_history
# uv run utils/db_json_to_excel.py \
#     -i data/tau2/domains/airline/db.json \
#     -o data/tau2/domains/airline/db.xlsx \
#   --flatten users.name \
#   --flatten users.address \
#   --flatten users.saved_passengers \
#   --flatten reservations.flights \
#   --flatten reservations.passengers \
#   --flatten reservations.payment_history \
#   --overwrite -v

# uv run utils/db_excel_merge_translations.py \
#     -i data/tau2/domains/airline/db.xlsx \
#     --translated-root data/tau2/domains/airline/translated \
#     -o data/tau2/domains/airline/db_merged.xlsx \
#     --merge users.name \
#     --merge users.address \
#     --merge users.saved_passengers \
#     --merge reservations.passengers \
#     --keep  users.address.country \
#     --keep  users.address.state \
#     --keep  users.address.zip \
#     --keep  users.saved_passengers.dob \
#     --keep  reservations.passengers.dob \
#     --overwrite -v