"""The printed digest must cover what the customer agreed to, and printed audio hashes must match the served files."""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from io import BytesIO

from fastapi.testclient import TestClient
from pypdf import PdfReader

from parcha.app import create_app
from parcha.artefact import audit_manifest, audit_manifest_sha256, render_pdf, verify_url

INTAKE_AUDIO = b"fake intake audio"
REPLY_AUDIO = b"fake reply audio"


def _confirmed(fake_services) -> tuple[TestClient, str]:
    fake_services.workflow.timbre = fake_services.timbre
    client = TestClient(create_app(fake_services))
    sid = client.post("/sessions").json()["id"]
    client.post(f"/sessions/{sid}/intake", data={"expected_revision": 0},
                files={"audio": ("estimate.wav", INTAKE_AUDIO, "audio/wav")})
    client.post(f"/sessions/{sid}/reask/items.part-1.amount_paise", data={"expected_revision": 1},
                files={"audio": ("part.wav", b"part", "audio/wav")})
    client.post(f"/sessions/{sid}/reask/items.labour-1.amount_paise", data={"expected_revision": 2},
                files={"audio": ("labour.wav", b"labour", "audio/wav")})
    client.post(f"/sessions/{sid}/readback", data={"expected_revision": 3})
    fake_services.workflow.prisma.transcribe = lambda wav, mode, **kw: "haan theek hai"
    res = client.post(f"/sessions/{sid}/reply", data={"expected_revision": 3, "readback_revision": 3},
                      files={"audio": ("reply.wav", REPLY_AUDIO, "audio/wav")})
    assert res.json()["outcome"] == "confirmed"
    return client, sid


def test_the_manifest_covers_every_amount_and_the_total(fake_services):
    _, sid = _confirmed(fake_services)
    session = fake_services.store.get(sid)
    card = audit_manifest(session)["card"]
    assert card["total_paise"] == session.card.total_paise
    assert [it["amount_paise"] for it in card["items"]] == [it.amount_paise for it in session.card.items]
    assert card["delivery"]["spoken"] == session.card.delivery.spoken


def test_changing_one_amount_changes_the_digest(fake_services):
    _, sid = _confirmed(fake_services)
    session = fake_services.store.get(sid)
    first = session.card.items[0]
    tampered_card = session.card.model_copy(update={"items": (first.model_copy(update={"amount_paise": first.amount_paise + 100}),) + tuple(session.card.items[1:])})
    assert audit_manifest_sha256(replace(session, card=tampered_card)) != audit_manifest_sha256(session)


def test_the_pdf_attachment_carries_the_card(fake_services):
    client, sid = _confirmed(fake_services)
    reader = PdfReader(BytesIO(client.get(f"/sessions/{sid}/pdf").content))
    evidence = json.loads(reader.attachments["transcripts.json"][0])
    assert evidence["card"]["total_paise"] == fake_services.store.get(sid).card.total_paise
    assert evidence["schema"] == "parcha-manifest/1"


def test_printed_audio_hashes_match_the_files_served_for_checking(fake_services):
    client, sid = _confirmed(fake_services)
    page = PdfReader(BytesIO(client.get(f"/sessions/{sid}/pdf").content)).pages[0].extract_text()
    intake_file = client.get(f"/sessions/{sid}/intake.wav").content
    reply_file = client.get(f"/sessions/{sid}/reply.wav").content
    assert hashlib.sha256(intake_file).hexdigest() in page
    assert hashlib.sha256(reply_file).hexdigest() in page
    verify = client.get(f"/verify/{sid}").text
    assert hashlib.sha256(reply_file).hexdigest() in verify


def test_the_qr_code_points_at_a_full_address(fake_services):
    client, sid = _confirmed(fake_services)
    session = fake_services.store.get(sid)
    assert verify_url(session, "https://test.example/") == f"https://test.example/verify/{sid}"
    page = PdfReader(BytesIO(client.get(f"/sessions/{sid}/pdf").content)).pages[0].extract_text()
    assert "Scan to Verify" in page


def test_no_qr_code_without_a_public_address(fake_services):
    _, sid = _confirmed(fake_services)
    pdf = render_pdf(fake_services.store.get(sid), base_url="")
    assert "Scan to Verify" not in PdfReader(BytesIO(pdf)).pages[0].extract_text()
