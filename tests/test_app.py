from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from parcha.app import AppServices, create_app
from parcha.config import Settings
from parcha.session import SessionStore


def test_create_session_and_reject_empty_intake(fake_services):
    client = TestClient(create_app(fake_services))
    res = client.post("/sessions")
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert data["revision"] == 0
    assert data["status"] == "draft"
    assert data["card"] is None
    session_id = data["id"]

    intake_res = client.post(
        f"/sessions/{session_id}/intake",
        data={"expected_revision": 0},
        files={"audio": ("empty.wav", b"", "audio/wav")},
    )
    assert intake_res.status_code == 422
    assert "empty recording" in intake_res.json()["detail"]


def test_workshop_page_has_record_and_review_controls(fake_services):
    client = TestClient(create_app(fake_services))
    res = client.get("/workshop")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    html = res.text
    assert '<meta name="viewport"' in html
    assert "Kaam ka Parcha — Workshop Estimate" in html
    assert "Synthetic demo data" in html
    assert 'id="record"' in html
    assert 'id="stop"' in html
    assert 'id="message"' in html
    assert 'id="transcript"' in html
    assert 'id="card"' in html
    assert 'id="start-readback"' in html
    assert 'id="customer-link"' in html
    assert "app.js" in html


def test_get_unknown_session_returns_404(fake_services):
    client = TestClient(create_app(fake_services))
    res = client.get("/sessions/unknown-id-12345")
    assert res.status_code == 404
    assert res.json()["detail"] == "unknown session"

    res_intake = client.post(
        "/sessions/unknown-id-12345/intake",
        data={"expected_revision": 0},
        files={"audio": ("audio.wav", b"fake audio content", "audio/wav")},
    )
    assert res_intake.status_code == 404
    assert res_intake.json()["detail"] == "unknown session"

    res_reask = client.post(
        "/sessions/unknown-id-12345/reask/delivery",
        data={"expected_revision": 0},
        files={"audio": ("audio.wav", b"fake audio content", "audio/wav")},
    )
    assert res_reask.status_code == 404
    assert res_reask.json()["detail"] == "unknown session"


def test_intake_success_returns_card_and_total(fake_services):
    client = TestClient(create_app(fake_services))
    session = client.post("/sessions").json()
    session_id = session["id"]

    intake_res = client.post(
        f"/sessions/{session_id}/intake",
        data={"expected_revision": 0},
        files={"audio": ("audio.wav", b"recorded speech bytes", "audio/wav")},
    )
    assert intake_res.status_code == 200
    data = intake_res.json()
    assert data["id"] == session_id
    assert data["revision"] == 1
    assert data["status"] == "review"
    assert data["card"] is not None
    assert len(data["card"]["items"]) == 2
    assert data["total_paise"] == 65000
    assert isinstance(data["review_fields"], list)

    get_res = client.get(f"/sessions/{session_id}")
    assert get_res.status_code == 200
    assert get_res.json() == data


def test_reask_endpoint_updates_field(fake_services):
    client = TestClient(create_app(fake_services))
    session_id = client.post("/sessions").json()["id"]

    # Initial intake
    intake_res = client.post(
        f"/sessions/{session_id}/intake",
        data={"expected_revision": 0},
        files={"audio": ("audio.wav", b"recorded speech bytes", "audio/wav")},
    )
    assert intake_res.status_code == 200
    assert intake_res.json()["revision"] == 1

    # Reask items.part-1.amount_paise
    reask_res = client.post(
        f"/sessions/{session_id}/reask/items.part-1.amount_paise",
        data={"expected_revision": 1},
        files={"audio": ("correction.wav", b"panch sau rupaye", "audio/wav")},
    )
    assert reask_res.status_code == 200
    data = reask_res.json()
    assert data["revision"] == 2
    part_1 = next(it for it in data["card"]["items"] if it["id"] == "part-1")
    assert part_1["amount_paise"] == 50000
    assert data["total_paise"] == 70000

    # Conflict on stale revision
    stale_res = client.post(
        f"/sessions/{session_id}/reask/items.part-1.amount_paise",
        data={"expected_revision": 1},
        files={"audio": ("correction.wav", b"audio", "audio/wav")},
    )
    assert stale_res.status_code == 409


