
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
        import fitz
        import pytesseract
        from PIL import Image

        # Find Tesseract executable on Streamlit Cloud
        tesseract_path = shutil.which("tesseract")

        if not tesseract_path:
            raise RuntimeError(
                "Tesseract executable not found. Check packages.txt."
            )

        pytesseract.pytesseract.tesseract_cmd = tesseract_path

        print("OCR STEP 1: Opening PDF with PyMuPDF", flush=True)

        document = fitz.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        extracted = []

        for page_number, page in enumerate(document, start=1):

            print(
                f"OCR STEP 2: Rendering page {page_number}",
                flush=True
            )

            pix = page.get_pixmap(
                matrix=fitz.Matrix(2, 2),
                colorspace=fitz.csGRAY,
                alpha=False
            )

            image = Image.frombytes(
                "L",
                [pix.width, pix.height],
                pix.samples
            )

            print(
                f"OCR STEP 3: Image size {image.size}",
                flush=True
            )

            text = pytesseract.image_to_string(
                image,
                lang="eng",
                config="--oem 1 --psm 6",
                timeout=90
            )

            print(
                f"OCR STEP 4: Page {page_number}, characters: {len(text)}",
                flush=True
            )

            extracted.append(text)

        document.close()

        result = "\n\n".join(extracted).strip()

        if len(result) < 20:
            raise ValueError(
                "OCR could not extract readable resume text."
            )

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
