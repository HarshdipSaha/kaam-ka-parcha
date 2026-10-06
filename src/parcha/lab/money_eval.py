"""Evaluate whether the benchmark's two transcription passes accept item amounts."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Literal

from parcha.lab.dataset import Clip, load_manifest
from parcha.lab.metrics import canonical_reference
from parcha.money import decide_amounts
from parcha.numerals import parse_amounts


OutcomeKind = Literal["correct", "wrong_accepted", "abstained"]


@dataclass(frozen=True)
class AmountOutcome:
    clip_id: str
    condition: str
    slice: str
    expected_paise: int
    decided_paise: int | None
    reason: str | None

    @property
    def kind(self) -> OutcomeKind:
        if self.reason is not None:
            return "abstained"
        return "correct" if self.decided_paise == self.expected_paise else "wrong_accepted"


def _condition(row: dict) -> str:
    codec = row.get("codec")
    snr = row.get("snr")
    if snr is None:
        snr_label = "clean"
    else:
        snr_value = float(snr)
        snr_label = str(int(snr_value)) if snr_value.is_integer() else repr(snr_value)

    parts = [str(codec), snr_label]
    loss = float(row.get("loss") or 0.0)
    if loss != 0.0:
        loss_label = str(int(loss)) if loss.is_integer() else repr(loss)
        parts.append(f"loss={loss_label}")
    impulse_profile = row.get("impulse_profile")
    if impulse_profile:
        parts.append(f"profile={impulse_profile}")
    return "|".join(parts)


def score_rows(
    rows: list[dict],
    expected: dict[str, list[int]],
    slices: dict[str, str],
) -> list[AmountOutcome]:
    """Pair transcribe/verbatim rows and score one result for each expected amount."""
    pairs: dict[tuple[str, str], dict[str, dict]] = {}
    for row in rows:
        mode = row.get("stt_mode")
        if mode not in {"transcribe", "verbatim"}:
            continue
        clip_id = row.get("clip_id")
        if clip_id not in expected:
            continue
        pairs.setdefault((clip_id, _condition(row)), {})[mode] = row

    outcomes: list[AmountOutcome] = []
    for (clip_id, condition), pair in sorted(pairs.items()):
        transcribe = pair.get("transcribe")
        verbatim = pair.get("verbatim")
        labels = expected[clip_id]
        available_rows = [row for row in (transcribe, verbatim) if row is not None]
        if any(row.get("transcription_error") for row in available_rows):
            decisions = [None] * len(labels)
            reasons = ["provider_error"] * len(labels)
        elif transcribe is None or verbatim is None:
            continue
        else:
            decisions_from_parser = decide_amounts(
                verbatim.get("transcript") or "",
                transcribe.get("transcript") or "",
                expected_count=len(labels),
            )
            # This benchmark has one recording and no separate confirmation, so
            # parser agreement alone is not an accepted money decision.
            decisions = [
                None if decision.reason is None else decision.paise
                for decision in decisions_from_parser
            ]
            reasons = [
                "independent_confirmation_required" if decision.reason is None else decision.reason
                for decision in decisions_from_parser
            ]

        slice_name = slices.get(clip_id, "unspecified")
        for expected_paise, decided_paise, reason in zip(labels, decisions, reasons):
            outcomes.append(AmountOutcome(
                clip_id=clip_id,
                condition=condition,
                slice=slice_name,
                expected_paise=expected_paise,
                decided_paise=decided_paise,
                reason=reason,
            ))
    return outcomes


def wilson_upper(failures: int, n: int, z: float = 1.96) -> float:
    """Return the upper Wilson score confidence bound for a binomial rate."""
    if n < 0 or failures < 0 or failures > n:
        raise ValueError("failures and n must satisfy 0 <= failures <= n")
    if z < 0:
        raise ValueError("z must be non-negative")
    if n == 0:
        return 1.0
    rate = failures / n
    z2 = z * z
    denominator = 1 + z2 / n
    center = rate + z2 / (2 * n)
    margin = z * math.sqrt(rate * (1 - rate) / n + z2 / (4 * n * n))
    return min(1.0, (center + margin) / denominator)


def summarize(outcomes: list[AmountOutcome]) -> list[dict]:
    """Aggregate error and abstention rates by benchmark slice and condition."""
    groups: dict[tuple[str, str], list[AmountOutcome]] = {}
    for outcome in outcomes:
        groups.setdefault((outcome.slice, outcome.condition), []).append(outcome)

    summaries: list[dict] = []
    for (slice_name, condition), group in sorted(groups.items()):
        amounts = len(group)
        wrong = sum(outcome.kind == "wrong_accepted" for outcome in group)
        correct = sum(outcome.kind == "correct" for outcome in group)
        abstained = sum(outcome.kind == "abstained" for outcome in group)
        reasons: dict[str, int] = {}
        for outcome in group:
            if outcome.kind == "abstained" and outcome.reason is not None:
                reasons[outcome.reason] = reasons.get(outcome.reason, 0) + 1
        summaries.append({
            "slice": slice_name,
            "condition": condition,
            "amounts": amounts,
            "wrong_accepted": wrong,
            "correct": correct,
            "abstained": abstained,
            "wrong_amount_confirmed_rate": wrong / amounts if amounts else 0.0,
            "wrong_amount_confirmed_upper95": wilson_upper(wrong, amounts),
            "abstain_rate": abstained / amounts if amounts else 0.0,
            "abstain_reasons": dict(sorted(reasons.items())),
        })
    return summaries


def score_number_agreement(reference: str, hypothesis: str) -> dict[str, int]:
    """Compare the hypothesis's parsed numbers with canonical reference numbers."""
    reference_numbers = parse_amounts(canonical_reference(reference))
    hypothesis_numbers = parse_amounts(hypothesis)
    ref_count = len(reference_numbers)
    counts = {
        "ref_numbers": ref_count,
        "matched": 0,
        "confident_wrong": 0,
        "abstain_equivalent": 0,
    }
    if ref_count != len(hypothesis_numbers):
        counts["abstain_equivalent"] = ref_count
        return counts

    for reference_number, hypothesis_number in zip(reference_numbers, hypothesis_numbers):
        if reference_number.status != "complete" or hypothesis_number.status != "complete":
            counts["abstain_equivalent"] += 1
        elif reference_number.paise == hypothesis_number.paise:
            counts["matched"] += 1
        else:
            counts["confident_wrong"] += 1
    return counts