def test_missing_credentials_returns_503(fake_services):
    # Missing API_KEY
    services_no_gnani = AppServices(
        settings=Settings(api_key=""),
        store=SessionStore(),
        workflow=fake_services.workflow,
    )
    client_no_gnani = TestClient(create_app(services_no_gnani))
    s1_id = client_no_gnani.post("/sessions").json()["id"]
    res1 = client_no_gnani.post(
        f"/sessions/{s1_id}/intake",
        data={"expected_revision": 0},
        files={"audio": ("audio.wav", b"audio data", "audio/wav")},
    )
    assert res1.status_code == 503
    assert "API_KEY is required" in res1.json()["detail"]

    # Missing Extractor settings
    services_no_ext = AppServices(
        settings=Settings(api_key="some-key", extractor_base_url=""),
        store=SessionStore(),
        workflow=fake_services.workflow,
    )
    client_no_ext = TestClient(create_app(services_no_ext))
    s2_id = client_no_ext.post("/sessions").json()["id"]
    res2 = client_no_ext.post(
        f"/sessions/{s2_id}/intake",
        data={"expected_revision": 0},
        files={"audio": ("audio.wav", b"audio data", "audio/wav")},
    )
    assert res2.status_code == 503
    assert "extractor endpoint and model are required" in res2.json()["detail"]


