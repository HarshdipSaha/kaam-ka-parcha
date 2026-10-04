from __future__ import annotations

import io
from pathlib import Path
import wave
import numpy as np
import pytest
from fastapi.testclient import TestClient

from parcha.app import AppServices, create_app
from parcha.audio import _write_pcm
from parcha.schema import JobCard, LineItem
from parcha.session import Conflict, SessionStore
from parcha.workflow import Readback, Workflow, format_rupees, make_readback
from tests.conftest import FakeExtractor, FakePrisma, FakeTimbreClient, make_test_card


def test_make_readback_formats_card_and_total():
    assert format_rupees(0) == "₹0"
    assert format_rupees(45000) == "₹450"
    assert format_rupees(20000) == "₹200"
    assert format_rupees(65000) == "₹650"
    assert format_rupees(65050) == "₹650.50"
    assert format_rupees(12345) == "₹123.45"

    card = make_test_card()
    text = make_readback(card)
    expected = (
        "front brake pad: ₹450, labour: ₹200. "
        "कुल ₹650. "
        "डिलीवरी Somvaar shaam tak. "
        "ठीक है? हाँ कहें, या सुधार बताएं।"
    )
    assert text == expected

    # Fractional rupees in item
    fractional_card = card.model_copy(
        update={
            "items": (
                LineItem(id="part-1", label="spark plug", kind="part", amount_paise=15050),
            )
        }
    )
    fractional_text = make_readback(fractional_card)
    assert "spark plug: ₹150.50" in fractional_text
    assert "कुल ₹150.50" in fractional_text


def test_readback_uses_derived_total_and_marks_revision():
    store = SessionStore()
    session = store.create()
    card = make_test_card()
    session = store.set_card(session.id, expected_revision=0, card=card)
    assert session.revision == 1

    fake_timbre = FakeTimbreClient()
    workflow = Workflow(
        store=store,
        prisma=FakePrisma(),
        extractor=FakeExtractor(),
        timbre=fake_timbre,
    )

    readback = workflow.start_readback(session.id, expected_revision=1)
    assert isinstance(readback, Readback)
    assert readback.revision == 1
    assert readback.readback_revision == 1
    assert "कुल ₹650" in readback.text
    assert fake_timbre.calls == [readback.text]
    assert readback.manifest == {
        "codec": "g711",
        "sample_rate": 8000,
        "noise_source": "none",
        "target_snr_db": None,
        "measured_snr_db": float("inf"),
        "loss_percent": 0,
        "revision": 1,
    }
    assert isinstance(readback.audio_wav, bytes)
    assert len(readback.audio_wav) > 0

    # Store state has transitioned to awaiting_reply
    updated = store.get(session.id)
    assert updated.status == "awaiting_reply"
    assert updated.revision == 1
    assert updated.readback_revision == 1
    assert len(updated.logs) == 1
    assert updated.logs[0].role == "system"
    assert updated.logs[0].mode == "timbre_readback"
    assert updated.logs[0].text == readback.text


def test_readback_with_noise_and_codec():
    store = SessionStore()
    session = store.create()
    card = make_test_card()
    store.set_card(session.id, expected_revision=0, card=card)

    from parcha.audio import _ffmpeg
    speech_wav = _write_pcm(np.full(8000, 2000, dtype=np.int16))
    mulaw_speech = _ffmpeg(
        speech_wav,
        [],
        ["-acodec", "pcm_mulaw", "-ar", "8000", "-ac", "1", "-f", "mulaw"],
    )
    noise_wav = _write_pcm(np.tile(np.array([-1000, 1000], dtype=np.int16), 4000))

    class CustomTimbre:
        def synthesize(self, text: str) -> bytes:
            return mulaw_speech

    workflow = Workflow(
        store=store,
        prisma=FakePrisma(),
        extractor=FakeExtractor(),
        timbre=CustomTimbre(),
        codec="g711",
        target_snr_db=10.0,
        noise_wav=noise_wav,
    )

    readback = workflow.start_readback(session.id, expected_revision=1)
    assert readback.manifest["noise_source"] == "synthetic"
    assert readback.manifest["target_snr_db"] == 10.0
    assert abs(readback.manifest["measured_snr_db"] - 10.0) < 0.5


def test_review_needed_card_cannot_start_readback():
    store = SessionStore()
    session = store.create()
    fake_timbre = FakeTimbreClient()
    workflow = Workflow(
        store=store,
        prisma=FakePrisma(),
        extractor=FakeExtractor(),
        timbre=fake_timbre,
    )

    # Session without card
    with pytest.raises(Conflict, match="card needs review"):
        workflow.start_readback(session.id, expected_revision=0)

    # Session with card requiring review
    unreviewed_card = make_test_card().model_copy(update={"evidence": ()})
    store.set_card(session.id, expected_revision=0, card=unreviewed_card)
    with pytest.raises(Conflict, match="card needs review"):
        workflow.start_readback(session.id, expected_revision=1)

    # Missing timbre client raises ValueError
    reviewed_card = make_test_card()
    store.set_card(session.id, expected_revision=1, card=reviewed_card)
    workflow_no_timbre = Workflow(
        store=store,
        prisma=FakePrisma(),
        extractor=FakeExtractor(),
        timbre=None,
    )
    with pytest.raises(ValueError, match="Timbre client required for readback"):
        workflow_no_timbre.start_readback(session.id, expected_revision=2)