def _read_result_rows(path: Path) -> list[dict]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid result JSON on line {line_number}: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"result line {line_number} must contain a JSON object")
        rows.append(row)
    return rows


def _load_exclusions() -> set[str]:
    root = Path(__file__).resolve().parents[3]
    path = root / "data" / "benchmarks" / "exclusions.json"
    return set(json.loads(path.read_text(encoding="utf-8-sig")))


def _load_clips(manifests: list[Path], excluded: set[str]) -> list[Clip]:
    clips_by_id: dict[str, Clip] = {}
    for path in manifests:
        for clip in load_manifest(path, require_audio=False):
            if clip.id in excluded:
                continue
            if clip.id in clips_by_id:
                raise ValueError(f"duplicate clip id across manifests: {clip.id}")
            clips_by_id[clip.id] = clip
    return [clips_by_id[clip_id] for clip_id in sorted(clips_by_id)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score benchmark amount safety outcomes.")
    parser.add_argument("--results", required=True, action="append", type=Path)
    parser.add_argument("--manifest", required=True, action="append", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    excluded = _load_exclusions()
    clips = _load_clips(args.manifest, excluded)
    expected = {clip.id: clip.expected_amounts_paise for clip in clips}
    slices = {clip.id: clip.stratum or "unspecified" for clip in clips}
    rows = [row for result_path in args.results for row in _read_result_rows(result_path)]
    outcomes = score_rows(rows, expected, slices)
    summaries = summarize(outcomes)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summaries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
