
from io import BytesIO
import os
import shutil
from pathlib import Path

from pypdf import PdfReader


POPPLER_PATH = (
    r"C:\Users\user\Downloads\Release-26.09.0-0\poppler-26.09.0\Library\bin"
    if os.name == "nt"
    else None
)

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_resume_text(pdf_file):
    if pdf_file is None:
        raise ValueError("Please upload your resume PDF.")

    pdf_bytes = pdf_file.getvalue()

    if not pdf_bytes:
        raise ValueError("Uploaded PDF is empty.")

    # STEP 1: Try extracting text using pypdf
    print("NEW DOCUMENT PROCESSOR CODE RUNNING", flush=True)
    try:
        reader = PdfReader(BytesIO(pdf_bytes))

        if reader.is_encrypted:
            raise ValueError("Encrypted PDF is not supported.")

        if len(reader.pages) == 0:
            raise ValueError("PDF has no pages.")

        pages = [
            page.extract_text() or ""
            for page in reader.pages
        ]

        text = "\n\n".join(pages).strip()

        print("pypdf extracted characters:", len(text), flush=True)

        if len(text) > 20:
            return text

    except ValueError:
        raise
    except Exception as exc:
        print("pypdf extraction error:", repr(exc), flush=True)

    # STEP 2: Try PyMuPDF as an alternative
    print("TRYING PYMUPDF EXTRACTION", flush=True)
    try:
        import fitz

        document = fitz.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        pages = [
            page.get_text("text") or ""
            for page in document
        ]

        text = "\n\n".join(pages).strip()
        document.close()

        print("PyMuPDF extracted characters:", len(text), flush=True)

        if len(text) > 20:
            return text

    except Exception as exc:
        print("PyMuPDF extraction error:", repr(exc), flush=True)

    # STEP 3: Use OCR only if text extraction fails
    print("No readable text found. Starting OCR...", flush=True)

    return extract_using_ocr(pdf_bytes)

def extract_using_ocr(pdf_bytes):
    try:
        import pytesseract
        from pdf2image import convert_from_bytes

        if os.name == "nt":
            if Path(TESSERACT_PATH).is_file():
                pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
            elif not shutil.which("tesseract"):
                raise RuntimeError("Tesseract executable not found.")

            poppler_path = POPPLER_PATH
        else:
            if not shutil.which("tesseract"):
                raise RuntimeError("Tesseract executable not found on Linux.")

            poppler_path = None

        images = convert_from_bytes(
            pdf_bytes,
            dpi=150,
            first_page=1,
            last_page=2,
            poppler_path=poppler_path
        )

        extracted = []

        for image in images:
            text = pytesseract.image_to_string(
                image,
                lang="eng",
                timeout=30
            )
            extracted.append(text)

        result = "\n\n".join(extracted).strip()

        if not result:
            raise ValueError("OCR found no readable text.")

        return result

    except Exception as exc:
        print("OCR ERROR:", repr(exc), flush=True)
        raise ValueError(
            f"OCR failed: {type(exc).__name__}: {exc}"
        ) from exc


def validate_job_description(jd_text):
    if not jd_text or not jd_text.strip():
        raise ValueError("Please enter a Job Description.")

    jd_text = jd_text.strip()

    if len(jd_text) < 50:
        raise ValueError(
            "Please provide a detailed Job Description (at least 50 characters)."
        )

    return jd_text
