"""Re-ask recovery benchmark: how often does one deliberate amount recording settle a gated amount?

Each case is a single spoken amount, the shape of a mechanic's re-ask. The decision under test is the
product's own `decide_amounts(..., expected_count=1)`, so a pass here is exactly what `_reask_amount` does.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from random import Random
from typing import Iterable, Mapping

from parcha.lab.money_eval import wilson_upper
from parcha.money import confusable_amount, decide_amounts
from parcha.numerals import render_colloquial_amount

SEED = 20261007
CONDITIONS = ("control", "g711|clean", "g711|0", "amr_nb_4750|clean", "amr_nb_4750|0")
VOICES = ("Roopesh", "Vikrant")
ESTIMATE_MANIFEST = Path("data/benchmarks/amount_v2/estimates.jsonl")


@dataclass(frozen=True)
class ReaskCase:
    case_id: str
    expected_paise: int
    utterance: str


def amount_pool(count: int = 100, manifest: Path = ESTIMATE_MANIFEST, *, seed: int = SEED,
                held_out: bool = False) -> list[int]:
    """The estimate benchmark's own amounts, topped up with a seeded spread of everyday rupee values.

    `held_out` drops the estimate amounts and every amount of the default pool, so it is a fresh sample.
    """
    pool: set[int] = set()
    if manifest.is_file() and not held_out:
        for line in manifest.read_text(encoding="utf-8").splitlines():
            pool.update(json.loads(line).get("expected_amounts_paise", []))
    pool = {p for p in pool if 0 < p <= 10_000_000 and p % 100 == 0}
    spread = [r * 100 for r in range(50, 5_001, 50)] + [r * 100 for r in range(5_500, 50_001, 500)]
    Random(seed).shuffle(spread)
    seen = set(amount_pool(100, manifest)) if held_out else set()
    for paise in spread:
        if len(pool) >= count:
            break
        if paise not in seen:
            pool.add(paise)
    return sorted(pool)


def build_cases(amounts: Iterable[int]) -> list[ReaskCase]:
    cases = []
    for index, paise in enumerate(sorted(amounts)):
        phrase = render_colloquial_amount(paise)
        cases.append(ReaskCase(f"r{index + 1:03d}", paise, phrase + (" रुपये" if index % 2 == 0 else "")))
    return cases


def score(case: ReaskCase, verbatim: str, transcribe: str) -> dict:
    decision = decide_amounts(verbatim, transcribe, expected_count=1)[0]
    if decision.reason is not None:
        outcome = "abstain"
    elif decision.paise == case.expected_paise:
        outcome = "recovered"
    else:
        outcome = "wrong_accepted"
    return {"paise": decision.paise, "reason": decision.reason, "outcome": outcome}


def summarize(rows: Iterable[Mapping]) -> dict[str, dict]:
    """Per-condition and overall counts with a Wilson upper bound on wrong accepts."""
    by_condition: dict[str, Counter] = {}
    reasons: dict[str, Counter] = {}
    for row in rows:
        for key in (row["condition"], "ALL"):
            by_condition.setdefault(key, Counter())[row["outcome"]] += 1
            if row["outcome"] == "abstain":
                reasons.setdefault(key, Counter())[row["reason"]] += 1
    summary = {}
    for key, counts in sorted(by_condition.items()):
        n = sum(counts.values())
        summary[key] = {
            "n": n,
            "recovered": counts["recovered"],
            "recovered_rate": counts["recovered"] / n,
            "wrong_accepted": counts["wrong_accepted"],
            "wrong_accepted_upper95": wilson_upper(counts["wrong_accepted"], n),
            "abstained": counts["abstain"],
            "abstain_reasons": dict(reasons.get(key, {})),
        }
    return summary


def rescore(rows: Iterable[Mapping]) -> list[dict]:
    """Re-run today's decision over saved transcripts (no API calls)."""
    out = []
    for row in rows:
        case = ReaskCase(row["case_id"], row["expected_paise"], row.get("utterance", ""))
        out.append({**row, **score(case, row["verbatim"], row["transcribe"])})
    return out


def paired_outcomes(rows: Iterable[Mapping]) -> dict[str, dict]:
    """Two-recordings rule: one voice is the earlier candidate, the other the re-ask (both directions).

    A pair settles only when both recordings are accepted by `decide_amounts`, agree, and carry no look-alike number
    word (those need a third recording, counted as `needs_third`). Wrong settles are the
    failures that matter: two independent recordings agreeing on the same wrong amount.
    """
    by_key: dict[tuple, dict] = {}
    for row in rows:
        by_key[(row["case_id"], row["condition"], row["voice"])] = row
    tally: dict[str, Counter] = {}
    for (case_id, condition, voice), first in by_key.items():
        for other_voice in VOICES:
            if other_voice == voice:
                continue
            second = by_key.get((case_id, condition, other_voice))
            if second is None:
                continue
            ok1, ok2 = first["paise"] is not None, second["paise"] is not None
            if ok1 and ok2 and first["paise"] == second["paise"]:
                if confusable_amount(first.get("verbatim", "")) or confusable_amount(second.get("verbatim", "")):
                    outcome = "needs_third"          # look-alike number words: the product asks for a third recording
                else:
                    outcome = "settled" if first["paise"] == first["expected_paise"] else "settled_wrong"
            else:
                outcome = "needs_another"
            for key in (condition, "ALL"):
                tally.setdefault(key, Counter())[outcome] += 1
    result = {}
    for key, counts in sorted(tally.items()):
        n = sum(counts.values())
        result[key] = {"pairs": n, "settled": counts["settled"], "settled_rate": counts["settled"] / n,
                       "settled_wrong": counts["settled_wrong"],
                       "settled_wrong_upper95": wilson_upper(counts["settled_wrong"], n),
                       "needs_another": counts["needs_another"], "needs_third": counts["needs_third"]}
    return result
