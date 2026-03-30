from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = f"sqlite:///{os.getenv('DATABASE_URL', './database/nessexpense.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    department = Column(String)
    manager_email = Column(String)
    hr_email = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    expense_id = Column(String, unique=True, nullable=False)
    employee_email = Column(String, nullable=False)
    vendor_name = Column(String)
    invoice_number = Column(String)
    invoice_date = Column(String)
    bill_amount = Column(Float)
    gst_number = Column(String)
    gst_amount = Column(Float)
    expense_category = Column(String)
    submission_date = Column(String)
    approval_status = Column(String, default="Pending")
    approval_level = Column(String)
    manager_email = Column(String)
    hr_email = Column(String)
    rejection_reason = Column(Text)
    fraud_flags = Column(Text)
    jira_issue_key = Column(String)
    jira_issue_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class ApprovalLog(Base):
    __tablename__ = "approval_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    expense_id = Column(String, nullable=False)
    employee_email = Column(String)
    action_by = Column(String)
    action_type = Column(String)
    action_date = Column(String)
    comments = Column(Text)
    approval_stage = Column(String)
    bill_amount = Column(Float)
    vendor_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    os.makedirs("./database", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _ensure_expense_columns()


def _ensure_expense_columns():
    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(expenses)").fetchall()
        }

        if "jira_issue_key" not in columns:
            connection.exec_driver_sql("ALTER TABLE expenses ADD COLUMN jira_issue_key VARCHAR")

        if "jira_issue_url" not in columns:
            connection.exec_driver_sql("ALTER TABLE expenses ADD COLUMN jira_issue_url VARCHAR")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_employees():
    """Seed or refresh demo employees for testing"""
    db = SessionLocal()
    try:
        employee_specs = [
            {
                "full_name": "Atharva Bhagat",
                "email": "atharva.bhagat@ness.com",
                "department": "Engineering",
                "manager_email": "vignesh.jayakumar@ness.com",
                "hr_email": "hariharasudan.venkatasalam@ness.com",
            },
            {
                "full_name": "Vignesh Jayakumar",
                "email": "vignesh.jayakumar@ness.com",
                "department": "Engineering",
                "manager_email": "vignesh.jayakumar@ness.com",
                "hr_email": "hariharasudan.venkatasalam@ness.com",
            },
            {
                "full_name": "Hariharasudan Venkatasalam",
                "email": "hariharasudan.venkatasalam@ness.com",
                "department": "Human Resources",
                "manager_email": "vignesh.jayakumar@ness.com",
                "hr_email": "hariharasudan.venkatasalam@ness.com",
            },
        ]

        existing_by_name = {
            employee.full_name: employee
            for employee in db.query(Employee).all()
        }

        for spec in employee_specs:
            employee = existing_by_name.get(spec["full_name"])
            if employee:
                employee.email = spec["email"]
                employee.department = spec["department"]
                employee.manager_email = spec["manager_email"]
                employee.hr_email = spec["hr_email"]
            else:
                db.add(Employee(**spec))

        db.commit()
        print("✅ Demo employees refreshed successfully")
    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()
