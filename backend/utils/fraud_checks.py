from datetime import datetime, date
from typing import List, Tuple
import re


def check_duplicate_invoice(invoice_number: str, existing_invoices: list) -> Tuple[bool, str]:
    """Check if invoice number already exists"""
    if not invoice_number:
        return False, ""
    for inv in existing_invoices:
        if inv.invoice_number and inv.invoice_number.lower() == invoice_number.lower():
            return True, f"Invoice number '{invoice_number}' has already been submitted."
    return False, ""


def check_invoice_age(invoice_date_str: str) -> Tuple[bool, str]:
    """Check if invoice is older than 15 days"""
    if not invoice_date_str:
        return True, "Invoice date is missing. Cannot validate age."
    try:
        # Handle multiple date formats
        for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%d %b %Y", "%B %d, %Y"]:
            try:
                invoice_date = datetime.strptime(invoice_date_str.strip(), fmt).date()
                break
            except ValueError:
                continue
        else:
            return False, ""  # Can't parse date, skip check

        today = date.today()
        delta = (today - invoice_date).days

        if delta > 15:
            return True, f"Invoice dated {invoice_date_str} is {delta} days old. Only invoices within 15 days are accepted."
        if delta < 0:
            return True, f"Invoice date {invoice_date_str} is in the future. Please check the date."
        return False, ""
    except Exception:
        return False, ""


def check_gst_number_present(gst_number: str) -> Tuple[bool, str]:
    """Check if GST number is present"""
    if not gst_number or gst_number.strip() == "":
        return True, "GST number is missing. Please upload a valid GST invoice."
    return False, ""


def check_gst_number_format(gst_number: str) -> Tuple[bool, str]:
    """Validate Indian GST number format: 15 characters alphanumeric"""
    if not gst_number:
        return False, ""
    # Indian GST format: 2 digits + 10 char PAN + 1 digit + Z + 1 char
    gst_pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    if not re.match(gst_pattern, gst_number.upper().strip()):
        return True, f"GST number '{gst_number}' format appears invalid."
    return False, ""


def check_bill_amount_valid(bill_amount: float) -> Tuple[bool, str]:
    """Check if bill amount is valid"""
    if bill_amount is None or bill_amount <= 0:
        return True, "Bill amount is missing or invalid."
    if bill_amount > 500000:
        return True, f"Bill amount ₹{bill_amount:,.2f} exceeds the maximum limit of ₹5,00,000."
    return False, ""


def run_all_fraud_checks(
    invoice_data: dict,
    existing_invoices: list
) -> dict:
    """
    Run all 4 fraud checks and return combined result
    """
    fraud_reasons = []
    is_fraudulent = False

    # Check 1: Duplicate invoice number
    dup, reason = check_duplicate_invoice(
        invoice_data.get("invoice_number", ""),
        existing_invoices
    )
    if dup:
        is_fraudulent = True
        fraud_reasons.append(reason)

    # Check 2: Invoice older than 15 days
    old, reason = check_invoice_age(invoice_data.get("invoice_date", ""))
    if old:
        is_fraudulent = True
        fraud_reasons.append(reason)

    # Check 3: GST number missing
    no_gst, reason = check_gst_number_present(invoice_data.get("gst_number", ""))
    if no_gst:
        is_fraudulent = True
        fraud_reasons.append(reason)

    # Check 4: Bill amount valid
    bad_amount, reason = check_bill_amount_valid(invoice_data.get("bill_amount", 0))
    if bad_amount:
        is_fraudulent = True
        fraud_reasons.append(reason)

    return {
        "is_fraudulent": is_fraudulent,
        "reasons": fraud_reasons
    }
