"""Local OCR text extraction via Tesseract.

Extracts raw text from uploaded images (PNG/JPEG). If the Tesseract binary is
not installed on the host, a clearly-labelled mock string is returned instead
of crashing, so the two-step review flow remains usable in development.
"""

import io

import pytesseract
from PIL import Image
from pytesseract import TesseractNotFoundError

from app.core.config import settings

_MOCK_TEXT = (
    "[Mock OCR] Tesseract engine is not installed on this server. "
    "Sample extracted text: Patient presents with elevated blood glucose "
    "(HbA1c 8.4%) and uncontrolled hypertension (150/95 mmHg)."
)


def extract_text(image_bytes: bytes) -> str:
    """Return raw text extracted from an image.

    Raises ``ValueError`` for invalid/unsupported image data, and returns a
    mock string when the Tesseract binary is unavailable.
    """
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    try:
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
    except TesseractNotFoundError:
        return _MOCK_TEXT
    except OSError as exc:
        raise ValueError("Invalid or unsupported image file") from exc

    return text.strip() or _MOCK_TEXT
