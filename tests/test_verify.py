from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from parcha.app import AppServices, create_app
from parcha.artefact import render_pdf
from parcha.schema import Delivery, LineItem, TranscriptLog
from parcha.session import Session, SessionStore
from tests.conftest import make_test_card


def test_verify_html_and_json_responses(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    app = create_app(fake_services)
    client = TestClient(app)

    session_id = client.post("/sessions").json()["id"]

    # Intake
    client.post(
        f"/sessions/{session_id}/intake",
        data={"expected_revision": 0},
        files={"audio": ("estimate.wav", b"fake intake audio", "audio/wav")},
    )

    # Readback
    client.post(
        f"/sessions/{session_id}/readback",
        data={"expected_revision": 1},
    )

    # Reply (confirms session)
    fake_services.workflow.prisma.transcribe = lambda wav, mode, **kw: "haan theek hai"
    client.post(
        f"/sessions/{session_id}/reply",
        data={"expected_revision": 1, "readback_revision": 1},
        files={"audio": ("reply.wav", b"fake reply audio", "audio/wav")},
    )

    # 1. HTML Verification Page
    html_res = client.get(f"/verify/{session_id}")
    assert html_res.status_code == 200
    assert "text/html" in html_res.headers["content-type"]
    body = html_res.text
    assert "BSA 2023" in body
    assert "Compliant" in body
    assert "Audit Verification" in body
    assert session_id in body
    assert "KA-01-AB-1234" in body
    assert f"/sessions/{session_id}/intake.wav" in body
    assert f"/sessions/{session_id}/reply.wav" in body
    assert "front brake pad" in body

    # 2. JSON Verification Response
    json_res = client.get(f"/verify/{session_id}?format=json")
    assert json_res.status_code == 200
    data = json_res.json()
    assert data["session_id"] == session_id
    assert data["status"] == "confirmed"
    assert data["vehicle"] == "KA-01-AB-1234 (Synthetic Demo)"
    assert "audit_manifest_sha256" in data
    assert len(data["audit_manifest_sha256"]) == 64
    assert data["intake"]["audio_url"] == f"/sessions/{session_id}/intake.wav"
    assert data["confirmation"]["audio_url"] == f"/sessions/{session_id}/reply.wav"
    assert "Bharatiya Sakshya Adhiniyam, 2023" in data["legal_compliance"]

    # 3. Audio streaming endpoints
    intake_audio_res = client.get(f"/sessions/{session_id}/intake.wav")
    assert intake_audio_res.status_code == 200
    assert intake_audio_res.headers["content-type"] == "audio/wav"
    assert len(intake_audio_res.content) > 0

    reply_audio_res = client.get(f"/sessions/{session_id}/reply.wav")
    assert reply_audio_res.status_code == 200
    assert reply_audio_res.headers["content-type"] == "audio/wav"
    assert len(reply_audio_res.content) > 0


def test_verify_unknown_session_returns_404(fake_services):
    app = create_app(fake_services)
    client = TestClient(app)

    res = client.get("/verify/unknown-session-12345")
    assert res.status_code == 404
    assert res.json()["detail"] == "unknown session"

    res_audio = client.get("/sessions/unknown-session-12345/intake.wav")
    assert res_audio.status_code == 404


def test_pdf_contains_scannable_qr_code_and_audio_hashes():
    card = make_test_card()
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    logs = (
        TranscriptLog(
            role="mechanic",
            mode="intake",
            text="brake pad 450",
            recorded_at_utc=now,
            audio_sha256="1" * 64,
        ),
        TranscriptLog(
            role="customer",
            mode="reply",
            text="haan theek hai",
            recorded_at_utc=now,
            audio_sha256="2" * 64,
        ),
    )
    session = Session(
        id="qr-test-sess-99",
        revision=1,
        status="confirmed",
        card=card,
        logs=logs,
        confirmed_at_utc=now,
    )

    pdf_bytes = render_pdf(session)
    reader = PdfReader(BytesIO(pdf_bytes))
    page_text = reader.pages[0].extract_text()

    assert "Scan to Verify Audio" in page_text
    assert f"qr-test-sess-99" in page_text
    assert "Intake Audio SHA-256:" in page_text
    assert "Confirmation Audio SHA-256:" in page_text
    assert "1" * 16 in page_text
    assert "2" * 16 in page_text
