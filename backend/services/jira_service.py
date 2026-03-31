import os
from typing import Any, Dict

import requests
from backend.utils.helpers import format_currency


JIRA_TIMEOUT = float(os.getenv("JIRA_TIMEOUT", "12"))


def jira_is_configured() -> bool:
    return all(
        [
            os.getenv("JIRA_BASE_URL"),
            os.getenv("JIRA_EMAIL"),
            os.getenv("JIRA_API_TOKEN"),
            os.getenv("JIRA_PROJECT_KEY"),
        ]
    )


def create_jira_task_for_expense(expense) -> Dict[str, Any]:
    if getattr(expense, "jira_issue_key", None):
        issue_key = expense.jira_issue_key
        return {
            "created": False,
            "existing": True,
            "issue_key": issue_key,
            "issue_url": getattr(expense, "jira_issue_url", None) or _build_issue_url(issue_key),
        }

    if not jira_is_configured():
        return {
            "created": False,
            "existing": False,
            "skipped": True,
            "reason": "Jira is not configured yet.",
        }

    base_url = os.getenv("JIRA_BASE_URL", "").rstrip("/")
    api_url = f"{base_url}/rest/api/3/issue"
    issue_type = os.getenv("JIRA_ISSUE_TYPE", "Task")

    payload = {
        "fields": {
            "project": {"key": os.getenv("JIRA_PROJECT_KEY")},
            "summary": _build_summary(expense),
            "issuetype": {"name": issue_type},
            "description": _build_description(expense),
        }
    }

    response = requests.post(
        api_url,
        json=payload,
        auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN")),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=JIRA_TIMEOUT,
    )

    if response.status_code not in (200, 201):
        _raise_jira_error(response)

    data = response.json()
    issue_key = data.get("key")
    if not issue_key:
        raise RuntimeError("Jira did not return an issue key after creating the task.")
    return {
        "created": True,
        "existing": False,
        "project_key": os.getenv("JIRA_PROJECT_KEY"),
        "issue_type": issue_type,
        "issue_key": issue_key,
        "issue_url": _build_issue_url(issue_key),
    }


def _build_issue_url(issue_key: str | None) -> str | None:
    if not issue_key:
        return None
    base_url = os.getenv("JIRA_BASE_URL", "").rstrip("/")
    if not base_url:
        return None
    return f"{base_url}/browse/{issue_key}"


def _build_description(expense) -> Dict[str, Any]:
    amount = format_currency(expense.bill_amount)
    employee = getattr(expense, "employee_email", None) or "Not available"
    category = getattr(expense, "expense_category", None) or "Not available"
    vendor = getattr(expense, "vendor_name", None) or "Not available"

    lines = [
        f"Approved for: {employee}",
        f"Amount approved: {amount}",
        f"Category: {category}",
        f"Vendor: {vendor}",
        f"Expense ID: {expense.expense_id}",
        f"Employee: {employee}",
        f"Vendor: {vendor}",
        f"Invoice Number: {expense.invoice_number or 'Not available'}",
        f"Invoice Date: {expense.invoice_date or 'Not available'}",
        f"Bill Amount: {amount if expense.bill_amount is not None else 'Not available'}",
        f"GST Number: {expense.gst_number or 'Not available'}",
        f"GST Amount: {format_currency(expense.gst_amount) if expense.gst_amount is not None else 'Not available'}",
        f"Category: {category}",
        f"Approval Status: {expense.approval_status}",
        f"Submitted On: {expense.submission_date or 'Not available'}",
    ]

    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "Expense approval details"}],
            },
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": line}],
                            }
                        ],
                    }
                    for line in lines
                ],
            },
        ],
    }


def _build_summary(expense) -> str:
    employee = getattr(expense, "employee_email", None) or "Unknown employee"
    category = getattr(expense, "expense_category", None) or "General"
    amount = format_currency(expense.bill_amount)
    return f"Approved expense for {employee} | {amount} | {category}"


def _raise_jira_error(response: requests.Response) -> None:
    body = {}
    try:
        body = response.json()
    except ValueError:
        body = {}

    error_messages = body.get("errorMessages") or []
    first_error = error_messages[0] if error_messages else response.text
    lowered_error = first_error.lower()

    if response.status_code == 401:
        if "permission" in lowered_error:
            raise RuntimeError(
                "Jira rejected the request for this project. Check JIRA_PROJECT_KEY and confirm this account can create issues there."
            )
        raise RuntimeError(
            "Jira authentication failed. Check JIRA_EMAIL and JIRA_API_TOKEN."
        )

    if response.status_code == 403:
        raise RuntimeError(
            "Jira denied access to create issues in this project. Make sure this account has Create issues permission."
        )

    if response.status_code == 404:
        raise RuntimeError(
            "Jira could not find the configured project. Check JIRA_PROJECT_KEY and JIRA_BASE_URL."
        )

    raise RuntimeError(
        f"Jira issue creation failed with status {response.status_code}: {first_error}"
    )
