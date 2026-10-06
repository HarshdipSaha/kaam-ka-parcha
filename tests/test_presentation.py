from datetime import date, datetime, timezone

import pytest

from parcha.presentation import (
    delivery_en, kind_en, status_en, format_inr, hindi_delivery, kind_label, latest_log_text, parcha_no, status_label,
)
from parcha.schema import Delivery, TranscriptLog


@pytest.mark.parametrize("paise, text", [
    (0, "₹0"), (65000, "₹650"), (4550, "₹45.50"), (125000, "₹1,250"),
    (12345600, "₹1,23,456"), (10000000, "₹1,00,000"), (10000000000, "₹10,00,00,000"),
    (None, "₹ —"),
])
def test_format_inr_groups_the_indian_way(paise, text):
    assert format_inr(paise) == text


@pytest.mark.parametrize("bad", [True, 450.0, "450"])
def test_format_inr_rejects_non_integer_paise(bad):
    with pytest.raises(TypeError):
        format_inr(bad)


def test_hindi_delivery_names_weekday_date_and_window():
    d = Delivery(date=date(2026, 10, 6), window="evening", spoken="Mangalvaar shaam tak")
    assert hindi_delivery(d) == "मंगलवार, 6 अक्टूबर · शाम"
    assert hindi_delivery(Delivery(date=date(2026, 10, 5), window="morning", spoken="x")) == "सोमवार, 5 अक्टूबर · सुबह"


def test_hindi_delivery_when_missing():
    assert hindi_delivery(None) == "अभी तय नहीं"


def test_kind_and_status_labels_are_hindi():
    assert kind_label("part") == "पार्ट"
    assert kind_label("labour") == "लेबर"
    assert status_label("review") == "जाँच बाकी"
    assert status_label("awaiting_reply") == "ग्राहक का जवाब बाकी"
    assert status_label("fallback_ready") == "बटन से पुष्टि"
    assert status_label("confirmed") == "मंज़ूर"


def test_parcha_no_is_six_digits_and_deterministic():
    assert parcha_no("abc") == parcha_no("abc")
    assert len(parcha_no("abc")) == 6 and parcha_no("abc").isdigit()
    assert parcha_no("abc") != parcha_no("abd")


def test_latest_log_text_picks_the_newest_matching_log():
    when = datetime(2026, 10, 5, tzinfo=timezone.utc)
    logs = (
        TranscriptLog(role="mechanic", mode="verbatim", text="pehla", recorded_at_utc=when),
        TranscriptLog(role="system", mode="timbre_readback", text="aapki gaadi", recorded_at_utc=when),
        TranscriptLog(role="mechanic", mode="reask:items.part-1.amount_paise", text="paanch sau", recorded_at_utc=when),
    )
    assert latest_log_text(logs, role="mechanic") == "paanch sau"
    assert latest_log_text(logs, role="system", mode="timbre_readback") == "aapki gaadi"
    assert latest_log_text(logs, role="customer") is None


def test_english_labels_mirror_the_hindi_ones():
    d = Delivery(date=date(2026, 10, 6), window="evening", spoken="x")
    assert delivery_en(d) == "Tuesday, 6 Oct · evening"
    assert delivery_en(None) == "Not decided yet"
    assert kind_en("part") == "Part" and kind_en("labour") == "Labour"
    assert status_en("confirmed") == "Approved" and status_en("awaiting_reply") == "Waiting for customer"
