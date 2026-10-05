from datetime import date, datetime, timezone
import pytest
from pydantic import ValidationError
from parcha.schema import Delivery, Evidence, JobCard, LineItem, TranscriptLog, review_fields


def sample_card():
    return JobCard(
        items=[
            LineItem(id="part-1", label="front brake pad", kind="part", amount_paise=45000),
            LineItem(id="labour-1", label="labour", kind="labour", amount_paise=20000),
        ],
        delivery=Delivery(date=date(2026, 10, 5), window="evening", spoken="Somvaar shaam tak"),
        evidence=[
            Evidence(field="items.part-1.label", quote="front brake pad", review_score=0.95),
            Evidence(field="items.part-1.amount_paise", quote="₹450", review_score=0.95),
            Evidence(field="items.labour-1.label", quote="labour", review_score=0.95),
            Evidence(field="items.labour-1.amount_paise", quote="₹200", review_score=0.95),
            Evidence(field="delivery", quote="Somvaar shaam tak", review_score=0.9),
        ],
    )


def test_total_is_computed_and_not_input():
    assert sample_card().total_paise == 65000
    with pytest.raises(ValidationError):
        JobCard.model_validate({**sample_card().model_dump(), "total_paise": 123})


def test_negative_amount_and_duplicate_id_are_rejected():
    with pytest.raises(ValidationError):
        LineItem(id="part-1", label="pad", kind="part", amount_paise=-1)
    with pytest.raises(ValidationError):
        JobCard(
            items=[sample_card().items[0], sample_card().items[0]],
            delivery=sample_card().delivery,
            evidence=[],
        )


def test_review_flag_is_derived_from_evidence():
    card = sample_card().model_copy(
        update={"evidence": [Evidence(field="delivery", quote="Somvaar", review_score=0.3)]}
    )
    assert card.needs_review


def test_complete_card_needs_no_review():
    assert not sample_card().needs_review
    assert review_fields(sample_card()) == []


def test_missing_amount_and_delivery_can_be_reasked():
    draft = JobCard(
        items=[LineItem(id="part-1", label="front brake pad", kind="part", amount_paise=None)],
        delivery=None,
        evidence=[],
    )
    assert draft.needs_review
    assert draft.maybe_total_paise is None


def test_blank_label_and_invalid_id_pattern_are_rejected():
    with pytest.raises(ValidationError):
        LineItem(id="part-1", label="   ", kind="part", amount_paise=1000)
    with pytest.raises(ValidationError):
        LineItem(id="INVALID", label="pad", kind="part", amount_paise=1000)


def test_total_paise_raises_when_amounts_missing():
    draft = JobCard(
        items=[LineItem(id="part-1", label="front brake pad", kind="part", amount_paise=None)],
        delivery=None,
        evidence=[],
    )
    with pytest.raises(ValueError, match="total unavailable"):
        _ = draft.total_paise


def test_transcript_log_validates():
    now = datetime.now(timezone.utc)
    log = TranscriptLog(
        role="mechanic",
        mode="stt",
        text="front brake pad badla",
        recorded_at_utc=now,
    )
    assert log.role == "mechanic"
    assert log.text == "front brake pad badla"
    with pytest.raises(ValidationError):
        TranscriptLog(
            role="invalid_role",  # type: ignore[arg-type]
            mode="stt",
            text="hello",
            recorded_at_utc=now,
        )


@pytest.mark.parametrize("invalid_amount", [True, False, "750", 450.5, -10])
def test_line_item_amount_paise_rejects_non_integers_and_negatives(invalid_amount):
    with pytest.raises(ValidationError):
        LineItem(id="part-1", label="brake pad", kind="part", amount_paise=invalid_amount)


@pytest.mark.parametrize("valid_amount", [0, 45000, None])
def test_line_item_amount_paise_accepts_integers_and_none(valid_amount):
    item = LineItem(id="part-1", label="brake pad", kind="part", amount_paise=valid_amount)
    assert item.amount_paise == valid_amount
