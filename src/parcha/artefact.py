from datetime import datetime
import hashlib
from io import BytesIO
import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from pypdf import PdfReader, PdfWriter

from .session import Conflict, Session
from .workflow import format_rupees


def audit_manifest(session: Session) -> dict:
    """Return the exact evidence covered by the PDF and attachment digest."""
    return {
        "session_id": session.id,
        "revision": session.revision,
        "confirmed_at_utc": session.confirmed_at_utc.isoformat() if session.confirmed_at_utc else None,
        "dpdp_consent": {
            "granted": session.dpdp_consent_granted,
            "recorded_at_utc": session.dpdp_consent_at_utc.isoformat() if session.dpdp_consent_at_utc else None,
            "user_agent": session.dpdp_user_agent,
            "consent_sha256": session.dpdp_consent_sha256,
        },
        "logs": [
            {
                "role": log.role,
                "mode": log.mode,
                "text": log.text,
                "recorded_at_utc": log.recorded_at_utc.isoformat(),
                "audio_sha256": log.audio_sha256,
            }
            for log in session.logs
        ],
    }


def audit_manifest_sha256(session: Session) -> str:
    canonical_manifest = json.dumps(
        audit_manifest(session), ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(canonical_manifest).hexdigest()


def attach_transcripts(pdf_bytes: bytes, session: Session) -> bytes:
    evidence = audit_manifest(session)
    evidence["audit_manifest_sha256"] = audit_manifest_sha256(session)

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
    c.drawString(50, 805, "Kaam ka Parcha — Work Estimate & Job Card (Demo)")

    # Dynamic verification QR code in top right
    qr_url = f"/verify/{session.id}"
    qr_widget = QrCodeWidget(qr_url)
    b = qr_widget.getBounds()
    w = b[2] - b[0]
    h = b[3] - b[1]
    qr_size = 65
    d = Drawing(qr_size, qr_size, transform=[qr_size / w, 0, 0, qr_size / h, 0, 0])
    d.add(qr_widget)
    renderPDF.draw(d, c, 475, 735)

    c.setFont("Helvetica", 6)
    c.drawRightString(540, 725, "Scan to Verify Audio")

    # Synthetic vehicle and metadata
    c.setFont("Helvetica", 10)
    c.drawString(50, 785, "Vehicle: KA-01-AB-1234 (Synthetic Demo)")
    c.drawString(50, 772, f"Session: {session.id} | Revision: {session.revision}")
    c.drawString(50, 759, f"Confirmed (UTC): {session.confirmed_at_utc.isoformat()}")
    audit_digest = audit_manifest_sha256(session)
    c.setFont("Helvetica", 7)
    c.drawString(50, 746, f"Audit manifest SHA-256: {audit_digest}")

    intake_log = next((l for l in session.logs if l.role == "mechanic" and l.audio_sha256), None)
    customer_log = next((l for l in session.logs if l.role == "customer" and l.audio_sha256), None)
    if intake_log and intake_log.audio_sha256:
        c.setFont("Helvetica", 6.5)
        c.drawString(50, 735, f"Intake Audio SHA-256: {intake_log.audio_sha256}")
    if customer_log and customer_log.audio_sha256:
        c.setFont("Helvetica", 6.5)
        c.drawString(50, 725, f"Confirmation Audio SHA-256: {customer_log.audio_sha256}")

    if session.dpdp_consent_granted and session.dpdp_consent_sha256:
        c.setFont("Helvetica", 6.5)
        c.drawString(
            50,
            715,
            f"DPDP Act 2023 Statutory Consent: Granted (SHA-256: {session.dpdp_consent_sha256[:24]}...)",
        )
    else:
        c.setFont("Helvetica-Oblique", 6.5)
        c.drawString(50, 715, "DPDP Act 2023 Statutory Consent: Not Recorded")

    # Simulation notice
    c.setFont("Helvetica-Oblique", 8.5)
    c.drawString(
        50,
        702,
        "Simulated phone line: G.711 + recorded engine ambience at 5 dB. No real call was placed.",
    )

    # Separator
    c.setLineWidth(1)
    c.line(50, 692, 545, 692)

    # Items section
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 674, "Items:")

    c.setFont("Helvetica", 10)
    y = 654
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
