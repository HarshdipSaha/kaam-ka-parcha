from datetime import date
import json
from pathlib import Path
import pytest

from parcha.lab.eval_corpus import (
    compare_items,
    evaluate_extracted_card,
    load_corpus,
    summarize_results,
)
from parcha.schema import Delivery, Evidence, JobCard, LineItem



@pytest.fixture
def corpus_data():
    return load_corpus()


def test_corpus_manifest_categories_and_minimum_counts(corpus_data):
    assert len(corpus_data) >= 72

    cat_counts = {}
    for case in corpus_data:
        cat_counts[case["category"]] = cat_counts.get(case["category"], 0) + 1

    # Verify all 8 categories meet minimum counts
    assert cat_counts.get("clean_workshop_speech", 0) >= 10
    assert cat_counts.get("engine_road_workshop_noise", 0) >= 10
    assert cat_counts.get("different_speakers_regions_pacing", 0) >= 10
    assert cat_counts.get("multiple_parts_and_labour", 0) >= 10
    assert cat_counts.get("corrections_reasks", 0) >= 8
    assert cat_counts.get("ambiguous_or_missing_amounts", 0) >= 8
    assert cat_counts.get("adversarial_numbers_timestamps", 0) >= 8
    assert cat_counts.get("duplicate_near_duplicate_labels", 0) >= 8


def test_corpus_provenance_anonymisation_and_splits(corpus_data):
    splits = {"development": 0, "holdout": 0, "challenge": 0}
    for case in corpus_data:
        assert case["provenance"]
        assert case["permission_status"] == "open_evaluation_consented"
        assert case["anonymisation_status"] == "synthetic_customer_identifiers"
        assert case["language_mix"]
        assert "approx_snr_db" in case
        assert "expected_items" in case
        assert case["split"] in splits
        splits[case["split"]] += 1

    # Ensure separate development and untouched holdout/challenge sets
    assert splits["development"] >= 40
    assert splits["holdout"] >= 10
    assert splits["challenge"] >= 10


def test_eval_metrics_computation_on_synthetic_cards():
    case = {
        "id": "TEST-01",
        "category": "clean_workshop_speech",
        "split": "development",
        "expected_items": [
            {"kind": "part", "label": "front brake pad", "amount_paise": 45000},
            {"kind": "labour", "label": "labour", "amount_paise": 20000},
        ],
        "expected_total_paise": 65000,
        "requires_review": False,
    }

    # 1. Perfect card
    good_card = JobCard(
        items=[
            LineItem(id="part-1", label="front brake pad", kind="part", amount_paise=45000),
            LineItem(id="labour-1", label="labour", kind="labour", amount_paise=20000),
        ],
        delivery=Delivery(date=date(2026, 10, 5), window="evening", spoken="Somvaar shaam tak"),
        evidence=[
            Evidence(field="items.part-1.label", quote="front brake pad", review_score=1.0),
            Evidence(field="items.part-1.amount_paise", quote="450", review_score=1.0),
            Evidence(field="items.labour-1.label", quote="labour", review_score=1.0),
            Evidence(field="items.labour-1.amount_paise", quote="200", review_score=1.0),
            Evidence(field="delivery", quote="Somvaar shaam tak", review_score=1.0),
        ],
    )
    res_good = evaluate_extracted_card(case, good_card)
    assert res_good.passed
    assert res_good.exact_item_match
    assert res_good.amount_match
    assert res_good.total_match
    assert not res_good.false_confirmation
    assert not res_good.false_merge
    assert not res_good.false_split
    assert res_good.customer_confirmation_ready

    # 2. Corrupted total without review flag (False confirmation)
    bad_card = JobCard(
        items=[
            LineItem(id="part-1", label="front brake pad", kind="part", amount_paise=10000),
            LineItem(id="labour-1", label="labour", kind="labour", amount_paise=20000),
        ],
        delivery=Delivery(date=date(2026, 10, 5), window="evening", spoken="Somvaar shaam tak"),
        evidence=[
            Evidence(field="items.part-1.label", quote="front brake pad", review_score=1.0),
            Evidence(field="items.part-1.amount_paise", quote="100", review_score=1.0),
            Evidence(field="items.labour-1.label", quote="labour", review_score=1.0),
            Evidence(field="items.labour-1.amount_paise", quote="200", review_score=1.0),
            Evidence(field="delivery", quote="Somvaar shaam tak", review_score=1.0),
        ],
    )

    res_bad = evaluate_extracted_card(case, bad_card)
    assert not res_bad.passed
    assert res_bad.false_confirmation
    assert not res_bad.customer_confirmation_ready

    # 3. False merge (part collapsed)
    merged_card = JobCard(
        items=[
            LineItem(id="part-1", label="front brake pad", kind="part", amount_paise=45000),
        ],
        delivery=None,
        evidence=[
            Evidence(field="items.part-1.label", quote="front brake pad", review_score=1.0),
            Evidence(field="items.part-1.amount_paise", quote="450", review_score=1.0),
        ],
    )
    res_merged = evaluate_extracted_card(case, merged_card)
    assert res_merged.false_merge
    assert not res_merged.exact_item_match

    # Summary metrics
    metrics = summarize_results([res_good, res_bad, res_merged])
    assert metrics["total_cases"] == 3
    assert metrics["false_confirmation_rate"] == round(1 / 3, 4)
    assert metrics["false_merge_rate"] == round(1 / 3, 4)
    assert metrics["customer_confirmation_success_rate"] == round(1 / 3, 4)


def test_ambiguous_case_requires_review_behaviour():
    case = {
        "id": "TEST-AMBIGUOUS",
        "category": "ambiguous_or_missing_amounts",
        "split": "holdout",
        "expected_items": [
            {"kind": "part", "label": "front brake pad", "amount_paise": None},
        ],
        "expected_total_paise": None,
        "requires_review": True,
    }
    card_with_review = JobCard(
        items=[
            LineItem(id="part-1", label="front brake pad", kind="part", amount_paise=None),
        ],
        delivery=None,
        evidence=[],
    )
    res = evaluate_extracted_card(case, card_with_review)
    assert res.passed
    assert res.correct_review_action
    assert not res.false_confirmation
