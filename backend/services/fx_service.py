from datetime import datetime
from functools import lru_cache

import requests


FX_SOURCES = [
    "https://open.er-api.com/v6/latest/USD",
    "https://api.frankfurter.app/latest?from=USD&to=INR",
]


@lru_cache(maxsize=8)
def get_usd_to_inr_rate() -> dict:
    last_error = None

    for url in FX_SOURCES:
        try:
            response = requests.get(
                url,
                timeout=8,
                headers={"User-Agent": "Mozilla/5.0 (compatible; NessExpense/1.0)"},
            )
            response.raise_for_status()
            payload = response.json()

            if "rates" in payload and payload["rates"].get("INR"):
                return {
                    "rate": float(payload["rates"]["INR"]),
                    "date": payload.get("date") or datetime.utcnow().strftime("%Y-%m-%d"),
                    "source": url,
                }

            if payload.get("result") == "success" and payload.get("rates", {}).get("INR"):
                return {
                    "rate": float(payload["rates"]["INR"]),
                    "date": payload.get("time_last_update_utc", ""),
                    "source": url,
                }
        except Exception as exc:
            last_error = exc

    raise RuntimeError(f"Unable to fetch USD to INR exchange rate: {last_error}")
