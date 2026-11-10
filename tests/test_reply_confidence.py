"""A customer's "yes" must not be trusted on a confidence Prisma never sent.

Prisma's documented responses carry `"confidence": null`, and the client used to substitute 1.0, so the 0.65
low-confidence gate never fired. Unknown confidence now needs a second, verbatim pass that also hears a yes.
"""
from __future__ import annotations

import threading

import httpx
import pytest

from parcha.gnani import PrismaClient
from parcha.session import SessionStore
from parcha.workflow import Workflow
from tests.conftest import FakeExtractor, FakeTimbreClient, make_test_card


def _client(payloads: list[dict]) -> PrismaClient:
    queue = list(payloads)
    return PrismaClient("k", http=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=queue.pop(0)))))


def test_missing_confidence_is_reported_as_unknown_not_certain():
    result = _client([{"success": True, "transcript": "हाँ ठीक है"}]).transcribe_detailed(b"x", mode="transcribe")
    assert result.text == "हाँ ठीक है" and result.confidence is None


def test_reported_confidence_is_kept():
    result = _client([{"success": True, "transcript": "haan", "confidence": 0.42}]).transcribe_detailed(b"x")
    assert result.confidence == pytest.approx(0.42)


def test_concurrent_calls_on_one_client_keep_their_own_confidence():
    def handler(request: httpx.Request) -> httpx.Response:
        conf = 0.9 if b"first" in request.content else 0.3
        return httpx.Response(200, json={"success": True, "transcript": "t", "confidence": conf})

    client = PrismaClient("k", http=httpx.Client(transport=httpx.MockTransport(handler)))
    results: dict[str, float | None] = {}
    threads = [
        threading.Thread(target=lambda tag=tag: results.__setitem__(tag, client.transcribe_detailed(tag.encode()).confidence))
        for tag in ("first", "second")
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results == {"first": 0.9, "second": 0.3}
    assert not hasattr(client, "last_confidence")


class PassPrisma:
    """Fake Prisma with no confidence report: answers per pass mode."""

    def __init__(self, transcribe_text: str, verbatim_text: str):
        self.texts = {"transcribe": transcribe_text, "verbatim": verbatim_text}
        self.modes: list[str] = []

    def transcribe(self, wav: bytes, *, mode: str, **_: object) -> str:
        self.modes.append(mode)
        return self.texts[mode]


def _awaiting_reply(prisma) -> tuple[Workflow, SessionStore, str, int, int]:
    store = SessionStore()
    session = store.create()
    store.set_card(session.id, expected_revision=0, card=make_test_card())
    workflow = Workflow(
        store=store, prisma=prisma, extractor=FakeExtractor(), timbre=FakeTimbreClient(),
        normalize_audio=lambda blob, mime, sample_rate=8000: b"RIFFpcm",
    )
    readback = workflow.start_readback(session.id, expected_revision=1)
    return workflow, store, session.id, readback.revision, readback.readback_revision


def test_unknown_confidence_yes_confirmed_only_when_the_verbatim_pass_agrees():
    prisma = PassPrisma("हाँ ठीक है", "हां ठीक है")
    workflow, _, sid, rev, rb = _awaiting_reply(prisma)
    result = workflow.reply(sid, b"audio", "audio/wav", expected_revision=rev, readback_revision=rb, degrade=False)
    assert result.outcome == "confirmed"
    assert prisma.modes == ["transcribe", "verbatim"]


def test_unknown_confidence_yes_is_retried_when_the_verbatim_pass_disagrees():
    prisma = PassPrisma("हाँ ठीक है", "हाँ लेकिन")
    workflow, store, sid, rev, rb = _awaiting_reply(prisma)
    result = workflow.reply(sid, b"audio", "audio/wav", expected_revision=rev, readback_revision=rb, degrade=False)
    assert result.outcome == "retry"
    assert store.get(sid).status == "awaiting_reply"
    assert store.get(sid).logs[-1].mode == "unconfirmed_accept"


def test_a_reported_high_confidence_yes_needs_no_second_pass():
    prisma = PassPrisma("haan theek hai", "unused")
    prisma.confidence = 0.97
    workflow, _, sid, rev, rb = _awaiting_reply(prisma)
    result = workflow.reply(sid, b"audio", "audio/wav", expected_revision=rev, readback_revision=rb, degrade=False)
    assert result.outcome == "confirmed" and prisma.modes == ["transcribe"]


def test_a_correction_with_unknown_confidence_makes_no_extra_call():
    prisma = PassPrisma("kya bola aapne", "unused")
    workflow, _, sid, rev, rb = _awaiting_reply(prisma)
    result = workflow.reply(sid, b"audio", "audio/wav", expected_revision=rev, readback_revision=rb, degrade=False)
    assert result.outcome == "retry" and prisma.modes == ["transcribe"]
