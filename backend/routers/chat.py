from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import json
import re

from backend.models.database import get_db, Expense, Employee
from backend.models.schemas import ChatRequest, ChatResponse
from backend.agents.orchestrator import get_orchestrator_response, parse_edit_intent
from backend.agents.extraction_agent import (
    process_invoice_file,
    validate_extracted_data,
    extraction_is_meaningful,
)
from backend.agents.fraud_agent import run_fraud_detection, format_fraud_message
from backend.agents.approval_agent import process_self_approval, get_expense_status_message
from backend.services.gst_service import resolve_gst_number
from backend.utils.helpers import (
    generate_expense_id, get_today_str,
    get_approval_level, get_initial_approval_status, format_currency
)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# In-memory session store (use Redis in production)
sessions: dict = {}
EXPENSE_ID_PATTERN = re.compile(r"\bEXP-\d{8}-[A-Za-z0-9]+\b", re.IGNORECASE)
STATUS_KEYWORDS = ("status", "track", "tracking", "approval", "approved", "pending", "where is")


def _build_submission_progress_message(
    base_message: str,
    gst_number: str = "",
    gst_checked: bool = False,
    jira_result: dict | None = None,
) -> str:
    lines = []

    if gst_checked and gst_number:
        lines.append(f"I’ve checked GST number **{gst_number}**.")
        lines.append("GST number is valid and active.")
        lines.append("Everything looks good, so I’m creating the expense now.")
    else:
        lines.append("I’ve completed the final checks.")
        lines.append("Everything looks good, so I’m creating the expense now.")

    lines.append("")
    lines.append(base_message)

    if jira_result and jira_result.get("created") and jira_result.get("issue_key"):
        lines.append("")
        lines.append(f"Jira task created: **{jira_result['issue_key']}**")

    return "\n\n".join(lines)


def _extract_expense_id(text: str) -> Optional[str]:
    match = EXPENSE_ID_PATTERN.search(text or "")
    return match.group(0) if match else None


def _is_status_lookup(message: str) -> bool:
    lowered = (message or "").lower()
    return any(keyword in lowered for keyword in STATUS_KEYWORDS) or bool(_extract_expense_id(message))


def _build_status_chat_reply(expense: Expense) -> str:
    status_message = get_expense_status_message(expense)
    lines = [
        f"Here’s the latest update for **{expense.expense_id}**.",
        f"Current status: **{expense.approval_status}**",
        status_message,
    ]

    if expense.approval_status == "Awaiting HR Approval":
        lines.append("Your manager has already approved it, so the next step is HR review.")
    elif expense.approval_status == "Awaiting Manager Approval":
        lines.append("It’s currently with your manager for review.")
    elif expense.approval_status == "Fully Approved":
        lines.append("Everything is approved now.")

    return "\n\n".join(lines)


@router.post("/message")
async def chat_message(request: ChatRequest, db: Session = Depends(get_db)):
    """Handle text chat messages"""
    session_id = request.session_id or request.employee_email
    if session_id not in sessions:
        sessions[session_id] = {
            "history": [],
            "pending_expense": None,
            "state": "idle"
        }

    session = sessions[session_id]
    history = session["history"]

    if _is_status_lookup(request.message):
        expense_id = _extract_expense_id(request.message)
        expense = None

        if expense_id:
            expense = db.query(Expense).filter(
                Expense.expense_id == expense_id,
                Expense.employee_email == request.employee_email
            ).first()
        else:
            expense = db.query(Expense).filter(
                Expense.employee_email == request.employee_email
            ).order_by(Expense.created_at.desc()).first()

        if expense:
            response_text = _build_status_chat_reply(expense)
            history.append({"role": "user", "content": request.message})
            history.append({"role": "assistant", "content": response_text})
            if len(history) > 20:
                history = history[-20:]
            sessions[session_id]["history"] = history

            return ChatResponse(
                message=response_text,
                session_id=session_id
            )

    # Get orchestrator response
    response_text = get_orchestrator_response(
        user_message=request.message,
        conversation_history=history
    )

    # Update history
    history.append({"role": "user", "content": request.message})
    history.append({"role": "assistant", "content": response_text})

    # Keep history manageable
    if len(history) > 20:
        history = history[-20:]
    sessions[session_id]["history"] = history

    return ChatResponse(
        message=response_text,
        session_id=session_id
    )


