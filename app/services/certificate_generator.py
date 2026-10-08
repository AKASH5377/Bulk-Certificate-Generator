from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


OUTPUT_DIR = Path("generated_certificates")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_certificate(
    name: str,
    course: str,
    event_name: str,
    event_date: str,
    certificate_title: str,
    certificate_id: str,
) -> str:
    safe_id = "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in certificate_id
    )
    file_path = OUTPUT_DIR / f"{safe_id}.pdf"

    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(str(file_path), pagesize=(page_width, page_height))

    # Border
    margin = 15 * mm
    pdf.setLineWidth(2)
    pdf.rect(
        margin,
        margin,
        page_width - 2 * margin,
        page_height - 2 * margin,
    )

    # Header
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(
        page_width / 2,
        page_height - 55 * mm,
        certificate_title,
    )

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(
        page_width / 2,
        page_height - 70 * mm,
        "This certificate is proudly presented to",
    )

    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(
        page_width / 2,
        page_height - 90 * mm,
        name,
    )

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(
        page_width / 2,
        page_height - 110 * mm,
        f"for successfully completing: {course}",
    )

    pdf.drawCentredString(
        page_width / 2,
        page_height - 125 * mm,
        f"{event_name} | {event_date}",
    )

    pdf.setFont("Helvetica", 9)
    pdf.drawString(
        margin + 5 * mm,
        margin + 7 * mm,
        f"Certificate ID: {certificate_id}",
    )

    pdf.drawRightString(
        page_width - margin - 5 * mm,
        margin + 7 * mm,
        "Bulk Certificate Generator",
    )

    pdf.save()
    return str(file_path)
