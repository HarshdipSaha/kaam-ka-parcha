"""Read-back echo benchmark per customer language: can Prisma recover every amount Timbre just read out?

Timbre speaks the product's own regional read-back (`make_readback(..., language=...)`, digit amounts, consent line
and closing prompt included) over the simulated phone line; Prisma transcribes it in the same language; an estimate
passes when every amount (and the total) appears in the transcript as a number. Numbers that are neither an expected
amount nor part of the spoken boilerplate (the Act year, the delivery date) are counted as phantom insertions.
Synthetic speech: this measures how well a voice survives the line, not how a person hears it.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
from random import Random
import re
from typing import Iterable, Mapping

from parcha.lab.money_eval import wilson_upper
from parcha.lab.reask_bench import amount_pool
from parcha.languages import LANGUAGES
from parcha.readback import make_readback
from parcha.schema import Delivery, Evidence, JobCard, LineItem

__all__ = ["CONDITIONS", "EchoCard", "build_cards", "readback_text", "score", "summarize"]

CONDITIONS = ("control", "g711|clean", "amr_nb_4750|0")
LABELS = ("front brake pad", "clutch plate", "oil filter", "chain set", "labour", "service charge")
NUMBER = re.compile(r"\d[\d,]*")


@dataclass(frozen=True)
class EchoCard:
    case_id: str
    amounts: tuple[int, ...]       # paise
    card: JobCard

    @property
    def expected_numbers(self) -> set[int]:
        rupees = {paise // 100 for paise in self.amounts}
        return rupees | {sum(self.amounts) // 100}


def build_cards(count: int = 60, *, seed: int = 20261009) -> list[EchoCard]:
    rng = Random(seed)
    pool = amount_pool(max(count * 3, 100), seed=seed)
    cards = []
    for index in range(count):
        n = 2 + index % 2
        amounts = tuple(rng.sample(pool, n))
        labels = rng.sample(LABELS[:-2], n - 1) + [rng.choice(LABELS[-2:])]
        items = [LineItem(id=f"item-{i + 1}", label=label, kind="labour" if label in LABELS[-2:] else "part", amount_paise=paise)
                 for i, (label, paise) in enumerate(zip(labels, amounts))]
        evidence = [Evidence(field=f"items.{it.id}.label", quote=it.label, review_score=0.95) for it in items]
        delivery = Delivery(date=date(2026, 10, 1 + index % 27), window=("morning", "afternoon", "evening")[index % 3],
                            spoken="synthetic")
        cards.append(EchoCard(f"c{index + 1:03d}", amounts, JobCard(items=items, delivery=delivery, evidence=evidence)))
    return cards


def readback_text(card: EchoCard, language: str) -> str:
    return make_readback(card.card, include_consent=True, language=language)


def _numbers(transcript: str) -> list[int]:
    out = []
    for token in NUMBER.findall(transcript):
        digits = token.replace(",", "")
        if digits:
            out.append(int(digits))
    return out


def score(card: EchoCard, transcript: str) -> dict:
    found = _numbers(transcript)
    expected = card.expected_numbers
    missing = sorted(expected - set(found))
    d = card.card.delivery
    allowed = expected | {2023, d.date.day, d.date.month, d.date.year, 0, 1, 2, 3}   # consent year, date, list markers
    phantom = sorted({n for n in found if n not in allowed and n >= 10})
    return {"recovered": not missing, "missing": missing, "phantom": phantom}


def summarize(rows: Iterable[Mapping]) -> dict:
    """Pass rate (with a Wilson interval) per language x voice x condition, plus each language's voice ranking."""
    cells: dict[tuple, Counter] = {}
    for row in rows:
        for key in ((row["language"], row["voice"], row["condition"]), (row["language"], row["voice"], "ALL")):
            c = cells.setdefault(key, Counter())
            c["n"] += 1
            c["pass"] += int(row["recovered"])
            c["phantom"] += int(bool(row["phantom"]))
    table = {}
    for (language, voice, condition), c in sorted(cells.items()):
        table.setdefault(language, {}).setdefault(voice, {})[condition] = {
            "n": c["n"], "recovered": c["pass"], "rate": c["pass"] / c["n"],
            "wilson_lower95": 1 - wilson_upper(c["n"] - c["pass"], c["n"]), "phantom_rows": c["phantom"],
        }
    ranking = {}
    for language, voices in table.items():
        worst = {voice: min(cell["rate"] for cond, cell in conds.items() if cond != "ALL") for voice, conds in voices.items()}
        ranking[language] = sorted(worst.items(), key=lambda kv: (-kv[1], kv[0]))
    return {"cells": table, "ranking_by_worst_condition": ranking}
