
from io import BytesIO
from pathlib import Path
import shutil

from pypdf import PdfReader
import os

if os.name == "nt":
    poppler_path = r"C:\Users\user\Downloads\Release-26.09.0-0\poppler-26.09.0\Library\bin"
else:
    poppler_path = None

def extract_resume_text(pdf_file):
    """Extract resume text from normal or scanned PDFs."""

    if pdf_file is None:
        raise ValueError("Please upload your resume PDF.")

    pdf_bytes = pdf_file.getvalue()

    if not pdf_bytes:
        raise ValueError("Uploaded PDF is empty.")

    try:
        reader = PdfReader(BytesIO(pdf_bytes))

        if reader.is_encrypted:
            raise ValueError("Encrypted PDF is not supported.")

        if len(reader.pages) == 0:
            raise ValueError("PDF has no pages.")

        # First try normal PDF extraction
        pages = [
            page.extract_text() or ""
            for page in reader.pages
        ]

        text = "\n\n".join(pages).strip()

        if text:
            return text

        # If no readable text, try OCR
        return extract_using_ocr(pdf_bytes)

    except ValueError:
        raise

    except Exception as exc:
        raise ValueError(
            f"Unable to process PDF: {exc}"
        ) from exc


def extract_using_ocr(pdf_bytes):
    """OCR fallback for scanned PDF files."""

    try:
        import pytesseract
        from pdf2image import convert_from_bytes

        # Tesseract executable path
        tess_path = (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )

        if Path(tess_path).is_file():
            pytesseract.pytesseract.tesseract_cmd = tess_path
        elif not shutil.which("tesseract"):
            raise RuntimeError(
                "Tesseract executable not found."
            )

        # Replace with your verified Poppler bin path
            import os
            from pdf2image import convert_from_path

            if os.name == "nt":
                POPPLER_PATH = r"C:\Users\user\Downloads\Release-26.09.0-0\poppler-26.09.0\Library\bin"
            else:
                POPPLER_PATH = None

        if not (
            Path(poppler_path) / "pdftoppm.exe"
        ).is_file():
            raise RuntimeError(
                f"Poppler path incorrect: {poppler_path}"
            )

        if not (
            Path(poppler_path) / "pdfinfo.exe"
        ).is_file():
            raise RuntimeError(
                "pdfinfo.exe missing from Poppler bin."
            )

            images = convert_from_path(
                pdf_path,
                poppler_path=poppler_path
            )

        extracted = []

        for image in images:
            text = pytesseract.image_to_string(
                image,
                lang="eng",
            )
            extracted.append(text)

        result = "\n\n".join(extracted).strip()

        if not result:
            raise ValueError(
                "OCR found no readable text."
            )

        return result

    except Exception as exc:
        print("OCR ERROR:", repr(exc))

        raise ValueError(
            f"OCR failed: {type(exc).__name__}: {exc}"
        ) from exc


def validate_job_description(jd_text):
    """Validate job description text."""

    if not jd_text or not jd_text.strip():
        raise ValueError(
            "Please enter a Job Description."
        )

    jd_text = jd_text.strip()

    if len(jd_text) < 50:
        raise ValueError(
            "Please provide a detailed Job Description "
            "(at least 50 characters)."
        )

    return jd_text
