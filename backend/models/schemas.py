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
    bill_currency: Optional[str] = None
    original_bill_amount: Optional[float] = None
    exchange_rate: Optional[float] = None
    exchange_rate_date: Optional[str] = None
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


class ClearApprovedExpensesResponse(BaseModel):
    deleted_expenses: int
    deleted_logs: int
    statuses_cleared: List[str]
    message: str


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


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    email: str
    full_name: str
    department: Optional[str] = None
    role: str
    default_password_hint: Optional[str] = None
