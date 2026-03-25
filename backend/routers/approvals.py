from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models.database import get_db, Expense, ApprovalLog
from backend.models.schemas import ApprovalAction
from backend.agents.approval_agent import (
    process_manager_approval,
    process_hr_approval,
    get_pending_approvals
)
from backend.utils.helpers import format_currency

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("/pending/{approver_email}")
async def get_pending(approver_email: str, stage: str = "manager", db: Session = Depends(get_db)):
    """Get all pending approvals for a manager or HR"""
    expenses = get_pending_approvals(db, approver_email, stage)
    return {
        "pending": [
            {
                "expense_id": e.expense_id,
                "employee_email": e.employee_email,
                "vendor_name": e.vendor_name,
                "bill_amount": format_currency(e.bill_amount),
                "bill_amount_raw": e.bill_amount,
                "invoice_date": e.invoice_date,
                "expense_category": e.expense_category,
                "gst_number": e.gst_number,
                "submission_date": e.submission_date,
                "status": e.approval_status
            }
            for e in expenses
        ]
    }


@router.post("/action")
async def take_approval_action(action: ApprovalAction, db: Session = Depends(get_db)):
    """Manager or HR takes approval action"""
    if action.stage.lower() == "manager":
        result = process_manager_approval(
            db=db,
            expense_id=action.expense_id,
            action=action.action,
            comments=action.comments or "",
            approver_email=action.approver_email
        )
    elif action.stage.lower() == "hr":
        result = process_hr_approval(
            db=db,
            expense_id=action.expense_id,
            action=action.action,
            comments=action.comments or "",
            approver_email=action.approver_email
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid stage. Use 'manager' or 'hr'")

    return result


@router.get("/expense/{expense_id}/logs")
async def get_approval_logs(expense_id: str, db: Session = Depends(get_db)):
    """Get all approval logs for an expense"""
    logs = db.query(ApprovalLog).filter(
        ApprovalLog.expense_id == expense_id
    ).order_by(ApprovalLog.created_at).all()

    return {
        "expense_id": expense_id,
        "logs": [
            {
                "action_by": log.action_by,
                "action_type": log.action_type,
                "stage": log.approval_stage,
                "date": log.action_date,
                "comments": log.comments
            }
            for log in logs
        ]
    }


@router.get("/all-expenses")
async def get_all_expenses(db: Session = Depends(get_db)):
    """Get all expenses — admin view"""
    expenses = db.query(Expense).order_by(Expense.created_at.desc()).all()
    return {
        "total": len(expenses),
        "expenses": [
            {
                "expense_id": e.expense_id,
                "employee_email": e.employee_email,
                "vendor_name": e.vendor_name,
                "bill_amount": format_currency(e.bill_amount),
                "status": e.approval_status,
                "category": e.expense_category,
                "submitted": e.submission_date
            }
            for e in expenses
        ]
    }