@router.post("/upload-invoice")
async def upload_invoice(
    file: UploadFile = File(...),
    employee_email: str = Form(...),
    session_id: str = Form(None),
    db: Session = Depends(get_db)
):
    """Handle invoice file upload, extraction, and fraud detection"""
    session_id = session_id or employee_email
    if session_id not in sessions:
        sessions[session_id] = {
            "history": [],
            "pending_expense": None,
            "state": "idle"
        }

    session = sessions[session_id]

    try:
        # Read file
        file_bytes = await file.read()
        filename = file.filename or "invoice.jpg"

        # Step 1: Extract invoice data using Claude Vision
        raw_extracted = process_invoice_file(file_bytes, filename)
        extracted = validate_extracted_data(raw_extracted)

        if not extraction_is_meaningful(extracted):
            return {
                "status": "error",
                "message": "I couldn’t clearly read the invoice details from that file. Please try a clearer image or a higher-quality PDF where the invoice number, date, vendor name, and total amount are easy to see.",
                "session_id": session_id
            }

        # Step 2: Run fraud detection
        existing_invoices = db.query(Expense).filter(
            Expense.employee_email == employee_email
        ).all()

        fraud_result = run_fraud_detection(extracted, existing_invoices)

        if fraud_result["is_fraudulent"]:
            fraud_message = format_fraud_message(fraud_result)
            response = get_orchestrator_response(
                user_message="Document uploaded",
                conversation_history=session["history"],
                context={"type": "fraud_detected", "reasons": fraud_result["reasons"]}
            )
            session["history"].append({"role": "user", "content": "[Uploaded invoice document]"})
            session["history"].append({"role": "assistant", "content": response})

            return {
                "status": "fraud_detected",
                "message": response,
                "fraud_reasons": fraud_result["reasons"],
                "session_id": session_id
            }

        # Step 3: Store extracted data in session
        session["pending_expense"] = extracted
        session["state"] = "awaiting_confirmation"

        # Step 4: Get agent response with extracted data
        response = get_orchestrator_response(
            user_message="I've uploaded my invoice",
            conversation_history=session["history"],
            context={"type": "extracted_data", "data": extracted}
        )

        session["history"].append({"role": "user", "content": "[Uploaded invoice document]"})
        session["history"].append({"role": "assistant", "content": response})

        return {
            "status": "extracted",
            "message": response,
            "extracted_data": extracted,
            "session_id": session_id
        }

    except Exception as e:
        error_text = str(e)
        if (
            "API usage limits" in error_text
            or "You have reached your specified API usage limits" in error_text
            or "insufficient_quota" in error_text
            or "quota" in error_text.lower()
            or "billing" in error_text.lower()
        ):
            return {
                "status": "error",
                "message": "I can’t read invoices right now because the AI service for extraction has run out of quota or billing access. Please update the API key or billing setup and try again.",
                "session_id": session_id
            }

        if "Incorrect API key" in error_text or "invalid_api_key" in error_text.lower():
            return {
                "status": "error",
                "message": "I can’t read invoices right now because the AI API key looks invalid. Please update the backend key and try again.",
                "session_id": session_id
            }

        if "pdfinfo" in error_text or "Poppler" in error_text:
            return {
                "status": "error",
                "message": "I can’t open PDF invoices on this server right now because the PDF renderer is missing. For now, please upload the invoice as an image or install the PDF dependency on the backend machine.",
                "session_id": session_id
            }

        return {
            "status": "error",
            "message": "I had trouble reading that document. Please try uploading it again and make sure the file is a clear image or PDF.",
            "session_id": session_id
        }


