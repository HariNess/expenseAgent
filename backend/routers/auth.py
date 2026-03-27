import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.database import Employee, get_db
from backend.models.schemas import LoginRequest, LoginResponse


router = APIRouter(prefix="/api/auth", tags=["auth"])

DEFAULT_PASSWORD = os.getenv("DEMO_LOGIN_PASSWORD", "Ness@123")


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.email == request.email).first()
    if not employee:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if (request.password or "") != DEFAULT_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    role = "employee"
    if employee.email == employee.hr_email:
        role = "hr"
    elif employee.email == employee.manager_email:
        role = "manager"

    return LoginResponse(
        email=employee.email,
        full_name=employee.full_name,
        department=employee.department,
        role=role,
        default_password_hint=DEFAULT_PASSWORD,
    )
