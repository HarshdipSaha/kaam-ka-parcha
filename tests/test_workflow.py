from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import io
import wave

import numpy as np
import pytest

from parcha.audio import AudioError, normalize_upload
from parcha.schema import Delivery, Evidence, JobCard, LineItem
from parcha.session import Conflict, SessionStore
from parcha.workflow import Workflow
from tests.fakes import INTAKE_T, INTAKE_V, ScriptedPrisma
from tests.test_schema import sample_card


def make_sine_wav(sample_rate: int = 16000, duration_s: float = 1.0) -> bytes:
    num_samples = int(sample_rate * duration_s)
    samples = (5000 * np.sin(2 * np.pi * 440 * np.arange(num_samples) / sample_rate)).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(samples.tobytes())
    return buf.getvalue()


class FakePrisma:
    def __init__(self):
        self.calls: list[tuple[bytes, str, list[str] | None, float]] = []

    def transcribe(self, wav: bytes, *, mode: str, bias: list[str] | None = None, score: float = 1.0) -> str:
        self.calls.append((wav, mode, bias, score))
        return (
            "front brake pad ₹450, labour ₹200, Somvaar shaam tak"
            if mode == "transcribe"
            else "front brake pad saade chaar sau labour do sau Somvaar shaam tak"
        )


class RaisingPrisma:
    def transcribe(self, *args, **kwargs) -> str:
        raise AssertionError("Prisma was unexpectedly called")


class FakeExtractor:
    def extract_card(self, normalized: str, verbatim: str, recorded_at_utc: datetime) -> JobCard:
        assert "₹450" in normalized and "brake pad" in verbatim
        return sample_card()

    def extract_field(self, field: str, transcript: str, old_card: JobCard, when: datetime | None = None) -> JobCard:
        if field == "items.part-1.amount_paise":
            new_items = []
            for item in old_card.items:
                if item.id == "part-1":
                    new_items.append(
                        LineItem(
                            id=item.id,
                            label=item.label,
                            kind=item.kind,
                            amount_paise=50000,
                        )
                    )
                else:
                    new_items.append(item)
            return JobCard(items=tuple(new_items), delivery=old_card.delivery, evidence=old_card.evidence)
        elif field == "items.part-1.label":
            new_items = []
            for item in old_card.items:
                if item.id == "part-1":
                    new_items.append(
                        LineItem(
                            id=item.id,
                            label="rear brake pad",
                            kind=item.kind,
                            amount_paise=item.amount_paise,
                        )
                    )
                else:
                    new_items.append(item)
            return JobCard(items=tuple(new_items), delivery=old_card.delivery, evidence=old_card.evidence)
        elif field == "delivery":
            new_delivery = Delivery(date=date(2026, 10, 6), window="morning", spoken="Mangalvaar subah")
            return JobCard(items=old_card.items, delivery=new_delivery, evidence=old_card.evidence)
        raise ValueError(f"Unexpected field: {field}")


def test_intake_uses_same_recording_for_two_prisma_passes():
    prisma, store = FakePrisma(), SessionStore()
    session = store.create()
    service = Workflow(
        store=store,
        prisma=prisma,
        extractor=FakeExtractor(),
        normalize_audio=lambda blob, mime: b"RIFFpcm",
    )
    result = service.intake(session.id, b"recorded", "audio/webm", expected_revision=0)

    # 1. Two Prisma calls: transcribe then verbatim
    assert [call[1] for call in prisma.calls] == ["transcribe", "verbatim"]
    # 2. Both calls use the exact same normalized audio bytes
    assert prisma.calls[0][0] == prisma.calls[1][0] == b"RIFFpcm"
    assert prisma.calls[1][2] is not None
    assert "brake" in prisma.calls[1][2]
    # 3. Spoken amounts need a separate recording before they can enter the card.
    assert result.card is not None
    assert [item.amount_paise for item in result.card.items] == [None, None]
    assert result.card.maybe_total_paise is None
    assert result.status == "review"
    assert {log.text for log in result.logs if log.mode.startswith("abstain:")} == {
        "independent_confirmation_required"
    }
    assert result.revision == 1
    assert result.status == "review"
    # 4. Logs recorded atomically
    assert len(result.logs) == 4
    assert result.logs[0].role == "mechanic"
    assert result.logs[0].mode == "transcribe"
    assert result.logs[0].text == "front brake pad ₹450, labour ₹200, Somvaar shaam tak"
    assert result.logs[1].role == "mechanic"
    assert result.logs[1].mode == "verbatim"
    assert result.logs[1].text == "front brake pad saade chaar sau labour do sau Somvaar shaam tak"
    assert result.logs[0].recorded_at_utc.tzinfo is not None

    # Bias configuration passed to second call when use_bias=True
    prisma_bias = FakePrisma()
    service_bias = Workflow(
        store=store,
        prisma=prisma_bias,
        extractor=FakeExtractor(),
        normalize_audio=lambda blob, mime: b"RIFFpcm",
        bias_words=("brake", "clutch", "Honda"),
        use_bias=True,
    )
    session_bias = store.create()
    service_bias.intake(session_bias.id, b"recorded", "audio/webm", expected_revision=0)
    assert prisma_bias.calls[1][2] == ["brake", "clutch", "Honda"]


