"""
Fraud Detection Agent
Runs rule-based and AI-powered fraud checks on submitted invoices
"""
from backend.utils.fraud_checks import run_all_fraud_checks
from backend.services.claude_service import analyze_fraud_with_ai


def run_fraud_detection(
    invoice_data: dict,
    existing_invoices: list,
    use_ai: bool = True,
    include_external_gst_check: bool = False,
) -> dict:
    """
    Run complete fraud detection pipeline.
    1. Rule-based checks (fast)
    2. AI-powered analysis (deeper)
    Returns combined result.
    """

    # Step 1: Rule-based checks
    rule_result = run_all_fraud_checks(
        invoice_data,
        existing_invoices,
        include_external_gst_check=include_external_gst_check,
    )

    # If rule checks already flagged — return immediately, no need for AI
    if rule_result["is_fraudulent"]:
        return {
            "is_fraudulent": True,
            "reasons": rule_result["reasons"],
            "detection_type": "rule_based"
        }

    # Step 2: AI-powered analysis for deeper checks
    if use_ai and existing_invoices:
        try:
            recent = [
                {
                    "vendor_name": inv.vendor_name,
                    "bill_amount": inv.bill_amount,
                    "invoice_date": inv.invoice_date,
                    "expense_category": inv.expense_category
                }
                for inv in existing_invoices[-5:]  # last 5 invoices
            ]
            ai_result = analyze_fraud_with_ai(invoice_data, recent)

            if ai_result.get("ai_fraud_detected") and ai_result.get("confidence", 0) > 0.75:
                return {
                    "is_fraudulent": True,
                    "reasons": ai_result.get("reasons", ["Suspicious patterns detected by AI analysis."]),
                    "detection_type": "ai_powered"
                }
        except Exception:
            # AI check failed — don't block submission, just skip
            pass

    return {
        "is_fraudulent": False,
        "reasons": [],
        "detection_type": "passed"
    }


def format_fraud_message(fraud_result: dict) -> str:
    """Format fraud result into user-friendly message"""
    if not fraud_result["is_fraudulent"]:
        return ""

    reasons = fraud_result["reasons"]
    if len(reasons) == 1:
        return (
            f"I found one thing to fix before we can continue:\n\n"
            f"• {reasons[0]}\n\n"
            f"Please update the invoice and upload it again."
        )

    reason_list = "\n".join([f"• {r}" for r in reasons])
    return (
        f"I found a few things to fix before we can continue:\n\n"
        f"{reason_list}\n\n"
        f"Please review them and upload the invoice again."
    )
