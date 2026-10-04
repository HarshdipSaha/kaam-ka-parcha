from datetime import datetime, timezone
from io import BytesIO
import json
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from parcha.app import AppServices
from parcha.artefact import render_pdf, whatsapp_text
from parcha.schema import TranscriptLog
from parcha.session import Conflict, Session
from tests.conftest import make_test_card


def test_unconfirmed_session_raises_conflict():
    # 1. Draft session with no card
    s1 = Session(id="test-1", status="draft")
    with pytest.raises(Conflict, match="session is not confirmed"):
        render_pdf(s1)
    with pytest.raises(Conflict, match="session is not confirmed"):
        whatsapp_text(s1)

    # 2. Review session with card but not confirmed
    card = make_test_card()
    s2 = Session(id="test-2", status="review", card=card)
    with pytest.raises(Conflict, match="session is not confirmed"):
        render_pdf(s2)
    with pytest.raises(Conflict, match="session is not confirmed"):
        whatsapp_text(s2)

    # 3. Awaiting reply session but not confirmed
    s3 = Session(id="test-3", status="awaiting_reply", card=card)
    with pytest.raises(Conflict, match="session is not confirmed"):
        render_pdf(s3)
    with pytest.raises(Conflict, match="session is not confirmed"):
        whatsapp_text(s3)

    # 4. Status is confirmed but confirmed_at_utc is None
    s4 = Session(id="test-4", status="confirmed", card=card, confirmed_at_utc=None)
    with pytest.raises(Conflict, match="session is not confirmed"):
        render_pdf(s4)
    with pytest.raises(Conflict, match="session is not confirmed"):
        whatsapp_text(s4)

    # 5. Status confirmed and confirmed_at_utc present, but card is None
    s5 = Session(
        id="test-5",
        status="confirmed",
        card=None,
        confirmed_at_utc=datetime.now(timezone.utc),
    )
    with pytest.raises(Conflict, match="session is not confirmed"):
        render_pdf(s5)
    with pytest.raises(Conflict, match="session is not confirmed"):
        whatsapp_text(s5)


