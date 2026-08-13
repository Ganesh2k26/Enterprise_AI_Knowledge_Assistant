"""
OCR pipeline for scanned PDFs and raw images.

Detection: a PDF page is considered "scanned" if pdfplumber extracts fewer
than OCR_MIN_TEXT_CHARS_PER_PAGE characters of text from it (i.e. it's
image-only). Scanned pages are rasterized with PyMuPDF and run through
EasyOCR. If EasyOCR fails to load (e.g. no internet to fetch model weights
on first run in an offline environment), we fall back to returning
whatever pdfplumber could extract rather than hard-failing the upload.
"""
import io
import threading

import fitz  # PyMuPDF
from PIL import Image

from app.core.config import settings
from app.core.logging_config import logger

_reader = None
_reader_lock = threading.Lock()
_reader_failed = False


def _get_reader():
    global _reader, _reader_failed
    if _reader is None and not _reader_failed:
        with _reader_lock:
            if _reader is None and not _reader_failed:
                try:
                    import easyocr

                    logger.info(f"Loading EasyOCR reader for languages {settings.OCR_LANGUAGES}...")
                    _reader = easyocr.Reader(settings.OCR_LANGUAGES, gpu=False)
                except Exception as exc:  # pragma: no cover - depends on network/model availability
                    logger.warning(f"EasyOCR could not be initialized, OCR will be skipped: {exc}")
                    _reader_failed = True
    return _reader


def is_scanned_page(extracted_text: str) -> bool:
    return len(extracted_text.strip()) < settings.OCR_MIN_TEXT_CHARS_PER_PAGE


def ocr_image(image: Image.Image) -> str:
    """Run OCR on a single PIL image, returning concatenated recognized text."""
    reader = _get_reader()
    if reader is None:
        return ""
    import numpy as np

    result = reader.readtext(np.array(image), detail=0, paragraph=True)
    return "\n".join(result)


def rasterize_pdf_page(pdf_path: str, page_index: int, zoom: float = 2.0) -> Image.Image:
    """Render a single PDF page to a PIL image using PyMuPDF, at `zoom`x resolution for better OCR accuracy."""
    doc = fitz.open(pdf_path)
    try:
        page = doc[page_index]
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix)
        return Image.open(io.BytesIO(pixmap.tobytes("png")))
    finally:
        doc.close()


def ocr_pdf_page(pdf_path: str, page_index: int) -> str:
    image = rasterize_pdf_page(pdf_path, page_index)
    return ocr_image(image)


def ocr_image_file(path: str) -> str:
    with Image.open(path) as img:
        return ocr_image(img.convert("RGB"))
