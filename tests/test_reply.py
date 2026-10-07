from __future__ import annotations

from datetime import date, datetime, timezone
import io
import wave
import numpy as np
import pytest

from parcha.audio import _write_pcm
from parcha.schema import Delivery, Evidence, JobCard, LineItem
from parcha.session import Conflict, SessionStore
from parcha.workflow import ReplyResult, Workflow, classify_reply
from tests.conftest import FakeExtractor, FakeTimbreClient, make_test_card


class MockPrisma:
    def __init__(self, transcript: str):
        self.transcript = transcript
        self.calls: list[tuple[bytes, str]] = []

    def transcribe(
        self,
        wav: bytes,
        *,
        mode: str,
        bias: list[str] | None = None,
        score: float = 1.0,
    ) -> str:
        self.calls.append((wav, mode))
        return self.transcript


def test_clear_acceptance():
    accept_phrases = [
        "haan",
        "han",
        "haan theek hai",
        "haan, theek hai",
        "han theek hai",
        "haan theek hai ji",
        "haan ji theek hai",
        "haan bilkul theek hai",
        "theek hai haan",
        "theek hai, haan",
        "theek hai haan ji",
        "haan manzoor hai",
        "manzoor hai",
        "haan ji manzoor hai",
        "manzoor hai ji",
        "haan sahi hai",
        "haan ji",
        "हाँ",
        "हां",
        "हाँ ठीक है",
        "हाँ, ठीक है",
        "हां ठीक है",
        "हाँ ठीक है जी",
        "हाँ जी ठीक है",
        "हाँ बिल्कुल ठीक है",
        "हाँ मंज़ूर है",
        "हाँ मंजूर है",
        "मंज़ूर है",
        "मंजूर है",
        "हाँ जी मंज़ूर है",
        "हाँ जी मंजूर है",
        "हाँ सही है",
        "हाँ जी",
        "Haan",
        "HAAN THEEK HAI",
        "haan   theek   hai",
    ]
    for phrase in accept_phrases:
        assert classify_reply(phrase) == "accept", f"Expected accept for {phrase!r}"



def test_plain_whole_sentence_affirmations_accept():
    """A customer on a phone line says "theek hai" or "ok" and means yes (changed 2026-10-07; these used to be unclear)."""
    for phrase in [
        "theek hai", "Theek hai ji", "thik hai", "bilkul theek hai", "theek hai theek hai", "sab theek hai",
        "sahi hai", "sahi", "manzoor hai", "mujhe manzoor hai", "kabool hai", "qabool hai", "chalega", "chalta hai",
        "pakka", "pakka hai", "zaroor", "jarur", "kar do", "theek hai kar do", "done", "ok", "OK.", "okay", "ok hai",
        "bilkul", "yes", "yeah", "sure", "correct", "agreed", "confirmed", "haan ok", "ok haan", "haan pakka",
        "ठीक है", "ठीक है ठीक है", "सब ठीक है", "सही है", "कबूल है", "चलेगा", "पक्का", "ज़रूर", "ओके", "हाँ ओके",
        "बिल्कुल", "बिल्कुल ठीक है", "कर दो", "मुझे मंज़ूर है",
    ]:
        assert classify_reply(phrase) == "accept", f"Expected accept for {phrase!r}"


def test_hedged_or_loaded_replies_still_never_accept():
    """Widening the yes list must not let a conditional, a correction, a number or an item name seal the parcha."""
    for phrase in [
        "theek hai par 500 se zyada nahi", "theek hai lekin", "theek hai but", "theek hai brake pad", "theek hai 450",
        "theek nahi hai", "ok nahi", "nahi theek hai", "sahi nahi hai", "bilkul nahi", "haan nahi", "ok but kal",
        "achha", "hmm", "ji", "theek", "haan theek", "chalo", "pata nahi", "soch ke batata hoon", "kitna hua",
        "ठीक नहीं है", "ठीक है लेकिन", "ठीक है पर कल", "अच्छा", "जी", "नहीं ठीक है",
    ]:
        assert classify_reply(phrase) != "accept", f"Phrase {phrase!r} must never accept"


def test_uncertain_or_correction_never_accepts():
    non_accept_cases = [
        ("theek", "unclear"),
        ("nahi", "reject"),
        ("nahin", "reject"),
        ("नहीं", "reject"),
        ("ना", "reject"),
        ("nahi 500", "correction"),
        ("nahi kal", "correction"),
        ("nahi kal shaam", "correction"),
        ("नहीं कल सुबह", "correction"),
        ("somvaar", "unclear"),
        ("haan nahi", "correction"),
        ("haan brake pad", "unclear"),
        ("haan theek", "unclear"),
        ("", "unclear"),
        ("   ", "unclear"),
        ("123", "unclear"),
        ("kuch samajh nahi aaya", "correction"),
        ("bilkul nahi", "correction"),
    ]
    for phrase, expected in non_accept_cases:
        res = classify_reply(phrase)
        assert res != "accept", f"Phrase {phrase!r} must never accept"
        assert res == expected, f"Phrase {phrase!r}: expected {expected}, got {res}"


