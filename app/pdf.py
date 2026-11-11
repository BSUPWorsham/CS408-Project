"""Intake PDF summaries built with ReportLab.

generate_intake_pdf() writes one PDF per intake into PDF_FOLDER
(app/static/uploads/pdfs/) and returns the file name, which the intake route
stores in Intakes.pdf_filename.

File names include a random token (intake_12_k3J9...pdf) so a client's PDF
can't be found by guessing another intake number.
"""
import os
import secrets
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FIRM_NAME = "Aplin Law"
FIRM_LINE = "Social Security Disability  |  Boise, Idaho  |  (208) 555-0100"
SPRUCE = colors.HexColor("#1f4d3f")
LINE = colors.HexColor("#c9d4ce")


def _styles():
    base = getSampleStyleSheet()
    return {
        "firm": ParagraphStyle("firm", parent=base["Title"], fontName="Helvetica-Bold",
                               fontSize=20, textColor=SPRUCE, alignment=0, spaceAfter=2),
        "firmline": ParagraphStyle("firmline", parent=base["Normal"], fontSize=9,
                                   textColor=colors.HexColor("#5b6863")),
        "title": ParagraphStyle("title", parent=base["Heading1"], fontSize=15, spaceBefore=14, spaceAfter=4),
        "meta": ParagraphStyle("meta", parent=base["Normal"], fontSize=9, alignment=TA_RIGHT,
                               textColor=colors.HexColor("#5b6863")),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=12, textColor=SPRUCE,
                             spaceBefore=12, spaceAfter=6),
        "label": ParagraphStyle("label", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10),
        "body": ParagraphStyle("body", parent=base["Normal"], fontSize=10, leading=14),
        "small": ParagraphStyle("small", parent=base["Normal"], fontSize=8, leading=11,
                                textColor=colors.HexColor("#5b6863")),
    }


def _text(value):
    """Escape user text for ReportLab's mini-HTML and keep the client's line breaks."""
    return escape(str(value or "")).replace("\n", "<br/>")


def _field_table(rows, styles):
    data = [[Paragraph(label, styles["label"]), Paragraph(_text(value), styles["body"])]
            for label, value in rows]
    table = Table(data, colWidths=[1.8 * inch, 4.7 * inch])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#5b6863"))
    canvas.drawString(doc.leftMargin, 0.5 * inch, "Confidential client intake. Not legal advice.")
    canvas.drawRightString(LETTER[0] - doc.rightMargin, 0.5 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_intake_pdf(intake, path):
    """Write the summary for one Intake row to `path`."""
    styles = _styles()
    submitted = intake.submitted_at or datetime.now(timezone.utc)
    doc = SimpleDocTemplate(
        path, pagesize=LETTER,
        leftMargin=inch, rightMargin=inch, topMargin=0.8 * inch, bottomMargin=0.9 * inch,
        title=f"Client Intake #{intake.intake_id}", author=FIRM_NAME,
        subject="Client intake summary",
        pageCompression=0,  # keeps text searchable in tests; files stay small
    )
    story = [
        Paragraph(FIRM_NAME, styles["firm"]),
        Paragraph(FIRM_LINE, styles["firmline"]),
        Paragraph("Client Intake Summary", styles["title"]),
        Paragraph(f"Reference #{intake.intake_id}  |  Submitted {submitted:%B %d, %Y %H:%M} UTC  |  "
                  f"Status: {_text(intake.status)}", styles["meta"]),
        Spacer(1, 6),
        Paragraph("Contact", styles["h2"]),
        _field_table([
            ("Name", intake.client_name),
            ("Email", intake.client_email),
            ("Phone", intake.client_phone),
        ], styles),
        Paragraph("Situation", styles["h2"]),
        _field_table([
            ("Age category", intake.age_category),
            ("Tried accommodations", "Yes" if intake.tried_accommodations else "No"),
        ], styles),
        Paragraph("Injury or condition", styles["h2"]),
        Paragraph(_text(intake.disability_details), styles["body"]),
        Paragraph("Case summary", styles["h2"]),
        Paragraph(_text(intake.case_summary), styles["body"]),
        Spacer(1, 18),
        Paragraph("This summary was generated from answers submitted through the Aplin Law website. "
                  "Submitting an intake does not create an attorney-client relationship. "
                  "Please keep this copy for your records.", styles["small"]),
    ]
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)


def generate_intake_pdf(intake, folder):
    """Create the PDF for `intake` in `folder` and return its file name."""
    os.makedirs(folder, exist_ok=True)
    filename = f"intake_{intake.intake_id}_{secrets.token_urlsafe(12)}.pdf"
    build_intake_pdf(intake, os.path.join(folder, filename))
    return filename