def test_readback_http_endpoints_and_audio_serving(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    app = create_app(fake_services)
    client = TestClient(app)

    session_id = client.post("/sessions").json()["id"]

    # Intake
    res = client.post(
        f"/sessions/{session_id}/intake",
        data={"expected_revision": 0},
        files={"audio": ("estimate.wav", b"fake speech", "audio/wav")},
    )
    assert res.status_code == 200
    assert res.json()["revision"] == 1

    # POST readback
    readback_res = client.post(
        f"/sessions/{session_id}/readback",
        data={"expected_revision": 1},
    )
    assert readback_res.status_code == 200
    data = readback_res.json()
    assert data["revision"] == 1
    assert data["readback_revision"] == 1
    assert data["audio_url"] == f"/sessions/{session_id}/readback.wav?revision=1"
    assert "front brake pad" in data["text"]
    assert "कुल ₹650" in data["text"]
    assert data["manifest"]["codec"] == "g711"

    # GET readback audio
    audio_res = client.get(data["audio_url"])
    assert audio_res.status_code == 200
    assert audio_res.headers["content-type"] == "audio/wav"
    assert len(audio_res.content) > 0

    # Unknown session 404
    unknown_post = client.post(
        "/sessions/unknown-session-xyz/readback",
        data={"expected_revision": 1},
    )
    assert unknown_post.status_code == 404
    assert unknown_post.json()["detail"] == "unknown session"

    unknown_get = client.get("/sessions/unknown-session-xyz/readback.wav?revision=1")
    assert unknown_get.status_code == 404
    assert unknown_get.json()["detail"] == "unknown session"

    # Path traversal attack attempt
    traversal_get = client.get("/sessions/..%2F..%2Fetc/readback.wav?revision=1")
    assert traversal_get.status_code in {400, 404}

    # Missing timbre in workflow returns 503
    services_no_timbre = AppServices(
        settings=fake_services.settings,
        store=fake_services.store,
        workflow=Workflow(
            store=fake_services.store,
            prisma=fake_services.workflow.prisma,
            extractor=fake_services.workflow.extractor,
            timbre=None,
        ),
        timbre=None,
    )
    client_no_timbre = TestClient(create_app(services_no_timbre))
    err_res = client_no_timbre.post(
        f"/sessions/{session_id}/readback",
        data={"expected_revision": 1},
    )
    assert err_res.status_code == 503
    assert "Timbre client required" in err_res.json()["detail"]


def test_stale_readback_wav_rejected(fake_services):
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

    # Calling GET readback.wav before readback started (status is 'review') -> 409
    res_not_started = client.get(f"/sessions/{session_id}/readback.wav?revision=1")
    assert res_not_started.status_code == 409

    # Start readback -> revision 1, status 'awaiting_reply'
    readback_res = client.post(
        f"/sessions/{session_id}/readback",
        data={"expected_revision": 1},
    )
    assert readback_res.status_code == 200

    # Requesting with mismatched revision -> 409
    res_wrong_rev = client.get(f"/sessions/{session_id}/readback.wav?revision=0")
    assert res_wrong_rev.status_code == 409

    res_future_rev = client.get(f"/sessions/{session_id}/readback.wav?revision=2")
    assert res_future_rev.status_code == 409

    # Requesting valid revision -> 200
    res_valid = client.get(f"/sessions/{session_id}/readback.wav?revision=1")
    assert res_valid.status_code == 200

    # Start readback again with stale expected_revision=0 -> 409
    res_stale_post = client.post(
        f"/sessions/{session_id}/readback",
        data={"expected_revision": 0},
    )
    assert res_stale_post.status_code == 409

    # Reask a field: updates card, bumps revision to 2, status to 'review'
    reask_res = client.post(
        f"/sessions/{session_id}/reask/items.part-1.amount_paise",
        data={"expected_revision": 1},
        files={"audio": ("correction.wav", b"speech", "audio/wav")},
    )
    assert reask_res.status_code == 200
    assert reask_res.json()["revision"] == 2
    assert reask_res.json()["status"] == "review"

    # Now GET readback.wav with revision 1 must be rejected with 409
    res_stale_after_reask = client.get(f"/sessions/{session_id}/readback.wav?revision=1")
    assert res_stale_after_reask.status_code == 409

    # Even with revision 2, it is rejected because readback was not started for revision 2
    res_rev2_not_started = client.get(f"/sessions/{session_id}/readback.wav?revision=2")
    assert res_rev2_not_started.status_code == 409