def test_date_only_negation_routes_to_delivery_correction():
    store = SessionStore()
    session = store.create()
    card = make_test_card()
    store.set_card(session.id, expected_revision=0, card=card)
    workflow = Workflow(
        store=store,
        prisma=MockPrisma("nahi kal subah"),
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
    assert res.outcome == "needs_readback"
    assert res.transcript == "nahi kal subah"
    assert res.session.revision == 2
    assert res.session.status == "review"
    assert res.session.readback_revision is None
    assert res.session.card is not None
    assert res.session.card.delivery is not None
    assert res.session.card.delivery.spoken == "Mangalvaar subah"
    assert len(res.session.logs) == 2  # readback + customer reply
    assert res.session.logs[-1].role == "customer"
    assert res.session.logs[-1].mode == "reply"
    assert res.session.logs[-1].text == "nahi kal subah"


def test_workflow_reply_accept_confirms_session():
    store = SessionStore()
    session = store.create()
    card = make_test_card()
    store.set_card(session.id, expected_revision=0, card=card)
    workflow = Workflow(
        store=store,
        prisma=MockPrisma("haan theek hai"),
        extractor=FakeExtractor(),
        timbre=FakeTimbreClient(),
        normalize_audio=lambda blob, mime, sample_rate=8000: b"RIFFpcm",
    )
    workflow.start_readback(session.id, expected_revision=1)

    t0 = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)
    res = workflow.reply(
        session.id,
        b"dummy_audio",
        "audio/webm",
        expected_revision=1,
        readback_revision=1,
        recorded_at_utc=t0,
    )
    assert isinstance(res, ReplyResult)
    assert res.outcome == "confirmed"
    assert res.transcript == "haan theek hai"
    assert res.session.status == "confirmed"
    assert res.session.confirmed_at_utc == t0
    assert res.session.revision == 1
    assert res.session.readback_revision == 1

    stored = store.get(session.id)
    assert stored.status == "confirmed"
    assert stored.confirmed_at_utc == t0
    assert stored.logs[-1].role == "customer"
    assert stored.logs[-1].mode == "reply"
    assert stored.logs[-1].text == "haan theek hai"


