"""
Extraction Agent
Responsible for extracting structured data from invoice images using Claude Vision
"""
import io
from PIL import Image
from backend.services.claude_service import extract_invoice_with_vision
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
        img = Image.open(io.BytesIO(file_bytes))
        # Resize if too large (Claude has limits)
        if img.width > 2000 or img.height > 2000:
            img.thumbnail((2000, 2000), Image.LANCZOS)
            output = io.BytesIO()
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            img.save(output, format="JPEG")
            file_bytes = output.getvalue()
            media_type = "image/jpeg"
    except Exception as e:
        raise ValueError(f"Could not process image: {str(e)}")

    # Call Claude Vision
    extracted = extract_invoice_with_vision(file_bytes, media_type)
    return extracted


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

    return cleaned
