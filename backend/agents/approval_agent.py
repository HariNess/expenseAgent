"""
Approval Agent
Handles expense approval routing, status updates, and notifications
"""
from sqlalchemy.orm import Session
from backend.models.database import Expense, ApprovalLog, Employee
from backend.utils.helpers import get_today_str, format_currency


def process_self_approval(db: Session, expense: Expense) -> dict:
    """Handle self-approval for expenses below ₹5,000"""
    expense.approval_status = "Self-Approved"

    log = ApprovalLog(
        expense_id=expense.expense_id,
        employee_email=expense.employee_email,
        action_by=expense.employee_email,
        action_type="Auto-Approved",
        action_date=get_today_str(),
        comments="Auto-approved as amount is below ₹5,000",
        approval_stage="Self",
        bill_amount=expense.bill_amount,
        vendor_name=expense.vendor_name
    )
    db.add(log)
    db.commit()

    return {
        "status": "Self-Approved",
        "message": f"✅ Your expense **{expense.expense_id}** has been automatically approved!\n\n"
                   f"Since the amount is below ₹5,000, no further approval is needed.\n\n"
                   f"**Amount:** {format_currency(expense.bill_amount)}\n"
                   f"**Vendor:** {expense.vendor_name}\n"
                   f"**Reference:** {expense.expense_id}"
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
            "message": f"✅ Manager approved expense {expense_id}. Forwarded to HR."
        }
    else:
        expense.approval_status = "Rejected"
        expense.rejection_reason = comments
        db.commit()
        return {
            "status": "Rejected",
            "message": f"❌ Expense {expense_id} rejected by manager.\nReason: {comments}"
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
        return {
            "status": "Fully Approved",
            "message": f"🎉 Expense {expense_id} fully approved by HR!\n"
                       f"Amount: {format_currency(expense.bill_amount)}\n"
                       f"Reimbursement will be processed shortly."
        }
    else:
        expense.approval_status = "Rejected"
        expense.rejection_reason = comments
        db.commit()
        return {
            "status": "Rejected",
            "message": f"❌ Expense {expense_id} rejected by HR.\nReason: {comments}"
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
        "Pending": "⏳ Your expense is being processed.",
        "Self-Approved": f"✅ Auto-approved (amount below ₹5,000).",
        "Awaiting Manager Approval": "⏳ Waiting for your manager to approve.",
        "Awaiting HR Approval": "⏳ Manager approved! Waiting for HR approval.",
        "Fully Approved": "🎉 Fully approved by Manager and HR!",
        "Rejected": f"❌ Rejected. Reason: {expense.rejection_reason or 'No reason provided'}"
    }
    return status_map.get(expense.approval_status, f"Status: {expense.approval_status}")