def test_workflow_reply_correction_updates_card_and_needs_readback():
    store = SessionStore()
    session = store.create()
    card = make_test_card()
    store.set_card(session.id, expected_revision=0, card=card)
    workflow = Workflow(
        store=store,
        prisma=MockPrisma("nahi front brake pad 500"),
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
    assert res.outcome == "needs_readback"
    assert res.transcript == "nahi front brake pad 500"
    assert res.session.revision == 2
    assert res.session.status == "review"
    assert res.session.readback_revision is None
    assert res.session.card is not None
    assert res.session.card.items[0].amount_paise == 50000
    assert res.session.logs[-1].role == "customer"
    assert res.session.logs[-1].mode == "reply"
    assert res.session.logs[-1].text == "nahi front brake pad 500"


def test_workflow_reply_ambiguous_amount_asks_which_item():
    store = SessionStore()
    session = store.create()
    card = make_test_card()  # Has 2 items: front brake pad & labour
    store.set_card(session.id, expected_revision=0, card=card)
    workflow = Workflow(
        store=store,
        prisma=MockPrisma("nahi 500"),
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
    assert res.outcome == "ask_field"
    assert res.message == "Which item would you like to correct?"
    assert res.transcript == "nahi 500"
    assert res.session.status == "awaiting_reply"
    assert res.session.revision == 1
    assert res.session.readback_revision == 1
    assert res.session.logs[-1].role == "customer"
    assert res.session.logs[-1].mode == "unresolved_correction"
    assert res.session.logs[-1].text == "nahi 500"


def test_workflow_reply_unclear_records_observation_and_retries():
    store = SessionStore()
    session = store.create()
    card = make_test_card()
    store.set_card(session.id, expected_revision=0, card=card)
    mock_prisma = MockPrisma("kya bola aapne")
    workflow = Workflow(
        store=store,
        prisma=mock_prisma,
        extractor=FakeExtractor(),
        timbre=FakeTimbreClient(),
        normalize_audio=lambda blob, mime, sample_rate=8000: b"RIFFpcm",
    )
    workflow.start_readback(session.id, expected_revision=1)

    # 1. Unclear reply
    res = workflow.reply(
        session.id,
        b"dummy_audio",
        "audio/webm",
        expected_revision=1,
        readback_revision=1,
    )
    assert isinstance(res, ReplyResult)
    assert res.outcome == "retry"
    assert res.message == "Could not recognize confirmation or correction"
    assert res.session.status == "awaiting_reply"
    assert res.session.revision == 1
    assert res.session.readback_revision == 1
    assert res.session.logs[-1].role == "customer"
    assert res.session.logs[-1].mode == "reply"
    assert res.session.logs[-1].text == "kya bola aapne"

    # 2. Reject reply ("nahi")
    mock_prisma.transcript = "nahi"
    res2 = workflow.reply(
        session.id,
        b"dummy_audio",
        "audio/webm",
        expected_revision=1,
        readback_revision=1,
    )
    assert isinstance(res2, ReplyResult)
    assert res2.outcome == "retry"
    assert res2.message == "Could not recognize confirmation or correction"
    assert res2.session.status == "awaiting_reply"
    assert res2.session.revision == 1
    assert res2.session.readback_revision == 1
    assert res2.session.logs[-1].role == "customer"
    assert res2.session.logs[-1].mode == "reply"
    assert res2.session.logs[-1].text == "nahi"


def test_stale_reply_rejected_with_conflict():
    store = SessionStore()
    session = store.create()
    card = make_test_card()
    store.set_card(session.id, expected_revision=0, card=card)
    workflow = Workflow(
        store=store,
        prisma=MockPrisma("haan"),
        extractor=FakeExtractor(),
        timbre=FakeTimbreClient(),
        normalize_audio=lambda blob, mime, sample_rate=8000: b"RIFFpcm",
    )

    # Not yet read back (status is "review")
    with pytest.raises(Conflict, match="not awaiting reply"):
        workflow.reply(
            session.id,
            b"dummy_audio",
            "audio/webm",
            expected_revision=1,
            readback_revision=1,
        )

    workflow.start_readback(session.id, expected_revision=1)

    # Stale expected_revision
    with pytest.raises(Conflict, match="stale revision"):
        workflow.reply(
            session.id,
            b"dummy_audio",
            "audio/webm",
            expected_revision=0,
            readback_revision=1,
        )

    # Stale readback_revision
    with pytest.raises(Conflict, match="stale revision"):
        workflow.reply(
            session.id,
            b"dummy_audio",
            "audio/webm",
            expected_revision=1,
            readback_revision=0,
        )

    # Confirm the session
    workflow.reply(
        session.id,
        b"dummy_audio",
        "audio/webm",
        expected_revision=1,
        readback_revision=1,
    )

    # Calling reply after confirmation
    with pytest.raises(Conflict, match="not awaiting reply"):
        workflow.reply(
            session.id,
            b"dummy_audio",
            "audio/webm",
            expected_revision=1,
            readback_revision=1,
        )


def test_workflow_reply_single_item_auto_resolves_amount():
    store = SessionStore()
    session = store.create()
    single_item_card = JobCard(
        items=[LineItem(id="part-1", label="brake pad", kind="part", amount_paise=45000)],
        delivery=Delivery(date=date(2026, 10, 5), window="evening", spoken="Somvaar shaam tak"),
        evidence=[
            Evidence(field="items.part-1.label", quote="brake pad", review_score=0.9),
            Evidence(field="items.part-1.amount_paise", quote="₹450", review_score=0.9),
            Evidence(field="delivery", quote="Somvaar shaam tak", review_score=0.9),
        ],
    )
    store.set_card(session.id, expected_revision=0, card=single_item_card)
    workflow = Workflow(
        store=store,
        prisma=MockPrisma("nahi 500"),  # Does not explicitly mention "brake pad"
        extractor=FakeExtractor(),
        timbre=FakeTimbreClient(),
        normalize_audio=lambda blob, mime, sample_rate=8000: b"RIFFpcm",
    )
    workflow.start_readback(session.id, expected_revision=1)

    # Since only 1 item exists on card, ambiguous amount auto-resolves to that item
    res = workflow.reply(
        session.id,
        b"dummy_audio",
        "audio/webm",
        expected_revision=1,
        readback_revision=1,
    )
    assert res.outcome == "needs_readback"
    assert res.session.revision == 2
    assert res.session.card.items[0].amount_paise == 50000


def test_workflow_reply_with_noise_and_codec():
    store = SessionStore()
    session = store.create()
    card = make_test_card()
    store.set_card(session.id, expected_revision=0, card=card)

    speech_wav = _write_pcm(np.full(8000, 2000, dtype=np.int16))
    noise_wav = _write_pcm(np.full(8000, 500, dtype=np.int16))

    mock_prisma = MockPrisma("haan")
    workflow = Workflow(
        store=store,
        prisma=mock_prisma,
        extractor=FakeExtractor(),
        timbre=FakeTimbreClient(),
        target_snr_db=15.0,
        noise_wav=noise_wav,
        codec="g711",
        normalize_audio=lambda blob, mime, sample_rate=8000: speech_wav,
    )
    workflow.start_readback(session.id, expected_revision=1)

    res = workflow.reply(
        session.id,
        b"raw_speech",
        "audio/webm",
        expected_revision=1,
        readback_revision=1,
    )
    assert res.outcome == "confirmed"
    assert len(mock_prisma.calls) == 1
    # Check that audio passed to prisma was degraded (not the raw speech wav)
    assert mock_prisma.calls[0][0] != speech_wav
    # Check that audio is valid wav
    with wave.open(io.BytesIO(mock_prisma.calls[0][0]), "rb") as w:
        assert w.getframerate() == 8000
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
