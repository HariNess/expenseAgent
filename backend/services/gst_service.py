import os
import re
from functools import lru_cache

import requests


GST_LOOKUP_TIMEOUT = float(os.getenv("GST_LOOKUP_TIMEOUT", "8"))
GST_LOOKUP_URL = "https://razorpay.com/gst-number-search/{gst_number}"
GST_DATA_PATTERN = re.compile(
    r'"gstin":"(?P<gstin>[A-Z0-9]{15})".*?"status":"(?P<status>[^"]+)"',
    re.DOTALL,
)


@lru_cache(maxsize=256)
def lookup_gst_status(gst_number: str) -> dict:
    normalized = (gst_number or "").strip().upper()
    if not normalized:
        return {
            "checked": False,
            "found": False,
            "status": None,
            "is_active": False,
            "reason": "GST number is missing.",
        }

    response = requests.get(
        GST_LOOKUP_URL.format(gst_number=normalized),
        timeout=GST_LOOKUP_TIMEOUT,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; NessExpense/1.0; +https://ness.com)",
        },
    )
    response.raise_for_status()

    match = GST_DATA_PATTERN.search(response.text)
    if not match:
        return {
            "checked": True,
            "found": False,
            "status": None,
            "is_active": False,
            "reason": f"GST number '{normalized}' could not be verified on the GST lookup page.",
        }

    status = (match.group("status") or "").strip()
    is_active = status.lower() == "active"
    return {
        "checked": True,
        "found": True,
        "status": status,
        "is_active": is_active,
        "reason": "" if is_active else f"GST number '{normalized}' is not active.",
    }
