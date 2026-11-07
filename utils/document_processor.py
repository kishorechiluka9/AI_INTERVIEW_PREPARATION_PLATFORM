
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
        print("PDF STEP 1: Reading PDF...")

        reader = PdfReader(BytesIO(pdf_bytes))

        if reader.is_encrypted:
            raise ValueError("Encrypted PDF is not supported.")

        total_pages = len(reader.pages)

        if total_pages == 0:
            raise ValueError("PDF has no pages.")

        print(f"PDF STEP 2: Total pages: {total_pages}")

        # First try normal text extraction.
        pages = []

        for i, page in enumerate(reader.pages, start=1):
            print(f"PDF STEP 3: Extracting page {i}/{total_pages}")
            pages.append(page.extract_text() or "")

        text = "\n\n".join(pages).strip()

        if text:
            print("PDF STEP 4: Normal text extraction successful")
            print("Extracted characters:", len(text))
            return text

        print("PDF STEP 4: No selectable text. Starting OCR...")

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

        print("OCR STEP 1: Checking Tesseract...")

        if os.name == "nt":
            if Path(TESSERACT_PATH).is_file():
                pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
            elif not shutil.which("tesseract"):
                raise RuntimeError("Tesseract executable not found.")
        else:
            if not shutil.which("tesseract"):
                raise RuntimeError("Tesseract executable not found on Linux.")

        print("OCR STEP 2: Tesseract available")

        if os.name == "nt":
            poppler_dir = Path(POPPLER_PATH)

            if not (poppler_dir / "pdftoppm.exe").is_file():
                raise RuntimeError(
                    f"Poppler path incorrect: {POPPLER_PATH}"
                )

        print("OCR STEP 3: Converting PDF pages to images...")

        images = convert_from_bytes(
            pdf_bytes,
            dpi=150,
            poppler_path=POPPLER_PATH,
            thread_count=2,
            timeout=60
        )

        print(f"OCR STEP 4: Converted {len(images)} pages")

        extracted = []

        for i, image in enumerate(images, start=1):
            print(f"OCR STEP 5: Reading page {i}/{len(images)}")

            text = pytesseract.image_to_string(
                image,
                lang="eng",
                timeout=30
            )

            extracted.append(text)

        result = "\n\n".join(extracted).strip()

        if not result:
            raise ValueError("OCR found no readable text.")

        print("OCR STEP 6: OCR completed successfully")

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
