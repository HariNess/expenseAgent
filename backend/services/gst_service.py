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
INDIAN_STATE_CODES = [f"{code:02d}" for code in range(1, 39)]
OCR_DIGIT_VARIANTS = {
    "0": ["0", "3", "8", "9", "6"],
    "1": ["1", "7"],
    "2": ["2", "7", "3"],
    "3": ["3", "8", "0", "2"],
    "4": ["4", "9"],
    "5": ["5", "6"],
    "6": ["6", "8", "0", "5"],
    "7": ["7", "1", "2", "3"],
    "8": ["8", "3", "0", "6", "9"],
    "9": ["9", "8", "4", "0"],
}


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


def resolve_gst_number(gst_number: str) -> dict:
    normalized = (gst_number or "").strip().upper()
    if not normalized:
        return {"gst_number": normalized, "lookup": lookup_gst_status(normalized)}

    direct_lookup = lookup_gst_status(normalized)
    if direct_lookup.get("is_active"):
        return {"gst_number": normalized, "lookup": direct_lookup}

    # OCR often misreads the GST state code prefix. Try only OCR-plausible
    # state-code alternatives while preserving the rest of the GSTIN.
    if len(normalized) == 15:
        suffix = normalized[2:]
        first_digit_options = OCR_DIGIT_VARIANTS.get(normalized[0], [normalized[0]])
        second_digit_options = OCR_DIGIT_VARIANTS.get(normalized[1], [normalized[1]])
        candidate_state_codes = []

        for first_digit in first_digit_options:
            for second_digit in second_digit_options:
                candidate_state = f"{first_digit}{second_digit}"
                if candidate_state in INDIAN_STATE_CODES and candidate_state not in candidate_state_codes:
                    candidate_state_codes.append(candidate_state)

        for state_code in candidate_state_codes:
            candidate = f"{state_code}{suffix}"
            if candidate == normalized:
                continue
            candidate_lookup = lookup_gst_status(candidate)
            if candidate_lookup.get("is_active"):
                candidate_lookup["reason"] = (
                    f"Corrected GST number from '{normalized}' to '{candidate}' after live verification."
                )
                return {"gst_number": candidate, "lookup": candidate_lookup}

    return {"gst_number": normalized, "lookup": direct_lookup}
