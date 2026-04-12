"""Check remaining balance associated with OpenRouter API key."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

key_response = requests.get(
    "https://openrouter.ai/api/v1/key",
    headers={"Authorization": f"Bearer {API_KEY}"},
    timeout=30,
)
key_response.raise_for_status()
key_data = key_response.json().get("data", {})

if key_data.get("limit"):
    limit_total = float(key_data.get("limit"))
    limit_remaining = float(key_data.get("limit_remaining"))
    limit_usage = float(key_data.get("usage"))
    limit_reset = key_data.get("limit_reset") or "monthly"
    usage_field = {
        "daily": "usage_daily",
        "weekly": "usage_weekly",
        "monthly": "usage_monthly",
    }.get(limit_reset, "usage")
    usage_against_limit = float(key_data.get(usage_field) or 0)
    print(
        "OpenRouter key limits: "
        f"limit=${limit_total:.2f}, "
        f"used_total=${limit_usage:.2f}, "
        f"used_against_limit=${usage_against_limit:.2f}, "
        f"reset={limit_reset}, "
        f"remaining=${limit_remaining:.2f}"
    )
else:
    print("There's no OpenRouter key limit")
