"""Generalisation Evaluation Suite for Kaam Ka Parcha.

Evaluates extraction across 8 operational categories:
1. Clean Hindi/Hinglish workshop speech
2. Engine/road/workshop noise
3. Different speakers, regions, and pacing
4. Multiple parts and labour
5. Corrections and re-asks
6. Ambiguous or missing amounts
7. Adversarial number confusions and timestamps
8. Duplicate or near-duplicate labels
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable

from parcha.extract import _canonical_label, _deduplicate_items
from parcha.schema import JobCard, LineItem


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    category: str
    split: str
    passed: bool
    exact_item_match: bool
    amount_match: bool
    total_match: bool
    false_confirmation: bool
    false_merge: bool
    false_split: bool
    correct_review_action: bool
    customer_confirmation_ready: bool
    error: str | None = None


def normalize_item_label(label: str | None) -> str:
    return _canonical_label(label)


def compare_items(
    expected_items: list[dict[str, Any]],
    actual_items: list[LineItem] | tuple[LineItem, ...],
) -> tuple[bool, bool, bool, bool]:
    """Returns (exact_item_match, amount_match, false_merge, false_split)."""
    exp_labels = [normalize_item_label(it["label"]) for it in expected_items]
    act_labels = [normalize_item_label(it.label) for it in actual_items]

    # False merge: expected distinct items collapsed into fewer items
    false_merge = len(act_labels) < len(exp_labels)
    # False split: same item duplicated into more items
    false_split = len(act_labels) > len(exp_labels)

    exact_item_match = sorted(exp_labels) == sorted(act_labels)

    # Check amounts
    amount_match = True
    for exp in expected_items:
        exp_lbl = normalize_item_label(exp["label"])
        matching_act = next(
            (it for it in actual_items if normalize_item_label(it.label) == exp_lbl),
            None,
        )
        if matching_act is None:
            amount_match = False
            break
        if matching_act.amount_paise != exp.get("amount_paise"):
            amount_match = False
            break

    return exact_item_match, amount_match, false_merge, false_split


def evaluate_extracted_card(case: dict[str, Any], card: JobCard) -> CaseResult:
    expected_items = case["expected_items"]
    expected_total = case.get("expected_total_paise")
    expected_review = case.get("requires_review", False)

    exact_item_match, amount_match, false_merge, false_split = compare_items(
        expected_items, card.items
    )

    actual_total = card.maybe_total_paise
    total_match = (actual_total == expected_total)

    # False confirmation: wrong complete card presented as ready
    has_wrong_data = not (exact_item_match and amount_match and total_match)
    false_confirmation = (not card.needs_review) and has_wrong_data

    # Correct review / re-ask behaviour
    correct_review_action = (card.needs_review == expected_review)

    # End-to-end confirmation ready: complete, exact, no review required
    customer_confirmation_ready = (
        not card.needs_review
        and exact_item_match
        and amount_match
        and total_match
        and not expected_review
    )

    passed = (
        exact_item_match
        and amount_match
        and total_match
        and correct_review_action
        and not false_confirmation
    )

    return CaseResult(
        case_id=case["id"],
        category=case["category"],
        split=case["split"],
        passed=passed,
        exact_item_match=exact_item_match,
        amount_match=amount_match,
        total_match=total_match,
        false_confirmation=false_confirmation,
        false_merge=false_merge,
        false_split=false_split,
        correct_review_action=correct_review_action,
        customer_confirmation_ready=customer_confirmation_ready,
    )


def summarize_results(results: list[CaseResult]) -> dict[str, Any]:
    n = len(results)
    if n == 0:
        return {"total_cases": 0}

    passed_count = sum(1 for r in results if r.passed)
    exact_item_count = sum(1 for r in results if r.exact_item_match)
    amount_count = sum(1 for r in results if r.amount_match)
    total_count = sum(1 for r in results if r.total_match)
    false_conf_count = sum(1 for r in results if r.false_confirmation)
    false_merge_count = sum(1 for r in results if r.false_merge)
    false_split_count = sum(1 for r in results if r.false_split)
    correct_review_count = sum(1 for r in results if r.correct_review_action)
    confirmation_count = sum(1 for r in results if r.customer_confirmation_ready)

    return {
        "total_cases": n,
        "overall_pass_rate": round(passed_count / n, 4),
        "exact_item_set_match_rate": round(exact_item_count / n, 4),
        "amount_accuracy_rate": round(amount_count / n, 4),
        "total_accuracy_rate": round(total_count / n, 4),
        "false_confirmation_rate": round(false_conf_count / n, 4),
        "false_merge_rate": round(false_merge_count / n, 4),
        "false_split_rate": round(false_split_count / n, 4),
        "correct_review_reask_rate": round(correct_review_count / n, 4),
        "customer_confirmation_success_rate": round(confirmation_count / n, 4),
    }


def load_corpus(path: Path | str | None = None) -> list[dict[str, Any]]:
    if path is None:
        path = Path(__file__).resolve().parents[3] / "data" / "generalization_corpus_v1.json"
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Evaluation corpus not found at {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    return data["cases"]
