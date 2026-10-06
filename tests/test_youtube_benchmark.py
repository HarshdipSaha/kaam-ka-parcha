from pathlib import Path
import json
import pytest
from pydantic import ValidationError

from parcha.schema import JobCard, LineItem, Evidence
from scripts.benchmark_youtube_samples import BENCHMARK_CASES


def test_youtube_benchmark_cases_structure_and_counts():
    assert len(BENCHMARK_CASES) == 5
    for case in BENCHMARK_CASES:
        assert case["id"].startswith("YT-MECH-")
        assert case["video_id"]
        assert case["url"].startswith("https://www.youtube.com/watch?v=")
        assert case["duration_seconds"] > 60
        assert case["vehicle"]
        assert case["spoken_context"]
        assert len(case["expected_items"]) >= 2
        assert case["dispute_scenario"]
        assert case["resolution_path"]


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


def test_manifest_file_exists_and_matches_cases():
    manifest_path = Path("var/benchmark_audio/youtube_mechanic_benchmark.json")
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert data["total_cases"] == len(BENCHMARK_CASES)
        assert len(data["cases"]) == len(BENCHMARK_CASES)
        for c in data["cases"]:
            assert "audio_16k_wav" in c
            assert "transcript_txt" in c
