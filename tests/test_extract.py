import json
from datetime import date, datetime, timezone
import httpx
import pytest
from parcha.extract import ExtractionError, Extractor
from parcha.schema import Delivery, Evidence, JobCard, LineItem

WHEN = datetime(2026, 10, 4, 10, tzinfo=timezone.utc) # Sunday Oct 4, 2026

def fake_chat(content, status_code=200):
    return httpx.Response(status_code, json={"choices": [{"message": {"content": json.dumps(content)}}]})

def test_valid_card_uses_both_transcripts_and_computes_total():
    payload = {"items": [
        {"id": "part-1", "label": "front brake pad", "kind": "part", "amount_paise": 45000},
        {"id": "labour-1", "label": "labour", "kind": "labour", "amount_paise": 20000}],
        "delivery": {"date": "2026-10-05", "window": "evening", "spoken": "Somvaar shaam tak"},
        "evidence": [
            {"field": "items.part-1.label", "quote": "front brake pad", "review_score": 0.95},
            {"field": "items.part-1.amount_paise", "quote": "₹450", "review_score": 0.95},
            {"field": "items.labour-1.label", "quote": "labour", "review_score": 0.95},
            {"field": "items.labour-1.amount_paise", "quote": "₹200", "review_score": 0.95},
            {"field": "delivery", "quote": "Somvaar shaam tak", "review_score": 0.9}]}
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    card = Extractor("http://test/v1", "key", "model", http).extract_card(
        "front brake pad ₹450, labour ₹200, Somvaar shaam tak",
        "front brake pad saade chaar sau, labour do sau, Somvaar shaam tak", WHEN)
    assert card.total_paise == 65000
    assert not card.needs_review

def test_unquoted_evidence_blocks_dispatch():
    payload = {"items": [{"id":"part-1","label":"pad","kind":"part","amount_paise":45000}],
               "delivery":{"date":"2026-10-05","window":"evening","spoken":"Somvaar"},
               "evidence":[{"field":"items.part-1.amount_paise","quote":"₹999","review_score":0.99}]}
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    card = Extractor("http://test/v1", "key", "model", http).extract_card("₹450 Somvaar", "", WHEN)
    assert card.needs_review


