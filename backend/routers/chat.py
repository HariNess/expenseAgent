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
from backend.services.gst_service import lookup_gst_status
from backend.utils.helpers import (
    generate_expense_id, get_today_str,
    get_approval_level, get_initial_approval_status, format_currency
)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# In-memory session store (use Redis in production)
sessions: dict = {}
EXPENSE_ID_PATTERN = re.compile(r"\bEXP-\d{8}-[A-Za-z0-9]+\b", re.IGNORECASE)
STATUS_KEYWORDS = ("status", "track", "tracking", "approval", "approved", "pending", "where is")


def _extract_expense_id(text: str) -> Optional[str]:
    match = EXPENSE_ID_PATTERN.search(text or "")
    return match.group(0) if match else None


def _is_status_lookup(message: str) -> bool:
    lowered = (message or "").lower()
    return any(keyword in lowered for keyword in STATUS_KEYWORDS) or bool(_extract_expense_id(message))


def _build_status_chat_reply(expense: Expense) -> str:
    status_message = get_expense_status_message(expense)
    lines = [
        f"Reference ID: {expense.expense_id}",
        f"Status: {expense.approval_status}",
        status_message,
    ]

    if expense.approval_status == "Awaiting HR Approval":
        lines.append("Your manager has already approved this expense. It is now waiting for HR review.")
    elif expense.approval_status == "Awaiting Manager Approval":
        lines.append("This expense is currently waiting for manager review.")
    elif expense.approval_status == "Fully Approved":
        lines.append("This reimbursement has completed the approval workflow.")

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
                "message": "I couldn't reliably read the invoice details from that document. Please try a clearer image or a higher-quality PDF where the invoice number, date, vendor name, and total amount are visible.",
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
                "message": "Invoice extraction is temporarily unavailable because the configured AI provider has run out of quota or billing access. Please add a valid API key with available usage and try again.",
                "session_id": session_id
            }

        if "Incorrect API key" in error_text or "invalid_api_key" in error_text.lower():
            return {
                "status": "error",
                "message": "Invoice extraction is temporarily unavailable because the configured API key is invalid. Please update the AI provider key in the backend environment and try again.",
                "session_id": session_id
            }

        if "pdfinfo" in error_text or "Poppler" in error_text:
            return {
                "status": "error",
                "message": "PDF processing is not available right now because the PDF renderer dependency is missing on the server. Please upload the invoice as an image for now, or install Poppler on the backend machine.",
                "session_id": session_id
            }

        return {
            "status": "error",
            "message": f"I had trouble processing that document. Could you try uploading it again? Make sure it's a clear image or PDF.",
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
        return {"message": "No pending expense found. Please upload an invoice first."}

    # Prevent editing bill_amount
    if field == "bill_amount":
        return {
            "message": "The bill amount cannot be edited as it's extracted directly from your document. If the amount is wrong, please upload a clearer image of your invoice.",
            "extracted_data": pending
        }

    # Update the field
    if field in pending:
        pending[field] = new_value
        session["pending_expense"] = pending

        response = f"✅ Updated **{field.replace('_', ' ').title()}** to **{new_value}**.\n\nHere's the updated details:\n\n" + \
                   build_table_from_dict(pending) + \
                   "\n\nAnything else to change, or shall I submit this?"

        session["history"].append({"role": "assistant", "content": response})
        return {
            "message": response,
            "extracted_data": pending
        }

    return {"message": f"Field '{field}' not found."}


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
        return {"message": "No pending expense to submit. Please upload an invoice first."}

    # Look up employee
    employee = db.query(Employee).filter(Employee.email == employee_email).first()
    if not employee:
        return {"message": "Employee not found. Please contact IT support."}

    gst_number = (pending.get("gst_number") or "").strip().upper()
    if gst_number:
        try:
            gst_lookup = lookup_gst_status(gst_number)
        except Exception:
            return {
                "message": "I couldn't complete the GST verification step right now. Please try submitting again in a moment.",
                "gst_verification": {
                    "checked": False,
                    "status": "Unavailable",
                },
            }

        if not gst_lookup.get("found"):
            return {
                "message": f"I checked GST number **{gst_number}** during submission, but it could not be verified on the GST registry lookup. Please review the GST number before submitting.",
                "gst_verification": gst_lookup,
                "extracted_data": pending,
            }

        if not gst_lookup.get("is_active"):
            return {
                "message": f"I checked GST number **{gst_number}** during submission and found it is **{gst_lookup.get('status', 'inactive')}**. Please review the GST number before submitting.",
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
        gst_number=pending.get("gst_number"),
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
        response = get_orchestrator_response(
            user_message="Expense submitted",
            conversation_history=session["history"],
            context={
                "type": "expense_submitted",
                "expense_id": expense_id,
                "status": "Self-Approved",
                "amount": format_currency(bill_amount),
                "approval_level": "self"
            }
        )
    else:
        response = get_orchestrator_response(
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
        return {"message": f"No expense found with ID {expense_id}"}

    status_message = get_expense_status_message(expense)
    return {
        "expense_id": expense_id,
        "status": expense.approval_status,
        "message": status_message,
        "details": {
            "vendor": expense.vendor_name,
            "amount": format_currency(expense.bill_amount),
            "submitted": expense.submission_date
        }
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
                "submitted": e.submission_date
            }
            for e in expenses
        ]
    }


def build_table_from_dict(data: dict) -> str:
    from backend.utils.helpers import build_expense_table_markdown
    return build_expense_table_markdown(data)
