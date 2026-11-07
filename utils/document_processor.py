
from io import BytesIO
import os
import shutil
from pathlib import Path

from pypdf import PdfReader


def extract_resume_text(pdf_file):
    if pdf_file is None:
        raise ValueError("Please upload your resume PDF.")

    pdf_bytes = pdf_file.getvalue()

    if not pdf_bytes:
        raise ValueError("Uploaded PDF is empty.")

    print("PDF PROCESSING STARTED", flush=True)

    # STEP 1: Extract normal PDF text using pypdf
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

        print("PYPDF CHARACTERS:", len(text), flush=True)

        if len(text) > 20:
            print("TEXT PDF SUCCESS", flush=True)
            return text

    except ValueError:
        raise
    except Exception as exc:
        print("PYPDF ERROR:", repr(exc), flush=True)

    # STEP 2: Try PyMuPDF text extraction
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

        print("PYMUPDF CHARACTERS:", len(text), flush=True)

        if len(text) > 20:
            print("PYMUPDF TEXT SUCCESS", flush=True)
            return text

    except Exception as exc:
        print("PYMUPDF ERROR:", repr(exc), flush=True)

    # STEP 3: OCR fallback for scanned/image PDFs
    print("STARTING OCR FALLBACK", flush=True)

    return extract_using_ocr(pdf_bytes)


def extract_using_ocr(pdf_bytes):
    try:
        import fitz
        import pytesseract

        from PIL import Image, ImageOps

        # Find Tesseract
        tesseract_path = shutil.which("tesseract")

        if not tesseract_path and os.name == "nt":
            windows_path = (
                r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            )

            if Path(windows_path).is_file():
                tesseract_path = windows_path

        if not tesseract_path:
            raise RuntimeError(
                "Tesseract not found. Check packages.txt."
            )

        pytesseract.pytesseract.tesseract_cmd = tesseract_path

        document = fitz.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        extracted = []

        for index, page in enumerate(document):

            print(
                f"OCR PROCESSING PAGE {index + 1}",
                flush=True
            )

            # Render at 1.5x to reduce processing time
            pix = page.get_pixmap(
                matrix=fitz.Matrix(1.5, 1.5),
                colorspace=fitz.csGRAY,
                alpha=False
            )

            image = Image.frombytes(
                "L",
                (pix.width, pix.height),
                pix.samples
            )

            # Improve contrast
            image = ImageOps.autocontrast(image)

            print(
                f"OCR IMAGE SIZE: {image.size}",
                flush=True
            )

            text = pytesseract.image_to_string(
                image,
                lang="eng",
                config="--oem 1 --psm 3",
                timeout=90
            )

            print(
                f"OCR PAGE {index + 1} CHARACTERS: {len(text)}",
                flush=True
            )

            extracted.append(text)

        document.close()

        result = "\n\n".join(extracted).strip()

        if len(result) < 20:
            raise ValueError(
                "OCR could not extract readable resume text."
            )

        print("OCR EXTRACTION SUCCESS", flush=True)

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
