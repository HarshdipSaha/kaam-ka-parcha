from pathlib import Path
import json
import pytest
from pydantic import ValidationError

from parcha.schema import JobCard, LineItem, Evidence
from scripts.benchmark_youtube_samples import load_cases

# Synthetic stand-ins: real third-party video metadata is never committed.
BENCHMARK_CASES = [
    {
        "id": "YT-MECH-001",
        "expected_items": [
            {"id": "part-1", "label": "Synthetic Part A", "kind": "part", "amount_paise": 378500, "quote": "synthetic quote a"},
            {"id": "part-2", "label": "Synthetic Part B", "kind": "part", "amount_paise": None, "quote": "synthetic quote b"},
            {"id": "labour-1", "label": "Synthetic Labour", "kind": "labour", "amount_paise": 35000, "quote": "synthetic quote c"},
        ],
    },
    {
        "id": "YT-MECH-002",
        "expected_items": [
            {"id": "part-1", "label": "Synthetic Part C", "kind": "part", "amount_paise": 120000},
            {"id": "labour-1", "label": "Synthetic Labour", "kind": "labour", "amount_paise": 50000},
        ],
    },
]


def test_load_cases_requires_local_manifest(tmp_path):
    with pytest.raises(SystemExit):
        load_cases(tmp_path / "missing.json")
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(BENCHMARK_CASES), encoding="utf-8")
    assert load_cases(path) == BENCHMARK_CASES


def test_youtube_benchmark_items_satisfy_kaam_ka_parcha_schema():
    for case in BENCHMARK_CASES:
        items = []
        evidence = []
        for raw_item in case["expected_items"]:
            item = LineItem(
                id=raw_item["id"],
                label=raw_item["label"],
                kind=raw_item["kind"],
                amount_paise=raw_item["amount_paise"],
            )
            items.append(item)
            if raw_item.get("quote"):
                evidence.append(
                    Evidence(
                        field=f"items.{item.id}.label",
                        quote=raw_item["quote"],
                        review_score=0.95,
                    )
                )

        # Build JobCard and verify strict schema validation
        card = JobCard(items=tuple(items), evidence=tuple(evidence))
        assert len(card.items) == len(case["expected_items"])

        # Check paise integer constraints
        for item in card.items:
            if item.amount_paise is not None:
                assert isinstance(item.amount_paise, int)
                assert item.amount_paise > 0

        # Verify money integrity: total is computed or requires review if any amount is None
        has_none_amt = any(it.amount_paise is None for it in card.items)
        if has_none_amt:
            assert card.maybe_total_paise is None
            assert card.needs_review is True
            with pytest.raises(ValueError, match="total unavailable"):
                _ = card.total_paise
        else:
            expected_total = sum(it.amount_paise for it in card.items)
            assert card.total_paise == expected_total
            assert card.maybe_total_paise == expected_total


def test_youtube_benchmark_rejects_invalid_money_types():
    # Verify rejection of float and string amounts per AGENTS.md correctness rules
    with pytest.raises(ValidationError):
        LineItem(id="part-1", label="Clutch Bearing", kind="part", amount_paise=3785.50)  # type: ignore

    with pytest.raises(ValidationError):
        LineItem(id="part-1", label="Clutch Bearing", kind="part", amount_paise="378500")  # type: ignore
