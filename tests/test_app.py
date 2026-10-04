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
