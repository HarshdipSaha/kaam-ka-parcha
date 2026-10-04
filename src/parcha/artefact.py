from datetime import datetime
from io import BytesIO
import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from pypdf import PdfReader, PdfWriter

from .session import Conflict, Session
from .workflow import format_rupees


def attach_transcripts(pdf_bytes: bytes, session: Session) -> bytes:
    evidence = {
        "session_id": session.id,
        "revision": session.revision,
        "confirmed_at_utc": session.confirmed_at_utc.isoformat() if session.confirmed_at_utc else None,
        "logs": [
            {
                "role": log.role,
                "mode": log.mode,
                "text": log.text,
                "recorded_at_utc": log.recorded_at_utc.isoformat(),
            }
            for log in session.logs
        ],
    }
    writer = PdfWriter()
    writer.append_pages_from_reader(PdfReader(BytesIO(pdf_bytes)))
    writer.add_attachment(
        "transcripts.json",
        json.dumps(evidence, ensure_ascii=False, indent=2).encode("utf-8"),
    )
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def render_pdf(session: Session) -> bytes:
    if (
        session.status != "confirmed"
        or session.confirmed_at_utc is None
        or session.card is None
    ):
        raise Conflict("session is not confirmed")

    try:
        total_paise = session.card.total_paise
    except (ValueError, AttributeError):
        raise Conflict("session is not confirmed")

    buffer = BytesIO()
    c = Canvas(buffer, pagesize=A4)

    # Workshop header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "Kaam ka Parcha — Work Estimate & Job Card (Demo)")

    # Synthetic vehicle and metadata
    c.setFont("Helvetica", 10)
    c.drawString(50, 775, "Vehicle: KA-01-AB-1234 (Synthetic Demo)")
    c.drawString(50, 760, f"Session: {session.id} | Revision: {session.revision}")
    c.drawString(50, 745, f"Confirmed (UTC): {session.confirmed_at_utc.isoformat()}")

    # Simulation notice
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(
        50,
        725,
        "Simulated phone line: G.711 / AMR-NB + street noise at 5 dB. No real call was placed.",
    )

    # Separator
    c.setLineWidth(1)
    c.line(50, 715, 545, 715)

    # Items section
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 695, "Items:")

    c.setFont("Helvetica", 10)
    y = 675
    for item in session.card.items:
        label = item.label or "Item"
        amount_paise = item.amount_paise if item.amount_paise is not None else 0
        amount_str = format_rupees(amount_paise).replace("₹", "Rs. ")
        c.drawString(50, y, f"{label} ({item.kind}): {amount_str}")
        y -= 20

    y -= 5
    # Total
    c.setFont("Helvetica-Bold", 11)
    total_str = format_rupees(total_paise).replace("₹", "Rs. ")
    c.drawString(50, y, f"Total Amount: {total_str}")
    y -= 25

    # Delivery
    c.setFont("Helvetica", 10)
    if session.card.delivery:
        c.drawString(
            50,
            y,
            f"Promised Delivery: {session.card.delivery.date} ({session.card.delivery.window}) - Spoken: '{session.card.delivery.spoken}'",
        )
    else:
        c.drawString(50, y, "Promised Delivery: Not specified")

    c.showPage()
    c.save()

    raw_pdf = buffer.getvalue()
    return attach_transcripts(raw_pdf, session)


def whatsapp_text(session: Session) -> str:
    if (
        session.status != "confirmed"
        or session.confirmed_at_utc is None
        or session.card is None
    ):
        raise Conflict("session is not confirmed")

    try:
        total_paise = session.card.total_paise
    except (ValueError, AttributeError):
        raise Conflict("session is not confirmed")

    itemized_lines = "\n".join(
        f"- {item.label} ({item.kind}): {format_rupees(item.amount_paise if item.amount_paise is not None else 0)}"
        for item in session.card.items
    )

    delivery_str = (
        f"{session.card.delivery.date.isoformat()} ({session.card.delivery.window})"
        if session.card.delivery
        else "Not specified"
    )

    message = (
        f"*Kaam ka Parcha — confirmed*\n"
        f"Session: {session.id} (rev {session.revision})\n"
        f"Confirmed: {session.confirmed_at_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        f"*Items:*\n"
        f"{itemized_lines}\n\n"
        f"*Total:* {format_rupees(total_paise)}\n"
        f"*Delivery:* {delivery_str}\n\n"
        f"_Note: Simulated phone line; No real call was placed. All demo identities and data are synthetic._"
    )

    assert "sent" not in message.lower(), "Must not claim WhatsApp message was sent"
    return message
