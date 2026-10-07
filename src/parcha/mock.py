"""Offline demo wiring (PARCHA_MOCK=1): the real app, workflow and state machine with scripted speech services.

For clicking through the flow without keys or credits. It proves nothing about recognition: the mechanic's recording is
ignored (any audio produces the same synthetic estimate) and the first recording after a read-back is always
"Haan, theek hai". Use the real services for any accuracy claim.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import numpy as np

from .schema import Delivery, Evidence, JobCard, LineItem

ESTIMATE_NORMALIZED = "front brake pad ₹450, labour ₹200, Somvaar shaam tak"
ESTIMATE_VERBATIM = "front brake pad saade chaar sau labour do sau Somvaar shaam tak"
CUSTOMER_YES = "Haan, theek hai"


class MockPrisma:
    last_confidence = 0.95

    def __init__(self) -> None:
        self.awaiting_reply = False

    def transcribe(self, wav: bytes, *, mode: str = "transcribe", **_: object) -> str:
        if self.awaiting_reply and mode == "transcribe":
            self.awaiting_reply = False
            return CUSTOMER_YES
        return ESTIMATE_NORMALIZED if mode == "transcribe" else ESTIMATE_VERBATIM

    def transcribe_detailed(self, wav: bytes, *, mode: str = "transcribe", **kwargs: object) -> tuple[str, float]:
        return self.transcribe(wav, mode=mode, **kwargs), self.last_confidence


class MockExtractor:
    def extract_card(self, transcript_1: str, transcript_2: str, when: datetime) -> JobCard:
        due = (when.astimezone(timezone.utc) + timedelta(days=2)).date() if when else date.today() + timedelta(days=2)
        return JobCard(
            items=[
                LineItem(id="part-1", label="front brake pad", kind="part", amount_paise=45000),
                LineItem(id="labour-1", label="labour", kind="labour", amount_paise=20000),
            ],
            delivery=Delivery(date=due, window="evening", spoken="Somvaar shaam tak"),
            evidence=[
                Evidence(field="items.part-1.label", quote="front brake pad", review_score=0.95),
                Evidence(field="items.part-1.amount_paise", quote="₹450", review_score=0.95),
                Evidence(field="items.labour-1.label", quote="labour", review_score=0.95),
                Evidence(field="items.labour-1.amount_paise", quote="₹200", review_score=0.95),
                Evidence(field="delivery", quote="Somvaar shaam tak", review_score=0.9),
            ],
        )

    def extract_field(self, field: str, transcript: str, old_card: JobCard, when: datetime | None = None) -> JobCard:
        return old_card


def _mulaw_encode(pcm: np.ndarray) -> bytes:
    """G.711 mu-law from float samples in [-1, 1]."""
    mu = 255.0
    companded = np.sign(pcm) * np.log1p(mu * np.abs(pcm)) / np.log1p(mu)
    return ((companded * 127.5 + 127.5).astype(np.uint8) ^ 0xFF).tobytes()


class MockTimbre:
    """Returns a short two-tone chime in place of speech (8 kHz mu-law) and arms the scripted customer reply."""

    def __init__(self, prisma: MockPrisma) -> None:
        self.prisma = prisma
        self.voice = "mock"

    def synthesize(self, text: str, *, language: str = "hi-IN", voice: str | None = None) -> bytes:
        if not text.strip():
            raise ValueError("TTS text is empty")
        self.prisma.awaiting_reply = True
        t = np.arange(8000 * 2) / 8000
        tone = 0.25 * np.sin(2 * np.pi * np.where(t < 1.0, 523.25, 659.25) * t)
        return _mulaw_encode(tone)