def test_customer_page_renders_card_and_disclosure(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    client = TestClient(create_app(fake_services))
    session = client.post("/sessions").json()
    session_id = session["id"]

    # Intake to establish card
    client.post(
        f"/sessions/{session_id}/intake",
        data={"expected_revision": 0},
        files={"audio": ("estimate.wav", b"audio data", "audio/wav")},
    )

    # Start readback so readback_revision is set
    rb_res = client.post(
        f"/sessions/{session_id}/readback",
        data={"expected_revision": 1},
    )
    assert rb_res.status_code == 200

    res = client.get(f"/customer/{session_id}")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    html = res.text

    assert '<meta name="viewport"' in html
    assert "Kaam ka Parcha — Customer Estimate Review" in html
    assert 'id="disclosure"' in html
    assert "Simulated phone line: audio passed through G.711 + recorded engine ambience at 5 dB. No call was placed. All names and amounts are synthetic." in html
    assert 'id="readback-player"' in html
    assert f"/sessions/{session_id}/readback.wav?revision=1" in html
    assert 'id="customer-record"' in html
    assert 'id="customer-stop"' in html
    assert 'id="customer-status"' in html
    assert 'id="customer-message"' in html
    assert 'id="confirmed-banner"' in html
    assert "front brake pad" in html
    assert "labour" in html
    assert "app.js" in html


def test_customer_page_rejects_unknown_session_with_404(fake_services):
    client = TestClient(create_app(fake_services))
    res = client.get("/customer/non-existent-session-id")
    assert res.status_code == 404
    assert res.json()["detail"] == "unknown session"


def test_customer_reply_endpoint_confirms_session(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    client = TestClient(create_app(fake_services))
    session = client.post("/sessions").json()
    session_id = session["id"]

    # Intake
    client.post(
        f"/sessions/{session_id}/intake",
        data={"expected_revision": 0},
        files={"audio": ("estimate.wav", b"audio data", "audio/wav")},
    )

    # Readback
    rb_res = client.post(
        f"/sessions/{session_id}/readback",
        data={"expected_revision": 1},
    )
    assert rb_res.status_code == 200

    # Mock prisma to return accept phrase "हाँ ठीक है"
    fake_services.workflow.prisma.transcribe = lambda wav, mode, **kw: "हाँ ठीक है"

    # Post reply
    reply_res = client.post(
        f"/sessions/{session_id}/reply",
        data={"expected_revision": 1, "readback_revision": 1},
        files={"audio": ("reply.wav", b"haan bytes", "audio/wav")},
    )
    assert reply_res.status_code == 200
    data = reply_res.json()
    assert data["outcome"] == "confirmed"
    assert data["status"] == "confirmed"
    assert data["revision"] == 1
    assert data["id"] == session_id
    assert data["card"] is not None
    assert data["total_paise"] == 65000
    assert data["review_fields"] == []

    # Verify session GET also confirmed
    get_res = client.get(f"/sessions/{session_id}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "confirmed"

    # Verify customer page now reflects confirmed
    cust_res = client.get(f"/customer/{session_id}")
    assert cust_res.status_code == 200
    assert "Confirmed" in cust_res.text


def test_customer_reply_endpoint_handles_correction_and_conflict(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    client = TestClient(create_app(fake_services))
    session = client.post("/sessions").json()
    session_id = session["id"]

    # 1. Conflict: session not in awaiting_reply (draft status)
    res_not_ready = client.post(
        f"/sessions/{session_id}/reply",
        data={"expected_revision": 0, "readback_revision": 0},
        files={"audio": ("reply.wav", b"dummy audio", "audio/wav")},
    )
    assert res_not_ready.status_code == 409
    assert "session not awaiting reply" in res_not_ready.json()["detail"]

    # Intake to reach revision 1
    client.post(
        f"/sessions/{session_id}/intake",
        data={"expected_revision": 0},
        files={"audio": ("estimate.wav", b"audio data", "audio/wav")},
    )

    # Readback to reach awaiting_reply
    client.post(
        f"/sessions/{session_id}/readback",
        data={"expected_revision": 1},
    )

    # 2. 404 on unknown session
    res_404 = client.post(
        "/sessions/non-existent-session-id/reply",
        data={"expected_revision": 1, "readback_revision": 1},
        files={"audio": ("reply.wav", b"dummy audio", "audio/wav")},
    )
    assert res_404.status_code == 404
    assert res_404.json()["detail"] == "unknown session"

    # 3. 422 on empty recording
    res_empty = client.post(
        f"/sessions/{session_id}/reply",
        data={"expected_revision": 1, "readback_revision": 1},
        files={"audio": ("empty.wav", b"", "audio/wav")},
    )
    assert res_empty.status_code == 422
    assert "empty recording" in res_empty.json()["detail"]

    # 4. 409 on stale expected_revision or readback_revision
    res_stale = client.post(
        f"/sessions/{session_id}/reply",
        data={"expected_revision": 0, "readback_revision": 1},
        files={"audio": ("reply.wav", b"dummy audio", "audio/wav")},
    )
    assert res_stale.status_code == 409
    assert "stale revision" in res_stale.json()["detail"]

    res_stale_rb = client.post(
        f"/sessions/{session_id}/reply",
        data={"expected_revision": 1, "readback_revision": 999},
        files={"audio": ("reply.wav", b"dummy audio", "audio/wav")},
    )
    assert res_stale_rb.status_code == 409
    assert "stale revision" in res_stale_rb.json()["detail"]

    # 5. Correction handling: outcome == "needs_readback"
    fake_services.workflow.prisma.transcribe = lambda wav, mode, **kw: "nahi front brake pad 500"
    res_corr = client.post(
        f"/sessions/{session_id}/reply",
        data={"expected_revision": 1, "readback_revision": 1},
        files={"audio": ("correction.wav", b"correction audio", "audio/wav")},
    )
    assert res_corr.status_code == 200
    corr_data = res_corr.json()
    assert corr_data["outcome"] == "needs_readback"
    assert corr_data["revision"] == 2
    part_1 = next(it for it in corr_data["card"]["items"] if it["id"] == "part-1")
    assert part_1["amount_paise"] == 50000
    assert corr_data["total_paise"] == 70000

    # 6. Retry outcome when unclear
    client.post(
        f"/sessions/{session_id}/readback",
        data={"expected_revision": 2},
    )
    fake_services.workflow.prisma.transcribe = lambda wav, mode, **kw: "kya bola"
    res_retry = client.post(
        f"/sessions/{session_id}/reply",
        data={"expected_revision": 2, "readback_revision": 2},
        files={"audio": ("unclear.wav", b"unclear speech", "audio/wav")},
    )
    assert res_retry.status_code == 200
    assert res_retry.json()["outcome"] == "retry"


def test_api_key_not_leaked_in_any_response(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    api_key = fake_services.settings.api_key
    extractor_key = fake_services.settings.extractor_api_key
    assert api_key and extractor_key

    client = TestClient(create_app(fake_services))

    def assert_no_leak(res):
        text = res.text
        assert api_key not in text, f"API key leaked in body of {res.request.url}"
        assert extractor_key not in text, f"Extractor key leaked in body of {res.request.url}"
        for h_name, h_val in res.headers.items():
            assert api_key not in h_val, f"API key leaked in header {h_name}"
            assert extractor_key not in h_val, f"Extractor key leaked in header {h_name}"

    # Workshop page
    r = client.get("/workshop")
    assert_no_leak(r)

    # Create session
    r = client.post("/sessions")
    assert_no_leak(r)
    s_id = r.json()["id"]

    # Session details
    r = client.get(f"/sessions/{s_id}")
    assert_no_leak(r)

    # Intake
    r = client.post(
        f"/sessions/{s_id}/intake",
        data={"expected_revision": 0},
        files={"audio": ("test.wav", b"dummy audio", "audio/wav")},
    )
    assert_no_leak(r)

    # Readback
    r = client.post(
        f"/sessions/{s_id}/readback",
        data={"expected_revision": 1},
    )
    assert_no_leak(r)

    # Readback wav
    r = client.get(f"/sessions/{s_id}/readback.wav?revision=1")
    assert_no_leak(r)

    # Customer page
    r = client.get(f"/customer/{s_id}")
    assert_no_leak(r)

    # Customer reply
    fake_services.workflow.prisma.transcribe = lambda wav, mode, **kw: "हाँ"
    r = client.post(
        f"/sessions/{s_id}/reply",
        data={"expected_revision": 1, "readback_revision": 1},
        files={"audio": ("reply.wav", b"dummy audio", "audio/wav")},
    )
    assert_no_leak(r)

    # Customer page after confirmation
    r = client.get(f"/customer/{s_id}")
    assert_no_leak(r)
