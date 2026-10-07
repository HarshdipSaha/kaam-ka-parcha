"""Whole-estimate repeat benchmark: do two recordings of a multi-amount estimate settle every amount safely?

A case is an estimate of 2-4 priced items spoken the colloquial way. Two voices record it; one recording is the
intake and the other the repeat (both directions). Scoring replays the saved transcripts through the product's own
`Workflow.intake` and `Workflow.confirm_estimate`, so a pass here is exactly what the "say the whole estimate
again" button does. Synthetic (Timbre) speech: this measures application logic, not real-speech accuracy.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from random import Random
from typing import Iterable, Mapping

from parcha.lab.money_eval import wilson_upper
from parcha.lab.reask_bench import CONDITIONS, SEED, VOICES, amount_pool
from parcha.numerals import render_colloquial_amount
from parcha.schema import Evidence, JobCard, LineItem
from parcha.session import SessionStore
from parcha.workflow import Workflow

__all__ = ["CONDITIONS", "VOICES", "EstimateCase", "build_cases", "paired_estimates", "replay_pair", "summarize_pairs"]

PARTS = ("ब्रेक पैड", "क्लच प्लेट", "ऑयल फ़िल्टर", "बेयरिंग", "चेन सेट", "प्लग")
LABOURS = ("लेबर", "सर्विस चार्ज", "फिटिंग चार्ज")


@dataclass(frozen=True)
class EstimateCase:
    case_id: str
    items: tuple[tuple[str, str, int], ...]   # (label, kind, paise)
    utterance: str

    @property
    def expected(self) -> list[int]:
        return [paise for _, _, paise in self.items]


def build_cases(count: int = 100, *, seed: int = SEED, held_out: bool = False) -> list[EstimateCase]:
    """`count` estimates of 2, 3 and 4 items in rotation, amounts drawn from the re-ask benchmark's pool."""
    rng = Random(seed)
    pool = amount_pool(max(count * 4, 100), seed=seed, held_out=held_out)
    cases = []
    for index in range(count):
        n = 2 + index % 3
        amounts = rng.sample(pool, n)
        labels = rng.sample(PARTS, n - 1) + [rng.choice(LABOURS)]
        items = tuple((label, "labour" if label in LABOURS else "part", paise) for label, paise in zip(labels, amounts))
        parts = [f"{label} {render_colloquial_amount(paise)}" + (" रुपये" if (index + i) % 2 == 0 else "")
                 for i, (label, _, paise) in enumerate(items)]
        cases.append(EstimateCase(f"e{index + 1:03d}", items, ", ".join(parts)))
    return cases


class _Replay:
    """Prisma stand-in returning saved transcripts in call order (transcribe pass, then verbatim pass)."""

    def __init__(self, outputs: list[str]):
        self.outputs = outputs

    def transcribe(self, wav, *, mode, bias=None, score=1.0):
        return self.outputs.pop(0)


class _CardExtractor:
    """The extractor's job here is only labels; its amounts are ignored by the money path."""

    def __init__(self, card: JobCard):
        self.card = card

    def extract_card(self, normalized, verbatim, recorded_at_utc):
        return self.card


def _card(case: EstimateCase) -> JobCard:
    items = [LineItem(id=f"{kind}-{i + 1}", label=label, kind=kind, amount_paise=0)
             for i, (label, kind, _) in enumerate(case.items)]
    evidence = [Evidence(field=f"items.{it.id}.label", quote=it.label, review_score=0.95) for it in items]
    return JobCard(items=items, evidence=evidence)


def replay_pair(case: EstimateCase, first: Mapping, second: Mapping) -> dict:
    """Intake with `first`'s transcripts, whole-estimate repeat with `second`'s; returns what settled."""
    when = datetime(2026, 10, 7, tzinfo=timezone.utc)
    store = SessionStore()
    sid = store.create().id
    prisma = _Replay([first["transcribe"], first["verbatim"], second["transcribe"], second["verbatim"]])
    workflow = Workflow(store=store, prisma=prisma, extractor=_CardExtractor(_card(case)),
                        normalize_audio=lambda blob, mime: b"RIFFpcm")
    s1 = workflow.intake(sid, b"a", "audio/webm", expected_revision=0, recorded_at_utc=when)
    s2 = workflow.confirm_estimate(sid, b"b", "audio/webm", expected_revision=s1.revision, recorded_at_utc=when) \
        if any(it.amount_paise is None for it in s1.card.items) else s1
    settled = [it.amount_paise for it in s2.card.items]
    expected = case.expected
    right = sum(1 for got, want in zip(settled, expected) if got == want)
    wrong = sum(1 for got, want in zip(settled, expected) if got is not None and got != want)
    return {"items": len(expected), "settled_right": right, "settled_wrong": wrong,
            "all_settled": right == len(expected), "recordings": 2}


def paired_estimates(rows: Iterable[Mapping], cases: Mapping[str, EstimateCase]) -> list[dict]:
    by_key = {(r["case_id"], r["condition"], r["voice"]): r for r in rows}
    out = []
    for (case_id, condition, voice), first in sorted(by_key.items()):
        for other in VOICES:
            second = by_key.get((case_id, condition, other))
            if other == voice or second is None:
                continue
            out.append({"case_id": case_id, "condition": condition, "intake_voice": voice,
                        **replay_pair(cases[case_id], first, second)})
    return out


def summarize_pairs(pairs: Iterable[Mapping]) -> dict[str, dict]:
    tally: dict[str, Counter] = {}
    for p in pairs:
        for key in (p["condition"], "ALL"):
            c = tally.setdefault(key, Counter())
            c["estimates"] += 1
            c["items"] += p["items"]
            c["right"] += p["settled_right"]
            c["wrong"] += p["settled_wrong"]
            c["complete"] += int(p["all_settled"])
            c["recordings"] += p["recordings"]
    return {
        key: {"estimates": c["estimates"], "items": c["items"],
              "items_settled": c["right"], "items_settled_rate": c["right"] / c["items"],
              "items_wrong_settled": c["wrong"], "items_wrong_settled_upper95": wilson_upper(c["wrong"], c["items"]),
              "estimates_fully_settled": c["complete"], "estimates_fully_settled_rate": c["complete"] / c["estimates"],
              "recordings_per_estimate": c["recordings"] / c["estimates"]}
        for key, c in sorted(tally.items())
    }