@router.post("/edit-field")
async def edit_field(
    employee_email: str,
    session_id: str,
    field: str,
    new_value: str,
    db: Session = Depends(get_db)
):
    """Edit a field in the pending expense"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    pending = session.get("pending_expense")

    if not pending:
        return {"message": "I don’t have an invoice ready to update yet. Please upload one first."}

    # Prevent editing bill_amount
    if field == "bill_amount":
        return {
            "message": "The total amount is locked because it comes directly from the invoice. If it looks wrong, please upload a clearer copy of the document.",
            "extracted_data": pending
        }

    # Update the field
    if field in pending:
        pending[field] = new_value
        session["pending_expense"] = pending

        response = f"✅ Updated **{field.replace('_', ' ').title()}** to **{new_value}**.\n\nHere's the updated details:\n\n" + \
                   build_table_from_dict(pending) + \
                   "\n\nI’ve updated that for you. Would you like to change anything else, or should I submit it?"

        session["history"].append({"role": "assistant", "content": response})
        return {
            "message": response,
            "extracted_data": pending
        }

    return {"message": f"I couldn’t find the field '{field}' in this invoice."}


@router.post("/submit-expense")
async def submit_expense(
    employee_email: str,
    session_id: str,
    db: Session = Depends(get_db)
):
    """Submit the confirmed expense"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    pending = session.get("pending_expense")

    if not pending:
        return {"message": "I don’t have an invoice ready to submit yet. Please upload one first."}

    # Look up employee
    employee = db.query(Employee).filter(Employee.email == employee_email).first()
    if not employee:
        return {"message": "I couldn’t match this account to an employee record. Please check with your admin or IT team."}

    gst_number = (pending.get("gst_number") or "").strip().upper()
    if gst_number:
        try:
            gst_resolution = resolve_gst_number(gst_number)
            gst_lookup = gst_resolution["lookup"]
            gst_number = gst_resolution["gst_number"]
            pending["gst_number"] = gst_number
        except Exception:
            return {
                "message": "I couldn’t verify the GST number right now. Please try submitting again in a moment.",
                "gst_verification": {
                    "checked": False,
                    "status": "Unavailable",
                },
            }

        if not gst_lookup.get("found"):
            return {
                "message": f"I checked GST number **{gst_number}**, but I couldn’t verify it. Please review it once and then try submitting again.",
                "gst_verification": gst_lookup,
                "extracted_data": pending,
            }

        if not gst_lookup.get("is_active"):
            return {
                "message": f"I checked GST number **{gst_number}** and it looks **{gst_lookup.get('status', 'inactive')}** right now. Please review it before submitting.",
                "gst_verification": gst_lookup,
                "extracted_data": pending,
            }

    # Generate expense ID
    expense_id = generate_expense_id()
    bill_amount = pending.get("bill_amount", 0)
    approval_level = get_approval_level(bill_amount)
    approval_status = get_initial_approval_status(bill_amount)

    # Create expense record
    expense = Expense(
        expense_id=expense_id,
        employee_email=employee_email,
        vendor_name=pending.get("vendor_name"),
        invoice_number=pending.get("invoice_number"),
        invoice_date=pending.get("invoice_date"),
        bill_amount=bill_amount,
        gst_number=gst_number or pending.get("gst_number"),
        gst_amount=pending.get("gst_amount"),
        expense_category=pending.get("expense_category"),
        submission_date=get_today_str(),
        approval_status=approval_status,
        approval_level=approval_level,
        manager_email=employee.manager_email,
        hr_email=employee.hr_email
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    # Handle self-approval
    if approval_level == "Self":
        approval_result = process_self_approval(db, expense)
        response = _build_submission_progress_message(
            approval_result["message"],
            gst_number=gst_number,
            gst_checked=bool(gst_number),
            jira_result=approval_result.get("jira"),
        )
    else:
        base_response = get_orchestrator_response(
            user_message="Expense submitted",
            conversation_history=session["history"],
            context={
                "type": "expense_submitted",
                "expense_id": expense_id,
                "status": "Awaiting Manager Approval",
                "amount": format_currency(bill_amount),
                "approval_level": "dual"
            }
        )
        response = _build_submission_progress_message(
            base_response,
            gst_number=gst_number,
            gst_checked=bool(gst_number),
        )

    # Clear pending expense
    session["pending_expense"] = None
    session["state"] = "idle"
    session["history"].append({"role": "assistant", "content": response})

    return {
        "message": response,
        "expense_id": expense_id,
        "approval_status": expense.approval_status,
        "approval_level": approval_level
    }


@router.get("/status/{expense_id}")
async def get_expense_status(expense_id: str, db: Session = Depends(get_db)):
    """Get expense status"""
    expense = db.query(Expense).filter(Expense.expense_id == expense_id).first()
    if not expense:
        return {"message": f"I couldn’t find any expense with reference ID {expense_id}."}

    status_message = get_expense_status_message(expense)
    return {
        "expense_id": expense_id,
        "status": expense.approval_status,
        "message": status_message,
        "details": {
            "vendor": expense.vendor_name,
            "amount": format_currency(expense.bill_amount),
            "submitted": expense.submission_date
        },
        "jira": {
            "issue_key": expense.jira_issue_key,
            "issue_url": expense.jira_issue_url,
        },
    }


@router.get("/my-expenses/{employee_email}")
async def get_my_expenses(employee_email: str, db: Session = Depends(get_db)):
    """Get all expenses for an employee"""
    expenses = db.query(Expense).filter(
        Expense.employee_email == employee_email
    ).order_by(Expense.created_at.desc()).limit(10).all()

    return {
        "expenses": [
            {
                "expense_id": e.expense_id,
                "vendor_name": e.vendor_name,
                "bill_amount": format_currency(e.bill_amount),
                "status": e.approval_status,
                "submitted": e.submission_date,
                "jira_issue_key": e.jira_issue_key,
                "jira_issue_url": e.jira_issue_url,
            }
            for e in expenses
        ]
    }


def build_table_from_dict(data: dict) -> str:
    from backend.utils.helpers import build_expense_table_markdown
    return build_expense_table_markdown(data)
