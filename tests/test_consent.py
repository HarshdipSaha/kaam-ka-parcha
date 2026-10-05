import hashlib
import json
from datetime import datetime, timezone
from io import BytesIO
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from parcha.app import AppServices, create_app
from parcha.artefact import audit_manifest, audit_manifest_sha256, render_pdf
from parcha.readback import STATUTORY_CONSENT_NOTICE, make_readback
from parcha.schema import JobCard, LineItem, TranscriptLog
from parcha.session import Conflict, Session, SessionStore
from parcha.workflow import Workflow
from tests.conftest import FakeExtractor, FakePrisma, FakeTimbreClient, make_test_card


def test_session_store_record_dpdp_consent():
    store = SessionStore()
    session = store.create()
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15"

    updated = store.record_dpdp_consent(
        session.id,
        expected_revision=0,
        when=now,
        user_agent=user_agent,
        granted=True,
    )

    assert updated.dpdp_consent_granted is True
    assert updated.dpdp_consent_at_utc == now
    assert updated.dpdp_user_agent == user_agent
    expected_raw = f"DPDP_2023:{session.id}:{now.isoformat()}:{user_agent}:True"
    expected_hash = hashlib.sha256(expected_raw.encode("utf-8")).hexdigest()
    assert updated.dpdp_consent_sha256 == expected_hash

    # Check transcript log was recorded
    assert len(updated.logs) == 1
    log = updated.logs[0]
    assert log.role == "customer"
    assert log.mode == "dpdp_consent"
    assert "DPDP Act 2023" in log.text
    assert "granted" in log.text


def test_session_store_dpdp_consent_conflict_on_stale_or_confirmed():
    store = SessionStore()
    session = store.create()
    card = make_test_card()
    store.set_card(session.id, expected_revision=0, card=card)
    store.start_readback(session.id, expected_revision=1)
    now = datetime.now(timezone.utc)

    # Stale revision conflict
    with pytest.raises(Conflict, match="stale revision"):
        store.record_dpdp_consent(session.id, expected_revision=0, when=now)

    # Confirm session
    store.confirm(session.id, expected_revision=1, when=now)

    # Once confirmed, cannot mutate
    with pytest.raises(Conflict, match="confirmed session is immutable"):
        store.record_dpdp_consent(session.id, expected_revision=1, when=now)


def test_telephony_readback_includes_statutory_consent_notice():
    card = make_test_card()
    text = make_readback(card, include_consent=True)
    assert STATUTORY_CONSENT_NOTICE in text
    assert text.startswith(STATUTORY_CONSENT_NOTICE)
    assert "कुल ₹650" in text
    assert "Haan, theek hai" in text


def test_workflow_start_readback_includes_dpdp_consent_by_default():
    store = SessionStore()
    session = store.create()
    card = make_test_card()
    store.set_card(session.id, expected_revision=0, card=card)

    fake_timbre = FakeTimbreClient()
    workflow = Workflow(
        store=store,
        prisma=FakePrisma(),
        extractor=FakeExtractor(),
        timbre=fake_timbre,
    )

    readback = workflow.start_readback(session.id, expected_revision=1)
    assert STATUTORY_CONSENT_NOTICE in readback.text
    assert STATUTORY_CONSENT_NOTICE in fake_timbre.calls[0]


def test_consent_api_endpoint():
    store = SessionStore()
    session = store.create()
    card = make_test_card()
    store.set_card(session.id, expected_revision=0, card=card)

    services = AppServices(
        settings=None,
        store=store,
        workflow=None,
        timbre=None,
    )
    client = TestClient(create_app(services))

    headers = {"User-Agent": "ParchaCustomerApp/1.0"}
    res = client.post(
        f"/sessions/{session.id}/consent",
        data={"expected_revision": "1", "granted": "true"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["dpdp_consent_granted"] is True
    assert data["dpdp_consent_sha256"] is not None
    assert len(data["dpdp_consent_sha256"]) == 64

    # Verify session in store
    saved = store.get(session.id)
    assert saved.dpdp_consent_granted is True
    assert saved.dpdp_user_agent == "ParchaCustomerApp/1.0"


def test_dpdp_consent_embedded_in_transcripts_and_verify_endpoint():
    store = SessionStore()
    session = store.create()
    card = make_test_card()
    store.set_card(session.id, expected_revision=0, card=card)
    store.start_readback(session.id, expected_revision=1)
    now = datetime(2026, 10, 5, 14, 0, 0, tzinfo=timezone.utc)
    store.record_dpdp_consent(
        session.id,
        expected_revision=1,
        when=now,
        user_agent="AutomotiveBrowser/2.0",
        granted=True,
    )
    store.confirm(session.id, expected_revision=1, when=now)

    confirmed_session = store.get(session.id)
    manifest = audit_manifest(confirmed_session)
    assert "dpdp_consent" in manifest
    assert manifest["dpdp_consent"]["granted"] is True
    assert manifest["dpdp_consent"]["user_agent"] == "AutomotiveBrowser/2.0"
    assert manifest["dpdp_consent"]["consent_sha256"] == confirmed_session.dpdp_consent_sha256

    pdf_bytes = render_pdf(confirmed_session)
    reader = PdfReader(BytesIO(pdf_bytes))
    attach_data = reader.attachments["transcripts.json"][0]
    raw_json = attach_data if isinstance(attach_data, bytes) else attach_data.get_data()
    parsed_manifest = json.loads(raw_json.decode("utf-8"))
    assert parsed_manifest["dpdp_consent"]["granted"] is True
    assert parsed_manifest["dpdp_consent"]["consent_sha256"] == confirmed_session.dpdp_consent_sha256

    page_text = reader.pages[0].extract_text()
    assert "DPDP Act 2023" in page_text

    # Test /verify/{session_id} JSON
    services = AppServices(
        settings=None,
        store=store,
        workflow=None,
        timbre=None,
    )
    client = TestClient(create_app(services))
    res = client.get(f"/verify/{session.id}?format=json")
    assert res.status_code == 200
    vdata = res.json()
    assert "dpdp_consent" in vdata
    assert vdata["dpdp_consent"]["granted"] is True
    assert vdata["dpdp_consent"]["consent_sha256"] == confirmed_session.dpdp_consent_sha256

    # Test /verify/{session_id} HTML
    html_res = client.get(f"/verify/{session.id}")
    assert html_res.status_code == 200
    assert "DPDP Act 2023" in html_res.text
