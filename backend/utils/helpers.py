from datetime import datetime
import uuid
import re


def generate_expense_id() -> str:
    """Generate unique expense ID: EXP-20260324-a3f9c1"""
    date_str = datetime.utcnow().strftime("%Y%m%d")
    unique_part = str(uuid.uuid4()).replace("-", "")[:6]
    return f"EXP-{date_str}-{unique_part}"


def get_today_str() -> str:
    """Get today's date as string YYYY-MM-DD"""
    return datetime.utcnow().strftime("%Y-%m-%d")


def format_currency(amount: float) -> str:
    """Format amount as Indian currency"""
    if amount is None:
        return "₹0.00"
    return f"₹{amount:,.2f}"


def get_approval_level(bill_amount: float) -> str:
    """Determine approval level based on amount"""
    if bill_amount < SELF_APPROVAL_LIMIT:
        return "Self"
    return "Dual"


def get_initial_approval_status(bill_amount: float) -> str:
    """Get initial approval status based on amount"""
    if bill_amount < SELF_APPROVAL_LIMIT:
        return "Self-Approved"
    return "Awaiting Manager Approval"


def build_expense_table_markdown(extracted: dict) -> str:
    """Build a markdown table from extracted invoice data"""
    rows = [
        ("Vendor Name", extracted.get("vendor_name", "—")),
        ("Invoice Number", extracted.get("invoice_number", "—")),
        ("Invoice Date", extracted.get("invoice_date", "—")),
        ("Bill Amount", format_currency(extracted.get("bill_amount", 0))),
        ("GST Number", extracted.get("gst_number", "—")),
        ("GST Amount", format_currency(extracted.get("gst_amount", 0))),
        ("Category", extracted.get("expense_category", "—")),
    ]

    table = "| Field | Value |\n|---|---|\n"
    for field, value in rows:
        table += f"| {field} | {value} |\n"
    return table


def detect_media_type(filename: str) -> str:
    """Detect media type from filename"""
    ext = filename.lower().split(".")[-1]
    mapping = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "pdf": "application/pdf",
    }
    return mapping.get(ext, "image/jpeg")
SELF_APPROVAL_LIMIT = 100.0
