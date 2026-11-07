
import re
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    KeepTogether,
)


def clean_markdown(text):
    """Convert common Markdown syntax into readable PDF text."""
    text = str(text or "").replace("\r\n", "\n")

    # Remove code fences but keep code content
    text = re.sub(r"```[^\n]*\n?", "", text)

    # Replace Markdown images and links
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"[Image: \1]", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove bold and italic markers
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.*?)\*(?!\*)", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)

    # Remove heading markers
    text = re.sub(
        r"^\s{0,3}#{1,6}\s*",
        "",
        text,
        flags=re.MULTILINE,
    )

    # Convert Markdown bullets
    text = re.sub(
        r"^\s*[-*]\s+",
        "• ",
        text,
        flags=re.MULTILINE,
    )

    return text


def add_page_number(canvas, doc):
    """Draw footer page number."""
    canvas.saveState()

    page_number = canvas.getPageNumber()
    page_text = f"AI Interview Report | Page {page_number}"

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)

    canvas.drawRightString(
        A4[0] - 0.65 * inch,
        0.35 * inch,
        page_text,
    )

    canvas.restoreState()


def add_evaluation_report(story, report, body_style):
    """Add evaluation report content to PDF."""
    clean_text = clean_markdown(report).strip()

    for line in clean_text.splitlines():
        line = line.strip()

        if not line:
            story.append(Spacer(1, 4))
            continue

        safe_line = escape(line)
        story.append(Paragraph(safe_line, body_style))
        story.append(Spacer(1, 3))


def generate_interview_pdf(report, answers):
    """Generate and return interview report as PDF bytes."""

    if report is None:
        raise ValueError("Evaluation report is missing.")

    if answers is None:
        raise ValueError("Interview answers are missing.")

    if not isinstance(answers, (list, tuple)):
        raise TypeError("Answers must be a list.")

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title="AI Interview Performance Report",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=25,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1D4ED8"),
        spaceAfter=12,
    )

    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=17,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        spaceAfter=5,
        wordWrap="CJK",
    )

    story = []

    # Report title
    story.append(
        Paragraph(
            "AI Interview Performance Report",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Mock Interview Evaluation | AI-generated practice report",
            body_style,
        )
    )

    story.append(Spacer(1, 10))

    # Evaluation section
    story.append(
        Paragraph(
            "Performance Summary &amp; AI Feedback",
            heading_style,
        )
    )

    story.append(HRFlowable(width="100%", thickness=0.7))
    story.append(Spacer(1, 8))

    add_evaluation_report(
        story,
        str(report),
        body_style,
    )

    # Questions and answers section
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Interview Questions &amp; Candidate Answers",
            heading_style,
        )
    )

    story.append(HRFlowable(width="100%", thickness=0.7))
    story.append(Spacer(1, 8))

    for index, item in enumerate(answers, start=1):

        if not isinstance(item, dict):
            item = {}

        question_text = str(item.get("question") or "").strip()
        answer_text = str(item.get("answer") or "").strip()

        question = escape(
            question_text or "Question text unavailable"
        )

        answer = escape(answer_text or "No answer")

        question_elements = [
            Paragraph(
                f"Question {index}",
                heading_style,
            ),
            Paragraph(
                f"<b>Question:</b> {question}",
                body_style,
            ),
            Paragraph(
                f"<b>Your Answer:</b> {answer}",
                body_style,
            ),
            Spacer(1, 8),
        ]

        # Keep short Q&A together
        if len(question_text) + len(answer_text) < 1800:
            story.append(KeepTogether(question_elements))
        else:
            story.extend(question_elements)

    # Disclaimer
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Disclaimer: Scores and feedback are approximate AI "
            "practice estimates and are not official hiring decisions.",
            body_style,
        )
    )

    # Build PDF
    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    pdf_bytes = buffer.getvalue()
    buffer.close()

    if not pdf_bytes.startswith(b"%PDF"):
        raise ValueError(
            "PDF generation did not produce a valid PDF."
        )

    return pdf_bytes
