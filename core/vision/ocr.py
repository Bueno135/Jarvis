import logging
from typing import Optional
from PIL import Image

logger = logging.getLogger("Jarvis.Vision.OCR")


def extract_text(image: Image.Image, languages: str = "por+eng") -> str:
    """
    Extract text from a PIL Image using pytesseract OCR.
    Falls back gracefully if pytesseract/tesseract is not available.

    Args:
        image: PIL Image to extract text from
        languages: Tesseract language codes (default: Portuguese + English)

    Returns:
        Extracted text string, or empty string if OCR fails
    """
    if image is None:
        return ""

    try:
        import pytesseract
        text = pytesseract.image_to_string(image, lang=languages)
        logger.info(f"OCR extracted {len(text)} characters")
        return text.strip()
    except ImportError:
        logger.warning("pytesseract not installed. Attempting basic image analysis.")
        return _fallback_extract(image)
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return _fallback_extract(image)


def _fallback_extract(image: Image.Image) -> str:
    """
    Fallback when tesseract is not available.
    Returns basic image metadata as a description.
    """
    try:
        width, height = image.size
        mode = image.mode
        return f"[Image: {width}x{height}, mode={mode} — OCR unavailable, install pytesseract for text extraction]"
    except Exception:
        return ""
