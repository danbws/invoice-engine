"""Invoice PDF rendering with ReportLab.

Layout mirrors the classic Brazilian DANFE spirit: header with issuer and
document number, customer block, items table, totals — without pretending to
be a legally valid fiscal document.
"""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

from .config import settings
from .models import Invoice, InvoiceStatus

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Title"], fontSize=16, spaceAfter=2)
SMALL = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
CANCELLED = ParagraphStyle(
    "Cancelled", parent=styles["Title"], fontSize=22, textColor=colors.HexColor("#cc2244")
)


def render_invoice_pdf(invoice: Invoice) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Invoice {invoice.display_number}",
    )

    story = [
        Paragraph(settings.company_name, H1),
        Paragraph(f"Tax ID: {settings.company_tax_id}", SMALL),
        Spacer(1, 6 * mm),
        Paragraph(f"<b>INVOICE {invoice.display_number}</b>", styles["Heading2"]),
        Paragraph(
            f"Issued at: {invoice.issued_at:%Y-%m-%d %H:%M UTC}" if invoice.issued_at else "",
            SMALL,
        ),
        Spacer(1, 4 * mm),
        Paragraph(f"<b>Customer:</b> {invoice.customer_name}", styles["Normal"]),
    ]
    if invoice.customer_tax_id:
        story.append(Paragraph(f"<b>Customer tax ID:</b> {invoice.customer_tax_id}", styles["Normal"]))
    story.append(Spacer(1, 6 * mm))

    if invoice.status == InvoiceStatus.CANCELLED:
        story.append(Paragraph("CANCELLED", CANCELLED))
        story.append(Paragraph(f"Reason: {invoice.cancel_reason}", styles["Normal"]))
        story.append(Spacer(1, 6 * mm))

    rows = [["#", "Description", "Qty", "Unit price", "Amount"]]
    for n, item in enumerate(invoice.items, start=1):
        rows.append(
            [
                str(n),
                item.description,
                f"{item.quantity:g}",
                f"{item.unit_price:,.2f}",
                f"{item.quantity * item.unit_price:,.2f}",
            ]
        )
    rows.append(["", "", "", "Total", f"{invoice.total:,.2f}"])

    table = Table(rows, colWidths=[10 * mm, 90 * mm, 20 * mm, 28 * mm, 28 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -2), 0.4, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (3, -1), (-1, -1), "Helvetica-Bold"),
                ("LINEABOVE", (3, -1), (-1, -1), 0.8, colors.black),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    story.append(table)

    if invoice.notes:
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(f"<b>Notes:</b> {invoice.notes}", styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()
