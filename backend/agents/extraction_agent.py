"""
Extraction Agent
Responsible for extracting structured data from invoice images using Claude Vision
"""
import io
from PIL import Image, ImageEnhance, ImageOps
from backend.services.claude_service import extract_invoice_with_vision
from backend.services.fx_service import get_usd_to_inr_rate
from backend.utils.helpers import detect_media_type


def process_invoice_file(file_bytes: bytes, filename: str) -> dict:
    """
    Process uploaded invoice file and extract structured data.
    Handles images and PDFs.
    """
    media_type = detect_media_type(filename)

    # If PDF, convert first page to image
    if media_type == "application/pdf":
        file_bytes, media_type = convert_pdf_to_image(file_bytes)

    # Validate image can be opened
    try:
        normalized_bytes, media_type = prepare_image_bytes(file_bytes, media_type)
    except Exception as e:
        raise ValueError(f"Could not process image: {str(e)}")

    attempts = [
        (
            normalized_bytes,
            "Primary pass. Read the invoice exactly as shown and avoid leaving visible fields blank.",
        )
    ]

    try:
        enhanced_bytes = build_enhanced_variant(normalized_bytes)
        attempts.append(
            (
                enhanced_bytes,
                "Retry on an enhanced invoice image. Focus on the vendor header, invoice number, invoice date, total amount, and GST values.",
            )
        )
    except Exception:
        pass

    best_result = None
    best_score = -1

    for candidate_bytes, hint in attempts:
        extracted = extract_invoice_with_vision(candidate_bytes, media_type, hint)
        score = extraction_score(extracted)
        if score > best_score:
            best_result = extracted
            best_score = score
        if score >= 4:
            break

    return best_result or {}


def convert_pdf_to_image(pdf_bytes: bytes) -> tuple:
    """Convert first page of PDF to image bytes"""
    try:
        import pdf2image
        images = pdf2image.convert_from_bytes(pdf_bytes, first_page=1, last_page=1, dpi=200)
        if images:
            output = io.BytesIO()
            images[0].save(output, format="JPEG")
            return output.getvalue(), "image/jpeg"
    except Exception:
        pass

    # Fallback: render with pypdfium2, which does not require Poppler binaries.
    try:
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(pdf_bytes)
        page = pdf[0]
        bitmap = page.render(scale=2).to_pil()
        if bitmap.mode in ("RGBA", "LA", "P"):
            bitmap = bitmap.convert("RGB")

        output = io.BytesIO()
        bitmap.save(output, format="JPEG")
        page.close()
        pdf.close()
        return output.getvalue(), "image/jpeg"
    except Exception:
        pass

    # Fallback: try PIL directly
    try:
        img = Image.open(io.BytesIO(pdf_bytes))
        output = io.BytesIO()
        img.save(output, format="JPEG")
        return output.getvalue(), "image/jpeg"
    except Exception as e:
        raise ValueError(f"Could not convert PDF: {str(e)}")


def prepare_image_bytes(file_bytes: bytes, media_type: str) -> tuple[bytes, str]:
    """Normalize invoice images to a high-quality RGB JPEG for OCR-style extraction."""
    img = Image.open(io.BytesIO(file_bytes))
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Upscale small mobile captures a bit; downscale overly large images.
    max_dim = max(img.width, img.height)
    if max_dim < 1400:
        scale = 1400 / max_dim
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    elif max_dim > 2200:
        img.thumbnail((2200, 2200), Image.LANCZOS)

    output = io.BytesIO()
    img.save(output, format="JPEG", quality=95, optimize=True)
    return output.getvalue(), "image/jpeg"


def build_enhanced_variant(file_bytes: bytes) -> bytes:
    """Create a higher-contrast variant that helps OCR-heavy receipts and invoices."""
    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Contrast(img).enhance(1.35)
    img = ImageEnhance.Sharpness(img).enhance(1.25)

    output = io.BytesIO()
    img.save(output, format="JPEG", quality=95, optimize=True)
    return output.getvalue()


def extraction_score(extracted: dict) -> int:
    """Score extraction completeness so we can prefer the best retry result."""
    score = 0
    if extracted.get("vendor_name"):
        score += 1
    if extracted.get("invoice_number"):
        score += 1
    if extracted.get("invoice_date"):
        score += 1
    if extracted.get("bill_amount") not in (None, "", 0, 0.0):
        score += 2
    if extracted.get("gst_number"):
        score += 1
    if extracted.get("expense_category"):
        score += 1
    return score


def extraction_is_meaningful(extracted: dict) -> bool:
    """Detect when the AI effectively failed to read the invoice."""
    return extraction_score(extracted) >= 2


def validate_extracted_data(extracted: dict) -> dict:
    """
    Validate and clean extracted data.
    Ensure types are correct.
    """
    cleaned = {}

    # Text fields
    for field in ["vendor_name", "invoice_number", "invoice_date", "gst_number", "expense_category"]:
        val = extracted.get(field, "")
        cleaned[field] = str(val).strip() if val else ""

    bill_currency = str(extracted.get("bill_currency", "") or "INR").strip().upper()
    if bill_currency == "$":
        bill_currency = "USD"
    cleaned["bill_currency"] = bill_currency or "INR"

    # Numeric fields
    for field in ["bill_amount", "gst_amount"]:
        val = extracted.get(field, 0)
        try:
            # Remove currency symbols and commas
            if isinstance(val, str):
                val = val.replace("₹", "").replace(",", "").replace(" ", "").strip()
            cleaned[field] = float(val) if val else 0.0
        except (ValueError, TypeError):
            cleaned[field] = 0.0

    cleaned["original_bill_amount"] = cleaned["bill_amount"]
    cleaned["exchange_rate"] = None
    cleaned["exchange_rate_date"] = None

    if cleaned["bill_currency"] == "USD" and cleaned["bill_amount"] > 0:
        try:
            fx = get_usd_to_inr_rate()
            cleaned["exchange_rate"] = fx["rate"]
            cleaned["exchange_rate_date"] = fx["date"]
            cleaned["bill_amount"] = round(cleaned["original_bill_amount"] * fx["rate"], 2)
        except Exception:
            # If FX lookup fails, preserve the original amount so the user can still review it.
            pass

    return cleaned
