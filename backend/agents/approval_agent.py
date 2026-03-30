"""
Approval Agent
Handles expense approval routing, status updates, and notifications
"""
from sqlalchemy.orm import Session
from backend.models.database import Expense, ApprovalLog, Employee
from backend.services.jira_service import create_jira_task_for_expense
from backend.utils.helpers import get_today_str, format_currency, SELF_APPROVAL_LIMIT


def process_self_approval(db: Session, expense: Expense) -> dict:
    """Handle self-approval for expenses below the self-approval limit."""
    expense.approval_status = "Self-Approved"

    log = ApprovalLog(
        expense_id=expense.expense_id,
        employee_email=expense.employee_email,
        action_by=expense.employee_email,
        action_type="Auto-Approved",
        action_date=get_today_str(),
        comments=f"Auto-approved as amount is below ₹{SELF_APPROVAL_LIMIT:,.0f}",
        approval_stage="Self",
        bill_amount=expense.bill_amount,
        vendor_name=expense.vendor_name
    )
    db.add(log)
    db.commit()

    jira_result = _sync_jira_task(db, expense)

    message = (
        f"Your expense is all set and has been approved automatically.\n\n"
        f"Reference ID: **{expense.expense_id}**\n"
        f"Amount: **{format_currency(expense.bill_amount)}**\n"
        f"Vendor: **{expense.vendor_name}**\n\n"
        f"Because the amount is below **₹{SELF_APPROVAL_LIMIT:,.0f}**, no further approval is needed."
    )
    message = _append_jira_message(message, jira_result)

    return {
        "status": "Self-Approved",
        "message": message,
        "jira": jira_result,
    }


def process_manager_approval(db: Session, expense_id: str, action: str, comments: str, approver_email: str) -> dict:
    """Process manager approval or rejection"""
    expense = db.query(Expense).filter(Expense.expense_id == expense_id).first()
    if not expense:
        return {"error": "Expense not found"}

    log = ApprovalLog(
        expense_id=expense_id,
        employee_email=expense.employee_email,
        action_by=approver_email,
        action_type=action.capitalize(),
        action_date=get_today_str(),
        comments=comments,
        approval_stage="Manager",
        bill_amount=expense.bill_amount,
        vendor_name=expense.vendor_name
    )
    db.add(log)

    if action.lower() == "approve":
        expense.approval_status = "Awaiting HR Approval"
        db.commit()
        return {
            "status": "Awaiting HR Approval",
            "next_approver": expense.hr_email,
            "message": f"Manager approval is complete for **{expense_id}**. I've moved it to HR for the final review."
        }
    else:
        expense.approval_status = "Rejected"
        expense.rejection_reason = comments
        db.commit()
        return {
            "status": "Rejected",
            "message": f"Your manager didn’t approve **{expense_id}**.\n\nReason: {comments or 'No reason was shared.'}"
        }


def process_hr_approval(db: Session, expense_id: str, action: str, comments: str, approver_email: str) -> dict:
    """Process HR approval or rejection"""
    expense = db.query(Expense).filter(Expense.expense_id == expense_id).first()
    if not expense:
        return {"error": "Expense not found"}

    log = ApprovalLog(
        expense_id=expense_id,
        employee_email=expense.employee_email,
        action_by=approver_email,
        action_type=action.capitalize(),
        action_date=get_today_str(),
        comments=comments,
        approval_stage="HR",
        bill_amount=expense.bill_amount,
        vendor_name=expense.vendor_name
    )
    db.add(log)

    if action.lower() == "approve":
        expense.approval_status = "Fully Approved"
        db.commit()
        jira_result = _sync_jira_task(db, expense)
        message = (
            f"Good news, **{expense_id}** is fully approved.\n\n"
            f"Amount: **{format_currency(expense.bill_amount)}**\n"
            f"HR has completed the final review, and reimbursement can be processed next."
        )
        message = _append_jira_message(message, jira_result)
        return {
            "status": "Fully Approved",
            "message": message,
            "jira": jira_result,
        }
    else:
        expense.approval_status = "Rejected"
        expense.rejection_reason = comments
        db.commit()
        return {
            "status": "Rejected",
            "message": f"HR didn’t approve **{expense_id}**.\n\nReason: {comments or 'No reason was shared.'}"
        }


def get_pending_approvals(db: Session, approver_email: str, stage: str) -> list:
    """Get all expenses pending approval for a specific approver"""
    if stage == "manager":
        expenses = db.query(Expense).filter(
            Expense.manager_email == approver_email,
            Expense.approval_status == "Awaiting Manager Approval"
        ).all()
    else:
        expenses = db.query(Expense).filter(
            Expense.hr_email == approver_email,
            Expense.approval_status == "Awaiting HR Approval"
        ).all()

    return expenses


def get_expense_status_message(expense: Expense) -> str:
    """Generate human-readable status message"""
    status_map = {
        "Pending": "I’m still processing this expense.",
        "Self-Approved": f"This one was approved automatically because it is below ₹{SELF_APPROVAL_LIMIT:,.0f}.",
        "Awaiting Manager Approval": "This is waiting for your manager’s review.",
        "Awaiting HR Approval": "Your manager has approved it, and it is now waiting for HR review.",
        "Fully Approved": "This expense has been fully approved.",
        "Rejected": f"This expense was not approved. Reason: {expense.rejection_reason or 'No reason provided'}"
    }
    return status_map.get(expense.approval_status, f"The current status is {expense.approval_status}.")


def _sync_jira_task(db: Session, expense: Expense) -> dict:
    try:
        jira_result = create_jira_task_for_expense(expense)
    except Exception as exc:
        return {
            "created": False,
            "existing": False,
            "skipped": False,
            "error": str(exc),
        }

    issue_key = jira_result.get("issue_key")
    if issue_key and expense.jira_issue_key != issue_key:
        expense.jira_issue_key = issue_key
        expense.jira_issue_url = jira_result.get("issue_url")
        db.commit()

    return jira_result


def _append_jira_message(message: str, jira_result: dict) -> str:
    if jira_result.get("created") and jira_result.get("issue_key"):
        return (
            f"{message}\n\n"
            f"I’ve also created a Jira task for this approval: **{jira_result['issue_key']}**."
        )

    if jira_result.get("existing") and jira_result.get("issue_key"):
        return (
            f"{message}\n\n"
            f"This approval is already linked to Jira task **{jira_result['issue_key']}**."
        )

    if jira_result.get("error"):
        return (
            f"{message}\n\n"
            f"The approval is saved, but I couldn’t create the Jira task just now."
        )

    return message
