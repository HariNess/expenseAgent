"""
Orchestrator Agent
The master agent that understands user intent and coordinates all other agents.
Maintains conversation state and routes to the right specialist agent.
"""
from backend.services.claude_service import chat_with_orchestrator
from backend.utils.helpers import build_expense_table_markdown

SYSTEM_PROMPT = """You are NessExpense, an intelligent expense management assistant for Ness Technologies employees.

You help employees submit expense bills and invoices through a natural conversation — just like talking to a helpful colleague.

## Your Capabilities
- Help employees submit expense bills and invoices
- Show extracted invoice details in a clean table
- Allow employees to edit any field EXCEPT the bill amount
- Route expenses through the correct approval path
- Tell employees the status of their submitted expenses

## Your Personality
- Friendly, concise, and professional
- Never expose technical errors or internal system names
- Never ask users to fill forms or click multiple buttons
- Always guide users naturally — like ChatGPT or Claude would

## Expense Submission Flow
1. Ask user to upload their bill/invoice
2. System extracts data automatically (you will receive extracted data)
3. Show extracted table to user
4. Ask if anything needs editing (except amount — never editable)
5. Ask for confirmation to submit
   - If the bill was converted from USD to INR, mention that the review table already includes the INR-converted amount and the FX rate used for today
6. Tell user the approval path based on amount:
   - Below ₹100 → Auto-approved, no further action needed
   - ₹100 and above → Sent to manager, then HR

## Editing Rules
- User CAN edit: vendor_name, invoice_number, invoice_date, gst_number, gst_amount, expense_category
- User CANNOT edit: bill_amount (extracted from document — fixed)
- If user tries to edit amount, politely decline and explain it's fixed from the document

## Status Checking
When user asks about expense status, ask for their expense reference ID or look up their recent submissions.

## Important Rules
- Always confirm before final submission
- If fraud is detected, explain clearly and stop the flow
- Be empathetic if a bill is rejected
- Keep responses SHORT and conversational — no long paragraphs

## Context Handling
You will receive special context in square brackets like [EXTRACTED_DATA: {...}] or [FRAUD_DETECTED: ...] or [EXPENSE_SUBMITTED: ...].
Use this context to respond naturally without exposing the raw data format.
"""


def get_orchestrator_response(
    user_message: str,
    conversation_history: list,
    context: dict = None
) -> str:
    """
    Get response from orchestrator agent.
    Context can contain extracted invoice data, fraud results, etc.
    """

    # Inject context into the message if provided
    enriched_message = user_message
    if context:
        if context.get("type") == "extracted_data":
            table = build_expense_table_markdown(context["data"])
            enriched_message = f"""[EXTRACTED_DATA from invoice scan]:
{context['data']}

Formatted table:
{table}

User message: {user_message}

Please show the user this extracted data in a friendly way and ask them to confirm or edit."""

        elif context.get("type") == "fraud_detected":
            enriched_message = f"""[FRAUD_DETECTED]:
Reasons: {context['reasons']}

User message: {user_message}

Please inform the user about the fraud issues in a clear, empathetic way and ask them to resubmit."""

        elif context.get("type") == "expense_submitted":
            enriched_message = f"""[EXPENSE_SUBMITTED]:
Expense ID: {context['expense_id']}
Status: {context['status']}
Amount: {context['amount']}
Approval level: {context['approval_level']}

User message: {user_message}

Please confirm the submission to the user with the reference ID and explain next steps based on approval level."""

        elif context.get("type") == "status_check":
            enriched_message = f"""[STATUS_CHECK]:
{context['status_data']}

User message: {user_message}

Please tell the user about their expense status in a friendly way."""

    result = chat_with_orchestrator(
        message=enriched_message,
        conversation_history=conversation_history,
        system_prompt=SYSTEM_PROMPT
    )

    return result["content"]


def parse_edit_intent(user_message: str, current_data: dict) -> dict:
    """
    Parse user's edit request and return updated data.
    Example: "change category to Travel" → updates expense_category
    """
    from backend.services.claude_service import chat_with_orchestrator

    prompt = f"""The user wants to edit their expense data. Current data:
{current_data}

User's edit request: "{user_message}"

Extract what field they want to change and the new value.
Return ONLY a JSON with:
{{
  "field": "field_name",
  "new_value": "new value",
  "is_amount_edit": true/false
}}

Valid editable fields: vendor_name, invoice_number, invoice_date, gst_number, gst_amount, expense_category
If user tries to edit bill_amount, set is_amount_edit to true.
If no clear edit intent, return {{"field": null, "new_value": null, "is_amount_edit": false}}"""

    result = chat_with_orchestrator(
        message=prompt,
        conversation_history=[],
        system_prompt="You are a JSON parser. Return only valid JSON."
    )

    import json
    try:
        raw = result["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception:
        return {"field": None, "new_value": None, "is_amount_edit": False}
