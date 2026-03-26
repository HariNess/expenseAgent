import base64
import os
from typing import Optional

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

INVOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "vendor_name": {"type": "string"},
        "invoice_number": {"type": "string"},
        "invoice_date": {"type": "string"},
        "bill_amount": {"type": "number"},
        "gst_number": {"type": "string"},
        "gst_amount": {"type": "number"},
        "expense_category": {"type": "string"},
    },
    "required": [
        "vendor_name",
        "invoice_number",
        "invoice_date",
        "bill_amount",
        "gst_number",
        "gst_amount",
        "expense_category",
    ],
    "additionalProperties": False,
}

FRAUD_SCHEMA = {
    "type": "object",
    "properties": {
        "ai_fraud_detected": {"type": "boolean"},
        "confidence": {"type": "number"},
        "reasons": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["ai_fraud_detected", "confidence", "reasons"],
    "additionalProperties": False,
}


def _parse_json_response(response) -> dict:
    content = response.choices[0].message.content or ""
    if isinstance(content, str):
        import json
        return json.loads(content)
    raise ValueError("Model returned an empty response")


def extract_invoice_with_vision(
    image_bytes: bytes,
    media_type: str = "image/jpeg",
    extraction_hint: str = ""
) -> dict:
    """
    Send invoice image to OpenAI Vision and extract structured data.
    """
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    prompt = f"""You are an expert invoice parser.

Extract these fields from the invoice image:
- vendor_name: Name of the vendor or supplier
- invoice_number: Invoice ID or bill number
- invoice_date: Date on the invoice in YYYY-MM-DD format when possible
- bill_amount: Total bill amount as a number without currency symbols
- gst_number: GST registration number of the vendor if present, else empty string
- gst_amount: GST or tax amount as a number if present, else 0
- expense_category: Best match from:
  Travel Reimbursement, Internet Bill, Fuel Reimbursement, Hotel & Accommodation,
  Food & Meals, Office Supplies, Client Entertainment, Medical Reimbursement,
  Training & Courses, Miscellaneous

Important:
- Read the document carefully before leaving fields blank.
- Prioritize the printed invoice total, invoice number, vendor name, invoice date, and GST details.
- If the image is a photographed bill, infer the most likely vendor name from the header.
- Return empty strings or 0 only when the field is truly not visible.

Additional guidance for this attempt:
{extraction_hint or "No extra guidance."}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_b64}",
                            "detail": "high",
                        },
                    },
                ],
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "invoice_extraction",
                "strict": True,
                "schema": INVOICE_SCHEMA,
            },
        },
        max_tokens=1000,
    )

    return _parse_json_response(response)


def chat_with_orchestrator(
    message: str,
    conversation_history: list,
    system_prompt: str,
    tools: Optional[list] = None
) -> dict:
    """
    Send message to the OpenAI chat model with conversation history.
    """
    messages = [{"role": "system", "content": system_prompt}]
    for msg in conversation_history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    messages.append({"role": "user", "content": message})

    kwargs = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 2000,
    }

    if tools:
        kwargs["tools"] = tools

    response = client.chat.completions.create(**kwargs)
    choice = response.choices[0]
    message_obj = choice.message

    result = {
        "content": message_obj.content or "",
        "tool_use": None,
        "stop_reason": choice.finish_reason
    }

    if getattr(message_obj, "tool_calls", None):
        tool_call = message_obj.tool_calls[0]
        import json
        result["tool_use"] = {
            "name": tool_call.function.name,
            "input": json.loads(tool_call.function.arguments),
            "id": tool_call.id
        }

    return result


def analyze_fraud_with_ai(invoice_data: dict, existing_invoices: list) -> dict:
    """
    Use OpenAI to do intelligent fraud analysis beyond rule checks.
    """
    prompt = f"""You are a fraud detection expert for expense management.

Analyze this invoice for potential fraud indicators:
{invoice_data}

Recent invoices from the same employee:
{existing_invoices}

Check for:
1. Unusual vendor names or patterns
2. Suspiciously round amounts
3. Inconsistent GST calculations
4. Vendor names that look fake or generic
5. Any other red flags
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "fraud_analysis",
                "strict": True,
                "schema": FRAUD_SCHEMA,
            },
        },
        max_tokens=500,
    )

    return _parse_json_response(response)
