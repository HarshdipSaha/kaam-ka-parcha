from __future__ import annotations

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from parcha.app import AppServices, create_app
from parcha.session import Conflict, SessionStore
from parcha.workflow import ReplyResult, Workflow
from tests.conftest import FakeExtractor, FakeTimbreClient, make_test_card


class MockPrismaConfidence:
    def __init__(self, transcript: str, confidence: float = 1.0):
        self.transcript = transcript
        self.confidence = confidence

    def transcribe(
        self,
        wav: bytes,
        *,
        mode: str,
        bias: list[str] | None = None,
        score: float = 1.0,
    ) -> str:
        return self.transcript


def test_low_confidence_triggers_digital_fallback():
    store = SessionStore()
    session = store.create()
    card = make_test_card()
    store.set_card(session.id, expected_revision=0, card=card)

    # Low confidence (0.50 < 0.65)
    prisma = MockPrismaConfidence(transcript="haan theek hai", confidence=0.50)
    workflow = Workflow(
        store=store,
        prisma=prisma,
        extractor=FakeExtractor(),
        timbre=FakeTimbreClient(),
        normalize_audio=lambda blob, mime, sample_rate=8000: b"RIFFpcm",
    )
    workflow.start_readback(session.id, expected_revision=1)

    res = workflow.reply(
        session.id,
        b"dummy_audio",
        "audio/webm",
        expected_revision=1,
        readback_revision=1,
    )

    assert isinstance(res, ReplyResult)
    assert res.outcome == "fallback"
    assert "Speech confidence below 0.65" in (res.message or "")
    assert res.session.status == "fallback_ready"
    assert res.session.revision == 1
    assert res.fallback_payload is not None
    assert res.fallback_payload["confidence"] == 0.50
    assert len(res.fallback_payload["actions"]) == 2
    action_types = [a["action"] for a in res.fallback_payload["actions"]]
    assert "approve" in action_types
    assert "request_changes" in action_types

    # Session in store reflects fallback_ready status
    stored = store.get(session.id)
    assert stored.status == "fallback_ready"
    assert stored.logs[-1].mode == "low_confidence_fallback"


def test_repeated_retries_trigger_digital_fallback():
    store = SessionStore()
    session = store.create()
    card = make_test_card()
    store.set_card(session.id, expected_revision=0, card=card)

    # Normal confidence (1.0), but unclear audio
    prisma = MockPrismaConfidence(transcript="kya bola aapne", confidence=1.0)
    workflow = Workflow(
        store=store,
        prisma=prisma,
        extractor=FakeExtractor(),
        timbre=FakeTimbreClient(),
        normalize_audio=lambda blob, mime, sample_rate=8000: b"RIFFpcm",
    )
    workflow.start_readback(session.id, expected_revision=1)

    # Attempt 1: unclear -> retry
    res1 = workflow.reply(
        session.id,
        b"dummy_audio",
        "audio/webm",
        expected_revision=1,
        readback_revision=1,
    )
    assert res1.outcome == "retry"
    assert res1.session.status == "awaiting_reply"

    # Attempt 2: unclear -> retry
    res2 = workflow.reply(
        session.id,
        b"dummy_audio",
        "audio/webm",
        expected_revision=1,
        readback_revision=1,
    )
    assert res2.outcome == "retry"
    assert res2.session.status == "awaiting_reply"

    # Attempt 3: unclear after 2 prior retries -> triggers digital fallback
    res3 = workflow.reply(
        session.id,
        b"dummy_audio",
        "audio/webm",
        expected_revision=1,
        readback_revision=1,
    )
    assert res3.outcome == "fallback"
    assert res3.session.status == "fallback_ready"
    assert res3.fallback_payload is not None
    assert res3.fallback_payload["retries"] == 3