def test_duplicate_item_from_corrupted_transcribe_pass_prefers_verbatim_evidence():
    """A corrupted normal pass must not create a second, lower-value job-card item."""
    payload = {
        "items": [
            {"id": "part-1", "label": "फ्रंट ब्रेक पैड", "kind": "part", "amount_paise": 10000},
            {"id": "part-2", "label": "फ्रंट ब्रेक पैड", "kind": "part", "amount_paise": 45000},
            {"id": "labour-1", "label": "लेबर", "kind": "labour", "amount_paise": 20000},
        ],
        "delivery": {"date": "2026-10-06", "window": "evening", "spoken": True},
        "evidence": [
            {"field": "items.part-1.label", "quote": "फ्रंट ब्रेक पैड 04:30 100", "review_score": 1.0},
            {"field": "items.part-1.amount_paise", "quote": "फ्रंट ब्रेक पैड 04:30 100", "review_score": 1.0},
            {"field": "items.part-2.label", "quote": "फ्रंट ब्रेक पैड साढ़े चार सौ", "review_score": 1.0},
            {"field": "items.part-2.amount_paise", "quote": "फ्रंट ब्रेक पैड साढ़े चार सौ", "review_score": 1.0},
            {"field": "items.labour-1.label", "quote": "लेबर 200", "review_score": 1.0},
            {"field": "items.labour-1.amount_paise", "quote": "लेबर 200", "review_score": 1.0},
            {"field": "delivery", "quote": "मंगलवार शाम तक", "review_score": 1.0},
        ],
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    card = Extractor("http://test/v1", "key", "model", http).extract_card(
        "फ्रंट ब्रेक पैड 04:30 100 लेबर 200 मंगलवार शाम तक",
        "फ्रंट ब्रेक पैड साढ़े चार सौ लेबर दो सौ मंगलवार शाम तक",
        datetime(2026, 10, 5, 10, tzinfo=timezone.utc),
    )

    assert [(item.id, item.amount_paise) for item in card.items] == [
        ("part-1", 45000),
        ("labour-1", 20000),
    ]
    assert card.total_paise == 65000
    assert card.delivery is not None
    assert card.delivery.spoken == "मंगलवार शाम तक"
    assert not card.needs_review

def test_semantic_duplicate_label_variant_prefers_verbatim_evidence():
    """A partial or punctuated label from one STT pass must not create a second part."""
    payload = {
        "items": [
            {"id": "part-1", "label": "brake-pad", "kind": "part", "amount_paise": 10000},
            {"id": "part-2", "label": "front brake pad", "kind": "part", "amount_paise": 45000},
        ],
        "delivery": None,
        "evidence": [
            {"field": "items.part-1.label", "quote": "brake-pad 100", "review_score": 1.0},
            {"field": "items.part-1.amount_paise", "quote": "brake-pad 100", "review_score": 1.0},
            {"field": "items.part-2.label", "quote": "front brake pad saade chaar sau", "review_score": 1.0},
            {"field": "items.part-2.amount_paise", "quote": "front brake pad saade chaar sau", "review_score": 1.0},
        ],
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    card = Extractor("http://test/v1", "key", "model", http).extract_card(
        "brake-pad 100",
        "front brake pad saade chaar sau",
        WHEN,
    )
    assert [(item.label, item.amount_paise) for item in card.items] == [("front brake pad", 45000)]


@pytest.mark.parametrize("bad_amount", [True, False, "750", 450.5, -10])
def test_malformed_amount_is_rejected_before_it_can_change_a_total(bad_amount):
    payload = {
        "items": [{"id": "part-1", "label": "brake pad", "kind": "part", "amount_paise": bad_amount}],
        "delivery": None,
        "evidence": [],
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    with pytest.raises(ExtractionError, match="(amount_paise must be an integer|greater than or equal to 0)"):
        Extractor("http://test/v1", "key", "model", http).extract_card("brake pad", "brake pad", WHEN)


@pytest.mark.parametrize("bad_amount", [True, False, "750", 450.5, -10])
def test_malformed_amount_in_extract_field_is_rejected(bad_amount):
    old_card = JobCard(
        items=[LineItem(id="part-1", label="brake pad", kind="part", amount_paise=None)],
        delivery=None,
        evidence=[],
    )
    payload = {
        "value": bad_amount,
        "evidence_quote": "750",
        "review_score": 0.9,
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    with pytest.raises(ExtractionError, match="Invalid item update"):
        Extractor("http://test/v1", "key", "model", http).extract_field(
            "items.part-1.amount_paise", "750 rupaye", old_card, WHEN
        )


def test_semantic_duplicate_word_order_and_punctuation():
    payload = {
        "items": [
            {"id": "part-1", "label": "brake pad, front", "kind": "part", "amount_paise": 45000},
            {"id": "part-2", "label": "front brake pad", "kind": "part", "amount_paise": 45000},
        ],
        "delivery": None,
        "evidence": [
            {"field": "items.part-1.label", "quote": "front brake pad", "review_score": 0.95},
            {"field": "items.part-1.amount_paise", "quote": "450", "review_score": 0.95},
            {"field": "items.part-2.label", "quote": "front brake pad", "review_score": 0.95},
            {"field": "items.part-2.amount_paise", "quote": "450", "review_score": 0.95},
        ],
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    card = Extractor("http://test/v1", "key", "model", http).extract_card(
        "front brake pad 450", "front brake pad 450", WHEN
    )
    assert len(card.items) == 1
    assert card.items[0].label in {"front brake pad", "brake pad, front"}


def test_negative_front_vs_rear_brake_pad_retained_as_separate_parts():
    payload = {
        "items": [
            {"id": "part-1", "label": "front brake pad", "kind": "part", "amount_paise": 45000},
            {"id": "part-2", "label": "rear brake pad", "kind": "part", "amount_paise": 35000},
        ],
        "delivery": None,
        "evidence": [
            {"field": "items.part-1.label", "quote": "front brake pad", "review_score": 1.0},
            {"field": "items.part-1.amount_paise", "quote": "450", "review_score": 1.0},
            {"field": "items.part-2.label", "quote": "rear brake pad", "review_score": 1.0},
            {"field": "items.part-2.amount_paise", "quote": "350", "review_score": 1.0},
        ],
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    card = Extractor("http://test/v1", "key", "model", http).extract_card(
        "front brake pad 450, rear brake pad 350",
        "front brake pad 450, rear brake pad 350",
        WHEN,
    )
    assert len(card.items) == 2
    labels = {it.label for it in card.items}
    assert labels == {"front brake pad", "rear brake pad"}
    assert card.total_paise == 80000


def test_negative_brake_pad_vs_brake_disc_retained_as_separate_parts():
    payload = {
        "items": [
            {"id": "part-1", "label": "brake pad", "kind": "part", "amount_paise": 45000},
            {"id": "part-2", "label": "brake disc", "kind": "part", "amount_paise": 120000},
        ],
        "delivery": None,
        "evidence": [
            {"field": "items.part-1.label", "quote": "brake pad", "review_score": 1.0},
            {"field": "items.part-1.amount_paise", "quote": "450", "review_score": 1.0},
            {"field": "items.part-2.label", "quote": "brake disc", "review_score": 1.0},
            {"field": "items.part-2.amount_paise", "quote": "1200", "review_score": 1.0},
        ],
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    card = Extractor("http://test/v1", "key", "model", http).extract_card(
        "brake pad 450, brake disc 1200",
        "brake pad 450, brake disc 1200",
        WHEN,
    )
    assert len(card.items) == 2
    labels = {it.label for it in card.items}
    assert labels == {"brake pad", "brake disc"}
    assert card.total_paise == 165000


def test_tie_candidate_removes_total_and_requires_review():
    payload = {
        "items": [
            {"id": "part-1", "label": "front brake pad", "kind": "part", "amount_paise": 45000},
            {"id": "part-2", "label": "brake-pad", "kind": "part", "amount_paise": 10000},
        ],
        "delivery": None,
        "evidence": [
            {"field": "items.part-1.label", "quote": "unmentioned phrase", "review_score": 0.5},
            {"field": "items.part-1.amount_paise", "quote": "unmentioned 450", "review_score": 0.5},
            {"field": "items.part-2.label", "quote": "unmentioned phrase", "review_score": 0.5},
            {"field": "items.part-2.amount_paise", "quote": "unmentioned 100", "review_score": 0.5},
        ],
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    card = Extractor("http://test/v1", "key", "model", http).extract_card(
        "verbatim something else",
        "verbatim something else",
        WHEN,
    )
    assert len(card.items) == 1
    assert card.items[0].amount_paise is None
    assert card.needs_review is True
    assert card.maybe_total_paise is None



def test_missing_amount_is_a_reaskable_draft():
    payload = {"items": [{"id":"part-1","label":"front brake pad","kind":"part",
                          "amount_paise":None}], "delivery":None,
               "evidence":[{"field":"items.part-1.label","quote":"front brake pad",
                            "review_score":0.9}]}
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    card = Extractor("http://test/v1", "key", "model", http).extract_card(
        "front brake pad", "front brake pad", WHEN)
    assert card.needs_review and card.maybe_total_paise is None

def test_key_rotation_on_429():
    attempts = []
    def handler(request):
        auth = request.headers.get("authorization", "")
        attempts.append(auth)
        if "key1" in auth:
            return httpx.Response(429, json={"error": {"message": "rate limit"}})
        payload = {"items": [{"id":"part-1","label":"pad","kind":"part","amount_paise":45000}],
                   "delivery":None,
                   "evidence":[{"field":"items.part-1.label","quote":"pad","review_score":0.9},
                               {"field":"items.part-1.amount_paise","quote":"450","review_score":0.9}]}
        return fake_chat(payload)
    http = httpx.Client(transport=httpx.MockTransport(handler))
    extractor = Extractor("http://test/v1", "key1,key2", "model", http)
    card = extractor.extract_card("pad 450", "pad 450", WHEN)
    assert len(attempts) == 2
    assert "Bearer key1" in attempts[0]
    assert "Bearer key2" in attempts[1]

def test_single_item_amount_correction():
    old_card = JobCard(
        items=(LineItem(id="part-1", label="front brake pad", kind="part", amount_paise=None),),
        delivery=None,
        evidence=(Evidence(field="items.part-1.label", quote="front brake pad", review_score=0.9),),
    )
    payload = {
        "field": "items.part-1.amount_paise",
        "value": 45000,
        "evidence_quote": "chaar sau pachaas",
        "review_score": 0.95,
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    extractor = Extractor("http://test/v1", "key", "model", http)
    new_card = extractor.extract_field(
        "items.part-1.amount_paise",
        "chaar sau pachaas",
        old_card,
    )
    assert new_card.items[0].amount_paise == 45000
    assert new_card.items[0].label == "front brake pad"
    assert new_card.items[0].kind == "part"
    ev = next(e for e in new_card.evidence if e.field == "items.part-1.amount_paise")
    assert ev.quote == "chaar sau pachaas"
    assert ev.review_score == 0.95

def test_ambiguous_amount_correction_raises_error():
    old_card = JobCard(
        items=(
            LineItem(id="part-1", label="front brake pad", kind="part", amount_paise=40000),
            LineItem(id="labour-1", label="labour", kind="labour", amount_paise=20000),
        ),
        delivery=None,
        evidence=(
            Evidence(field="items.part-1.label", quote="front brake pad", review_score=0.9),
            Evidence(field="items.part-1.amount_paise", quote="400", review_score=0.9),
            Evidence(field="items.labour-1.label", quote="labour", review_score=0.9),
            Evidence(field="items.labour-1.amount_paise", quote="200", review_score=0.9),
        ),
    )
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat({})))
    extractor = Extractor("http://test/v1", "key", "model", http)
    with pytest.raises(ExtractionError, match="which item?"):
        extractor.extract_field(
            "amount_paise",
            "nahi, saade chaar sau",
            old_card,
        )
    with pytest.raises(ExtractionError, match="which item?"):
        extractor.extract_field(
            "items.part-1.amount_paise",
            "nahi, saade chaar sau",
            old_card,
        )

def test_delivery_date_correction_preserves_line_items_byte_for_byte():
    old_item1 = LineItem(id="part-1", label="front brake pad", kind="part", amount_paise=45000)
    old_item2 = LineItem(id="labour-1", label="labour", kind="labour", amount_paise=20000)
    old_card = JobCard(
        items=(old_item1, old_item2),
        delivery=Delivery(date=date(2026, 10, 5), window="morning", spoken="Somvaar subah"),
        evidence=(
            Evidence(field="items.part-1.label", quote="front brake pad", review_score=0.95),
            Evidence(field="items.part-1.amount_paise", quote="₹450", review_score=0.95),
            Evidence(field="items.labour-1.label", quote="labour", review_score=0.95),
            Evidence(field="items.labour-1.amount_paise", quote="₹200", review_score=0.95),
            Evidence(field="delivery", quote="Somvaar subah", review_score=0.9),
        ),
    )
    payload = {
        "field": "delivery",
        "value": {"date": "2026-10-06", "window": "evening", "spoken": "Mangalvaar shaam tak"},
        "evidence_quote": "Mangalvaar shaam tak",
        "review_score": 0.95,
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    extractor = Extractor("http://test/v1", "key", "model", http)
    new_card = extractor.extract_field(
        "delivery",
        "Mangalvaar shaam tak",
        old_card,
        when=WHEN,
    )
    # Line items preserved byte-for-byte
    assert new_card.items == old_card.items
    assert new_card.items[0] is old_item1
    assert new_card.items[1] is old_item2
    # Delivery updated
    assert new_card.delivery == Delivery(date=date(2026, 10, 6), window="evening", spoken="Mangalvaar shaam tak")
    # Evidence for delivery updated
    del_ev = next(e for e in new_card.evidence if e.field == "delivery")
    assert del_ev.quote == "Mangalvaar shaam tak"
    assert del_ev.review_score == 0.95
    # Other evidence preserved byte-for-byte
    assert next(e for e in new_card.evidence if e.field == "items.part-1.label") is old_card.evidence[0]

def test_weekday_resolution_and_invalid_next_week_date():
    # Sunday Oct 4, 2026 -> next Monday is Oct 5, 2026
    valid_payload = {
        "items": [{"id": "part-1", "label": "brake pad", "kind": "part", "amount_paise": 45000}],
        "delivery": {"date": "2026-10-05", "window": "evening", "spoken": "Somvaar shaam"},
        "evidence": [
            {"field": "items.part-1.label", "quote": "brake pad", "review_score": 0.9},
            {"field": "items.part-1.amount_paise", "quote": "450", "review_score": 0.9},
            {"field": "delivery", "quote": "Somvaar shaam", "review_score": 0.95},
        ],
    }
    http_valid = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(valid_payload)))
    card_valid = Extractor("http://test/v1", "key", "model", http_valid).extract_card(
        "brake pad 450 Somvaar shaam", "", WHEN
    )
    del_ev = next(e for e in card_valid.evidence if e.field == "delivery")
    assert del_ev.review_score == 0.95
    assert not card_valid.needs_review

    # Invalid next week date: Oct 12 instead of Oct 5
    invalid_payload = {
        "items": [{"id": "part-1", "label": "brake pad", "kind": "part", "amount_paise": 45000}],
        "delivery": {"date": "2026-10-12", "window": "evening", "spoken": "Somvaar shaam"},
        "evidence": [
            {"field": "items.part-1.label", "quote": "brake pad", "review_score": 0.9},
            {"field": "items.part-1.amount_paise", "quote": "450", "review_score": 0.9},
            {"field": "delivery", "quote": "Somvaar shaam", "review_score": 0.95},
        ],
    }
    http_invalid = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(invalid_payload)))
    card_invalid = Extractor("http://test/v1", "key", "model", http_invalid).extract_card(
        "brake pad 450 Somvaar shaam", "", WHEN
    )
    del_ev_invalid = next(e for e in card_invalid.evidence if e.field == "delivery")
    assert del_ev_invalid.review_score == 0.0
    assert card_invalid.needs_review

def test_delivery_ambiguity_conditions():
    # 1. Multiple weekdays mentioned: Somvaar ya Mangalvaar
    multi_payload = {
        "items": [{"id": "part-1", "label": "pad", "kind": "part", "amount_paise": 45000}],
        "delivery": {"date": "2026-10-05", "window": "evening", "spoken": "Somvaar ya Mangalvaar"},
        "evidence": [
            {"field": "items.part-1.label", "quote": "pad", "review_score": 0.9},
            {"field": "items.part-1.amount_paise", "quote": "450", "review_score": 0.9},
            {"field": "delivery", "quote": "Somvaar ya Mangalvaar", "review_score": 0.95},
        ],
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(multi_payload)))
    card = Extractor("http://test/v1", "key", "model", http).extract_card("pad 450 Somvaar ya Mangalvaar", "", WHEN)
    del_ev = next(e for e in card.evidence if e.field == "delivery")
    assert del_ev.review_score == 0.0

    # 2. Same day weekday: Ravivaar on Sunday Oct 4
    same_payload = {
        "items": [{"id": "part-1", "label": "pad", "kind": "part", "amount_paise": 45000}],
        "delivery": {"date": "2026-10-04", "window": "evening", "spoken": "Ravivaar shaam"},
        "evidence": [
            {"field": "items.part-1.label", "quote": "pad", "review_score": 0.9},
            {"field": "items.part-1.amount_paise", "quote": "450", "review_score": 0.9},
            {"field": "delivery", "quote": "Ravivaar shaam", "review_score": 0.95},
        ],
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(same_payload)))
    card = Extractor("http://test/v1", "key", "model", http).extract_card("pad 450 Ravivaar shaam", "", WHEN)
    del_ev = next(e for e in card.evidence if e.field == "delivery")
    assert del_ev.review_score == 0.0

    # 3. kal / कल mentioned without unambiguous date
    kal_payload = {
        "items": [{"id": "part-1", "label": "pad", "kind": "part", "amount_paise": 45000}],
        "delivery": {"date": "2026-10-05", "window": "evening", "spoken": "kal shaam tak"},
        "evidence": [
            {"field": "items.part-1.label", "quote": "pad", "review_score": 0.9},
            {"field": "items.part-1.amount_paise", "quote": "450", "review_score": 0.9},
            {"field": "delivery", "quote": "kal shaam tak", "review_score": 0.95},
        ],
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(kal_payload)))
    card = Extractor("http://test/v1", "key", "model", http).extract_card("pad 450 kal shaam tak", "", WHEN)
    del_ev = next(e for e in card.evidence if e.field == "delivery")
    assert del_ev.review_score == 0.0

def test_all_keys_rate_limited_raises():
    def handler(request):
        return httpx.Response(429, json={"error": {"message": "rate limit"}})
    http = httpx.Client(transport=httpx.MockTransport(handler))
    extractor = Extractor("http://test/v1", "key1,key2", "model", http)
    with pytest.raises(ExtractionError, match="429"):
        extractor.extract_card("pad 450", "pad 450", WHEN)

def test_extract_field_label_update():
    old_card = JobCard(
        items=(LineItem(id="part-1", label="brake", kind="part", amount_paise=45000),),
        delivery=None,
        evidence=(
            Evidence(field="items.part-1.label", quote="brake", review_score=0.9),
            Evidence(field="items.part-1.amount_paise", quote="450", review_score=0.9),
        ),
    )
    payload = {
        "field": "items.part-1.label",
        "value": "front brake pad",
        "evidence_quote": "front brake pad",
        "review_score": 0.95,
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    extractor = Extractor("http://test/v1", "key", "model", http)
    new_card = extractor.extract_field(
        "items.part-1.label",
        "front brake pad daal dena",
        old_card,
    )
    assert new_card.items[0].label == "front brake pad"
    assert new_card.items[0].amount_paise == 45000
    ev = next(e for e in new_card.evidence if e.field == "items.part-1.label")
    assert ev.quote == "front brake pad"
    assert ev.review_score == 0.95

def test_extract_field_unquoted_evidence_sets_zero_score():
    old_card = JobCard(
        items=(LineItem(id="part-1", label="brake", kind="part", amount_paise=45000),),
        delivery=None,
        evidence=(
            Evidence(field="items.part-1.label", quote="brake", review_score=0.9),
            Evidence(field="items.part-1.amount_paise", quote="450", review_score=0.9),
        ),
    )
    # The evidence_quote "teen sau" does not appear in "paanch sau"
    payload = {
        "field": "items.part-1.amount_paise",
        "value": 30000,
        "evidence_quote": "teen sau",
        "review_score": 0.95,
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    extractor = Extractor("http://test/v1", "key", "model", http)
    new_card = extractor.extract_field(
        "items.part-1.amount_paise",
        "paanch sau rupaye",
        old_card,
    )
    ev = next(e for e in new_card.evidence if e.field == "items.part-1.amount_paise")
    assert ev.review_score == 0.0

def test_extract_card_markdown_code_fence():
    inner_payload = {
        "items": [{"id": "part-1", "label": "oil filter", "kind": "part", "amount_paise": 15000}],
        "delivery": None,
        "evidence": [
            {"field": "items.part-1.label", "quote": "oil filter", "review_score": 0.9},
            {"field": "items.part-1.amount_paise", "quote": "150", "review_score": 0.9},
        ],
    }
    fenced_content = f"```json\n{json.dumps(inner_payload)}\n```"
    http = httpx.Client(transport=httpx.MockTransport(
        lambda _: httpx.Response(200, json={"choices": [{"message": {"content": fenced_content}}]})
    ))
    extractor = Extractor("http://test/v1", "key", "model", http)
    card = extractor.extract_card("oil filter 150", "oil filter 150", WHEN)
    assert card.items[0].label == "oil filter"
    assert card.items[0].amount_paise == 15000

def test_extract_card_invalid_json_raises():
    http = httpx.Client(transport=httpx.MockTransport(
        lambda _: httpx.Response(200, json={"choices": [{"message": {"content": "not json at all"}}]})
    ))
    extractor = Extractor("http://test/v1", "key", "model", http)
    with pytest.raises(ExtractionError, match="No JSON object found"):
        extractor.extract_card("pad 450", "pad 450", WHEN)
