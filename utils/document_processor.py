
from io import BytesIO
from pathlib import Path
import os
import shutil

from pypdf import PdfReader


# Windows Poppler path; Streamlit Cloud uses Linux system Poppler.
POPPLER_PATH = (
    r"C:\Users\user\Downloads\Release-26.09.0-0\poppler-26.09.0\Library\bin"
    if os.name == "nt"
    else None
)

# Windows Tesseract path.
TESSERACT_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


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

        # First try normal PDF text extraction.
        pages = [
            page.extract_text() or ""
            for page in reader.pages
        ]

        text = "\n\n".join(pages).strip()

        if text:
            return text

        # If the PDF is scanned, use OCR.
        return extract_using_ocr(pdf_bytes)

    except ValueError:
        raise

    except Exception as exc:
        raise ValueError(
            f"Unable to process PDF: {exc}"
        ) from exc


def extract_using_ocr(pdf_bytes):
    """Extract text from scanned PDFs using Tesseract OCR."""

    try:
        import pytesseract
        from pdf2image import convert_from_bytes

        # Configure Tesseract.
        if os.name == "nt":
            if Path(TESSERACT_PATH).is_file():
                pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
            elif not shutil.which("tesseract"):
                raise RuntimeError(
                    "Tesseract executable not found on Windows."
                )
        else:
            if not shutil.which("tesseract"):
                raise RuntimeError(
                    "Tesseract executable not found on Linux."
                )

        # Validate Poppler only on Windows.
        if os.name == "nt":
            if not POPPLER_PATH:
                raise RuntimeError("Poppler path is not configured.")

            poppler_dir = Path(POPPLER_PATH)

            if not (poppler_dir / "pdftoppm.exe").is_file():
                raise RuntimeError(
                    f"Poppler path incorrect: {POPPLER_PATH}"
                )

            if not (poppler_dir / "pdfinfo.exe").is_file():
                raise RuntimeError(
                    "pdfinfo.exe missing from Poppler bin."
                )

        # Convert PDF bytes into images.
        images = convert_from_bytes(
            pdf_bytes,
            poppler_path=POPPLER_PATH
        )

        extracted = []

        for image in images:
            text = pytesseract.image_to_string(
                image,
                lang="eng"
            )
            extracted.append(text)

        result = "\n\n".join(extracted).strip()

        if not result:
            raise ValueError("OCR found no readable text.")

        return result

    except Exception as exc:
        print("OCR ERROR:", repr(exc))

        raise ValueError(
            f"OCR failed: {type(exc).__name__}: {exc}"
        ) from exc


def validate_job_description(jd_text):
    """Validate job description text."""

    if not jd_text or not jd_text.strip():
        raise ValueError("Please enter a Job Description.")

    jd_text = jd_text.strip()

    if len(jd_text) < 50:
        raise ValueError(
            "Please provide a detailed Job Description "
            "(at least 50 characters)."
        )

    return jd_text