def test_browser_mime_with_codecs_is_accepted():
    wav_1s = make_sine_wav(sample_rate=16000, duration_s=1.0)

    # Test various browser mime types with codecs parameters
    browser_mimes = [
        "audio/webm;codecs=opus",
        "audio/webm; codecs=opus",
        "audio/ogg;codecs=opus",
        "audio/mp4;codecs=mp4a.40.2",
        "audio/wav",
        "audio/x-wav",
    ]

    for mime in browser_mimes:
        out = normalize_upload(wav_1s, mime, sample_rate=16000)
        with wave.open(io.BytesIO(out), "rb") as w:
            assert w.getnchannels() == 1
            assert w.getsampwidth() == 2
            assert w.getframerate() == 16000
            frames = w.readframes(w.getnframes())
            duration = len(frames) / (2 * 16000)
            assert 0.9 <= duration <= 1.1

    # Also test sample_rate=8000
    out_8k = normalize_upload(wav_1s, "audio/webm;codecs=opus", sample_rate=8000)
    with wave.open(io.BytesIO(out_8k), "rb") as w:
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert w.getframerate() == 8000
        frames = w.readframes(w.getnframes())
        duration = len(frames) / (2 * 8000)
        assert 0.9 <= duration <= 1.1


def test_bad_or_oversized_upload_is_rejected_before_prisma():
    store = SessionStore()
    session = store.create()
    prisma = RaisingPrisma()
    service = Workflow(
        store=store,
        prisma=prisma,
        extractor=FakeExtractor(),
    )

    # 1. Empty blob rejected
    with pytest.raises(AudioError, match="recording must be non-empty and under 8MB"):
        service.intake(session.id, b"", "audio/webm", expected_revision=0)

    # 2. Oversized blob (> 8MB) rejected
    with pytest.raises(AudioError, match="recording must be non-empty and under 8MB"):
        service.intake(session.id, b"0" * (8 * 1024 * 1024 + 1), "audio/webm", expected_revision=0)

    # 3. Unsupported mime types rejected
    with pytest.raises(AudioError, match="unsupported audio mime type: video/mp4"):
        service.intake(session.id, b"some audio", "video/mp4", expected_revision=0)

    with pytest.raises(AudioError, match="unsupported audio mime type: text/plain"):
        service.intake(session.id, b"some audio", "text/plain; charset=utf-8", expected_revision=0)

    # 4. Audio too short (< 0.3s)
    short_wav = make_sine_wav(sample_rate=16000, duration_s=0.1)
    with pytest.raises(AudioError, match="outside bounds"):
        service.intake(session.id, short_wav, "audio/wav", expected_revision=0)

    # Session in store remains completely untouched
    stored = store.get(session.id)
    assert stored.revision == 0
    assert stored.card is None
    assert stored.logs == ()


def test_concurrent_intake_conflict_handling():
    store = SessionStore()
    session = store.create()
    service = Workflow(
        store=store,
        prisma=FakePrisma(),
        extractor=FakeExtractor(),
        normalize_audio=lambda blob, mime: b"RIFFpcm",
    )

    # First intake succeeds at revision 0
    s1 = service.intake(session.id, b"audio_1", "audio/webm", expected_revision=0)
    assert s1.revision == 1
    assert len(s1.logs) == 4

    # Second intake using stale expected_revision=0 fails with Conflict
    with pytest.raises(Conflict, match="stale revision"):
        service.intake(session.id, b"audio_2", "audio/webm", expected_revision=0)

    # Session in store preserves only the committed intake's card and logs
    stored = store.get(session.id)
    assert stored.revision == 1
    assert len(stored.logs) == 4

    # Thread-level concurrency: two simultaneous requests at expected_revision=0
    session_concurrent = store.create()
    results: list = []
    conflicts: list = []

    def run_worker():
        try:
            res = service.intake(session_concurrent.id, b"audio", "audio/webm", expected_revision=0)
            results.append(res)
        except Conflict as exc:
            conflicts.append(exc)

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(run_worker)
        f2 = executor.submit(run_worker)
        f1.result()
        f2.result()

    assert len(results) == 1
    assert len(conflicts) == 1
    final_session = store.get(session_concurrent.id)
    assert final_session.revision == 1
    assert len(final_session.logs) == 4