def test_fallback_http_endpoint_approve_and_request_changes(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    app = create_app(fake_services)
    client = TestClient(app)

    session_id = client.post("/sessions").json()["id"]

    # Intake -> revision 1
    client.post(
        f"/sessions/{session_id}/intake",
        data={"expected_revision": 0},
        files={"audio": ("estimate.wav", b"fake speech", "audio/wav")},
    )

    client.post(f"/sessions/{session_id}/reask/items.part-1.amount_paise", data={"expected_revision": 1},
                files={"audio": ("part.wav", b"part correction", "audio/wav")})
    client.post(f"/sessions/{session_id}/reask/items.labour-1.amount_paise", data={"expected_revision": 2},
                files={"audio": ("labour.wav", b"labour correction", "audio/wav")})

    # Readback -> awaiting_reply
    client.post(
        f"/sessions/{session_id}/readback",
        data={"expected_revision": 3},
    )

    # Direct fallback trigger
    fb_trigger_res = client.post(
        f"/sessions/{session_id}/fallback",
        data={"expected_revision": 3, "action": "trigger"},
    )
    assert fb_trigger_res.status_code == 200
    assert fb_trigger_res.json()["status"] == "fallback_ready"
    assert len(fb_trigger_res.json()["actions"]) == 2

    # Approve via fallback -> confirms session
    fb_approve_res = client.post(
        f"/sessions/{session_id}/fallback",
        data={"expected_revision": 3, "action": "approve"},
    )
    assert fb_approve_res.status_code == 200
    assert fb_approve_res.json()["status"] == "confirmed"

    # Calling fallback again on confirmed session returns 409 Conflict
    fb_stale_res = client.post(
        f"/sessions/{session_id}/fallback",
        data={"expected_revision": 3, "action": "approve"},
    )
    assert fb_stale_res.status_code == 409

    # Calling with mismatched revision returns 409
    fb_wrong_rev = client.post(
        f"/sessions/{session_id}/fallback",
        data={"expected_revision": 99, "action": "approve"},
    )
    assert fb_wrong_rev.status_code == 409

    # Unknown session returns 404
    fb_unknown = client.post(
        "/sessions/unknown-fallback-session/fallback",
        data={"expected_revision": 1, "action": "approve"},
    )
    assert fb_unknown.status_code == 404


def test_fallback_http_endpoint_request_changes(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    app = create_app(fake_services)
    client = TestClient(app)

    session_id = client.post("/sessions").json()["id"]

    # Intake -> revision 1
    client.post(
        f"/sessions/{session_id}/intake",
        data={"expected_revision": 0},
        files={"audio": ("estimate.wav", b"fake speech", "audio/wav")},
    )

    client.post(f"/sessions/{session_id}/reask/items.part-1.amount_paise", data={"expected_revision": 1},
                files={"audio": ("part.wav", b"part correction", "audio/wav")})
    client.post(f"/sessions/{session_id}/reask/items.labour-1.amount_paise", data={"expected_revision": 2},
                files={"audio": ("labour.wav", b"labour correction", "audio/wav")})

    # Readback -> awaiting_reply
    client.post(
        f"/sessions/{session_id}/readback",
        data={"expected_revision": 3},
    )

    # Request changes via digital fallback -> moves to review
    fb_change_res = client.post(
        f"/sessions/{session_id}/fallback",
        data={"expected_revision": 3, "action": "request_changes"},
    )
    assert fb_change_res.status_code == 200
    assert fb_change_res.json()["status"] == "review"
    assert fb_change_res.json()["readback_revision"] is None


def test_customer_reply_low_confidence_e2e_http(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    fake_services.workflow.prisma.confidence = 0.45  # Low confidence
    app = create_app(fake_services)
    client = TestClient(app)

    session_id = client.post("/sessions").json()["id"]

    client.post(
        f"/sessions/{session_id}/intake",
        data={"expected_revision": 0},
        files={"audio": ("estimate.wav", b"fake speech", "audio/wav")},
    )

    client.post(f"/sessions/{session_id}/reask/items.part-1.amount_paise", data={"expected_revision": 1},
                files={"audio": ("part.wav", b"part correction", "audio/wav")})
    client.post(f"/sessions/{session_id}/reask/items.labour-1.amount_paise", data={"expected_revision": 2},
                files={"audio": ("labour.wav", b"labour correction", "audio/wav")})

    client.post(
        f"/sessions/{session_id}/readback",
        data={"expected_revision": 3},
    )

    # Reply over degraded line
    reply_res = client.post(
        f"/sessions/{session_id}/reply",
        data={"expected_revision": 3, "readback_revision": 3},
        files={"audio": ("reply.wav", b"degraded speech", "audio/wav")},
    )
    assert reply_res.status_code == 200
    data = reply_res.json()
    assert data["outcome"] == "fallback"
    assert data["status"] == "fallback_ready"
    assert data["fallback_payload"]["confidence"] == 0.45

    # Customer taps "Approve Estimate"
    approve_res = client.post(
        f"/sessions/{session_id}/fallback",
        data={"expected_revision": 3, "action": "approve"},
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "confirmed"

    # PDF can be retrieved for confirmed estimate
    pdf_res = client.get(f"/sessions/{session_id}/pdf")
    assert pdf_res.status_code == 200
    assert len(pdf_res.content) > 0
