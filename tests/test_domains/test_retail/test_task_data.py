import json
from pathlib import Path

RETAIL_DATA_DIR = Path("data/tau2/domains/retail")


def test_retail_task_product_detail_actions_reference_existing_products() -> None:
    db = json.loads((RETAIL_DATA_DIR / "db.json").read_text(encoding="utf-8"))
    tasks = json.loads((RETAIL_DATA_DIR / "tasks.json").read_text(encoding="utf-8"))

    product_ids = set(db["products"])
    missing_product_actions = []
    for task in tasks:
        actions = task.get("evaluation_criteria", {}).get("actions") or []
        for action in actions:
            if action["name"] != "get_product_details":
                continue
            product_id = action["arguments"]["product_id"]
            if product_id not in product_ids:
                missing_product_actions.append((task["id"], action["action_id"], product_id))

    assert missing_product_actions == []