def test_reask_updates_single_field_and_increments_revision():
    store = SessionStore()
    session = store.create()
    service = Workflow(
        store=store,
        prisma=ScriptedPrisma([INTAKE_T, INTAKE_V, "₹450", "saade chaar sau", "Mangalvaar subah", "rear brake pad"]),
        extractor=FakeExtractor(),
        normalize_audio=lambda blob, mime: b"RIFFpcm",
    )

    # Initial intake sets revision 1 with sample_card
    s1 = service.intake(session.id, b"audio", "audio/webm", expected_revision=0)
    assert s1.revision == 1
    assert s1.card is not None
    assert s1.card.items[0].amount_paise is None
    assert s1.card.items[1].amount_paise is None

    # Re-ask items.part-1.amount_paise
    s2 = service.reask(
        session.id,
        "items.part-1.amount_paise",
        b"reask_audio",
        "audio/webm",
        expected_revision=1,
    )
    assert s2.revision == 2
    assert s2.card is not None
    assert s2.card.items[0].amount_paise == 45000
    assert s2.card.items[1].amount_paise is None
    assert s2.card.delivery == s1.card.delivery
    assert len(s2.logs) == 5
    assert s2.logs[-1].role == "mechanic"
    assert s2.logs[-1].mode == "reask:items.part-1.amount_paise"

    # Re-ask delivery
    s3 = service.reask(
        session.id,
        "delivery",
        b"reask_audio_delivery",
        "audio/webm",
        expected_revision=2,
    )
    assert s3.revision == 3
    assert s3.card is not None
    assert s3.card.delivery is not None
    assert s3.card.delivery.spoken == "Mangalvaar subah"
    assert s3.card.items[0].amount_paise == 45000
    assert len(s3.logs) == 6
    assert s3.logs[-1].role == "mechanic"
    assert s3.logs[-1].mode == "reask:delivery"

    # Re-ask items.part-1.label
    s4 = service.reask(
        session.id,
        "items.part-1.label",
        b"reask_audio_label",
        "audio/webm",
        expected_revision=3,
    )
    assert s4.revision == 4
    assert s4.card is not None
    assert s4.card.items[0].label == "rear brake pad"
    assert s4.card.items[0].amount_paise == 45000
    assert len(s4.logs) == 7
    assert s4.logs[-1].mode == "reask:items.part-1.label"


def test_reask_invalid_field_raises():
    store = SessionStore()
    session = store.create()
    service = Workflow(
        store=store,
        prisma=FakePrisma(),
        extractor=FakeExtractor(),
        normalize_audio=lambda blob, mime: b"RIFFpcm",
    )

    # Cannot re-ask on session without card
    with pytest.raises(ValueError, match="cannot re-ask field on session without card"):
        service.reask(session.id, "delivery", b"audio", "audio/webm", expected_revision=0)

    # Initialize card on session
    service.intake(session.id, b"audio", "audio/webm", expected_revision=0)

    # Invalid field patterns
    invalid_fields = [
        "total_paise",
        "delivery_window",
        "items.part-1.invalid",
        "items.part_1.amount_paise",
        "items.part-1",
        "items",
        "items.PART-1.label",
        "",
        "notes",
    ]
    for field in invalid_fields:
        with pytest.raises(ValueError, match="invalid re-ask field"):
            service.reask(session.id, field, b"audio", "audio/webm", expected_revision=1)

    # Item ID not on card
    with pytest.raises(ValueError, match="item part-99 not found on card"):
        service.reask(session.id, "items.part-99.amount_paise", b"audio", "audio/webm", expected_revision=1)

    # Stale revision raises Conflict
    with pytest.raises(Conflict, match="stale revision"):
        service.reask(session.id, "items.part-1.amount_paise", b"audio", "audio/webm", expected_revision=0)
