from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class EmployeeSchema(BaseModel):
    full_name: str
    email: str
    department: Optional[str] = None
    manager_email: Optional[str] = None
    hr_email: Optional[str] = None

    class Config:
        from_attributes = True


class ExtractedInvoice(BaseModel):
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    bill_amount: Optional[float] = None
    gst_number: Optional[str] = None
    gst_amount: Optional[float] = None
    expense_category: Optional[str] = None


class FraudCheckResult(BaseModel):
    is_fraudulent: bool
    reasons: List[str] = []
    confidence: float = 1.0


class ExpenseCreateRequest(BaseModel):
    employee_email: str
    vendor_name: str
    invoice_number: str
    invoice_date: str
    bill_amount: float
    gst_number: Optional[str] = None
    gst_amount: Optional[float] = None
    expense_category: str


class ExpenseResponse(BaseModel):
    expense_id: str
    employee_email: str
    vendor_name: str
    invoice_number: str
    invoice_date: str
    bill_amount: float
    gst_number: Optional[str] = None
    gst_amount: Optional[float] = None
    expense_category: str
    submission_date: str
    approval_status: str
    approval_level: str

    class Config:
        from_attributes = True


class ApprovalAction(BaseModel):
    expense_id: str
    action: str  # "approve" or "reject"
    comments: Optional[str] = None
    approver_email: str
    stage: str  # "manager" or "hr"


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    employee_email: str
    conversation_history: Optional[List[ChatMessage]] = []
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    action: Optional[str] = None
    data: Optional[dict] = None
    session_id: Optional[str] = None