def test_pdf_embeds_exact_transcripts():
    card = make_test_card()
    now = datetime(2026, 10, 5, 14, 30, 0, tzinfo=timezone.utc)
    logs = (
        TranscriptLog(
            role="mechanic",
            mode="intake",
            text="Agla brake pad badalna hai ₹450, aur labour ₹200",
            recorded_at_utc=datetime(2026, 10, 5, 14, 0, 0, tzinfo=timezone.utc),
        ),
        TranscriptLog(
            role="customer",
            mode="reply",
            text="हाँ, बिल्कुल ठीक है",
            recorded_at_utc=datetime(2026, 10, 5, 14, 25, 0, tzinfo=timezone.utc),
        ),
    )
    session = Session(
        id="sess-xyz-123",
        revision=2,
        status="confirmed",
        card=card,
        logs=logs,
        confirmed_at_utc=now,
    )

    pdf_bytes = render_pdf(session)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")

    # Read the generated PDF
    reader = PdfReader(BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1
    page_text = reader.pages[0].extract_text()

    # Verify content in the PDF canvas
    assert "Kaam ka Parcha" in page_text
    assert "KA-01-AB-1234" in page_text
    assert "sess-xyz-123" in page_text
    assert "Total Amount:" in page_text
    assert "650" in page_text
    assert "Promised Delivery:" in page_text

    # Verify transcripts.json attachment
    assert "transcripts.json" in reader.attachments
    attach_data = reader.attachments["transcripts.json"][0]
    raw_json = attach_data if isinstance(attach_data, bytes) else attach_data.get_data()

    payload = json.loads(raw_json.decode("utf-8"))
    assert payload["session_id"] == "sess-xyz-123"
    assert payload["revision"] == 2
    assert payload["confirmed_at_utc"] == now.isoformat()
    assert len(payload["logs"]) == 2
    assert payload["logs"][0]["role"] == "mechanic"
    assert payload["logs"][0]["mode"] == "intake"
    assert payload["logs"][0]["text"] == "Agla brake pad badalna hai ₹450, aur labour ₹200"
    assert payload["logs"][1]["role"] == "customer"
    assert payload["logs"][1]["mode"] == "reply"
    assert payload["logs"][1]["text"] == "हाँ, बिल्कुल ठीक है"


def test_whatsapp_text_has_derived_total_and_no_delivery_claim():
    card = make_test_card()
    now = datetime(2026, 10, 5, 14, 30, 0, tzinfo=timezone.utc)
    session = Session(
        id="sess-wa-456",
        revision=1,
        status="confirmed",
        card=card,
        confirmed_at_utc=now,
    )

    text = whatsapp_text(session)
    assert "*Kaam ka Parcha — confirmed*" in text
    assert "Session: sess-wa-456 (rev 1)" in text
    assert f"Confirmed: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}" in text
    assert "*Items:*" in text
    assert "front brake pad (part): ₹450" in text
    assert "labour (labour): ₹200" in text
    assert "*Total:* ₹650" in text
    assert "*Delivery:* 2026-10-05 (evening)" in text
    assert "_Note: Simulated phone line; No real call was placed. All demo identities and data are synthetic._" in text

    # Verify no claim that message was sent / delivered
    assert "sent" not in text.lower()
    assert "delivered" not in text.lower()


def test_app_endpoints_serve_pdf_and_text_when_confirmed(
    client: TestClient, fake_services: AppServices
):
    session = fake_services.store.create()
    card = make_test_card()
    fake_services.store.set_card(
        session.id, expected_revision=session.revision, card=card
    )
    fake_services.store.start_readback(session.id, expected_revision=1)
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    confirmed_session = fake_services.store.confirm(
        session.id, expected_revision=1, when=now
    )

    # Test PDF endpoint
    resp_pdf = client.get(f"/sessions/{session.id}/parcha.pdf")
    assert resp_pdf.status_code == 200
    assert resp_pdf.headers["content-type"] == "application/pdf"
    assert (
        resp_pdf.headers["content-disposition"]
        == f'attachment; filename="parcha-{session.id}-rev{confirmed_session.revision}.pdf"'
    )
    assert resp_pdf.content.startswith(b"%PDF-")

    # Also test PDF alias
    resp_pdf_alias = client.get(f"/sessions/{session.id}/pdf")
    assert resp_pdf_alias.status_code == 200
    assert resp_pdf_alias.content.startswith(b"%PDF-")

    # Test WhatsApp text endpoint
    resp_txt = client.get(f"/sessions/{session.id}/whatsapp.txt")
    assert resp_txt.status_code == 200
    assert resp_txt.headers["content-type"].startswith("text/plain")
    assert (
        resp_txt.headers["content-disposition"]
        == f'attachment; filename="parcha-{session.id}.txt"'
    )
    assert "*Kaam ka Parcha — confirmed*" in resp_txt.text
    assert "*Total:* ₹650" in resp_txt.text
    assert "sent" not in resp_txt.text.lower()

    # Also test WhatsApp alias
    resp_txt_alias = client.get(f"/sessions/{session.id}/whatsapp")
    assert resp_txt_alias.status_code == 200
    assert "*Kaam ka Parcha — confirmed*" in resp_txt_alias.text


def test_app_endpoints_return_409_before_confirmed(
    client: TestClient, fake_services: AppServices
):
    session = fake_services.store.create()

    # Draft session: should return 409
    pdf_resp = client.get(f"/sessions/{session.id}/parcha.pdf")
    assert pdf_resp.status_code == 409
    assert "session is not confirmed" in pdf_resp.text

    txt_resp = client.get(f"/sessions/{session.id}/whatsapp.txt")
    assert txt_resp.status_code == 409
    assert "session is not confirmed" in txt_resp.text

    # Review status: should still return 409
    fake_services.store.set_card(
        session.id, expected_revision=session.revision, card=make_test_card()
    )
    assert client.get(f"/sessions/{session.id}/parcha.pdf").status_code == 409
    assert client.get(f"/sessions/{session.id}/whatsapp.txt").status_code == 409

    # Awaiting reply status: should still return 409
    fake_services.store.start_readback(session.id, expected_revision=1)
    assert client.get(f"/sessions/{session.id}/parcha.pdf").status_code == 409
    assert client.get(f"/sessions/{session.id}/whatsapp.txt").status_code == 409

    # Unknown session: should return 404
    assert client.get("/sessions/unknown-session-id/parcha.pdf").status_code == 404
    assert client.get("/sessions/unknown-session-id/whatsapp.txt").status_code == 404
