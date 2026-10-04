import pytest

from parcha.lab.metrics import (
    amount_match,
    cer,
    hallucinated_words,
    normalize,
    short_reply_drop,
)


def test_cer_and_empty_reference():
    # Empty reference cases
    assert cer("", "") == 0.0
    assert cer("", "something") == 1.0
    assert cer("something", "") == 1.0

    # Exact match
    assert cer("brake pad", "brake pad") == 0.0
    assert cer("Brake   Pad", "brake pad") == 0.0

    # Normalization check
    assert normalize("  हूँ \t \n KHATARA ") == "हूँ khatara"

    # Known edits
    # ref="brake" (len 5), hyp="brak" (delete 1) -> 1/5 = 0.2
    assert cer("brake", "brak") == pytest.approx(0.2)
    # ref="brake" (len 5), hyp="break" (sub 'a'->'e', sub 'k'->'a', ins 'k', etc -> distance 2) -> 2/5 = 0.4
    assert cer("brake", "break") == pytest.approx(0.4)

    # Unicode Devanagari consistency
    assert cer("हाँ ठीक है", "हाँ ठीक है") == 0.0
    assert cer("हाँ ठीक है", "हाँ") == pytest.approx(7 / 10)  # len("हाँ ठीक है") == 10, hyp="हाँ" (len 3), deletes 7


def test_amount_match_uses_rupees_not_string_format():
    # expected_paise is 45000 (i.e. 450 rupees)
    # Hypothesis is in rupees ("₹450" or "450 rupaye")
    # A naive check like `str(expected_paise) in hyp` would look for "45000" and fail!
    expected_paise = 45000

    assert amount_match(expected_paise, "brake ka part ₹450, Somvaar shaam tak") is True
    assert amount_match(expected_paise, "brake ka part 450 rupaye, Somvaar shaam tak") is True
    assert amount_match(expected_paise, "brake ka part ₹450.00") is True

    # Hypothesis has "45000" (45000 rupees = 4,500,000 paise), which does NOT match 45000 paise (450 rupees)
    assert amount_match(expected_paise, "brake ka part ₹45000") is False

    # Different amount
    assert amount_match(expected_paise, "brake ka part ₹500") is False

    # 1000 rupees = 100000 paise
    assert amount_match(100000, "clutch ka part ₹1000") is True
    assert amount_match(100000, "clutch ka part 1000 rupaye") is True


def test_amount_match_with_commas_and_decimals():
    # Indian / international comma separation
    assert amount_match(100000, "part ₹1,000, Somvaar tak") is True
    assert amount_match(120000, "₹ 1,200") is True
    assert amount_match(10000000, "ek part ₹1,00,000") is True  # 1 lakh = 100,000 rupees = 10,000,000 paise
    assert amount_match(10000000, "₹10,000,000") is False  # 1 crore rupees != 100,000 rupees

    # Decimals
    assert amount_match(100000, "₹1,000.00") is True
    assert amount_match(45000, "₹450.0") is True
    assert amount_match(45050, "₹450.50") is True
    assert amount_match(125075, "1,250.75 rupaye") is True

    # Currency prefixes / suffixes
    assert amount_match(50000, "Rs. 500") is True
    assert amount_match(50000, "500 rs") is True
    assert amount_match(50000, "INR 500") is True
    assert amount_match(50000, "500/-") is True

    # Words fallback
    assert amount_match(45000, "saade chaar sau rupaye") is True
    assert amount_match(45000, "चार सौ पचास रुपये") is True

    # Empty / none cases
    assert amount_match(45000, "") is False
    assert amount_match(45000, "kuch bhi bina number ke") is False


def test_reply_and_non_speech_metrics():
    # short_reply_drop on empty hypothesis
    assert short_reply_drop("accept", "") is True
    assert short_reply_drop("haan", "   ") is True
    assert short_reply_drop("nahi", "") is True

    # Acceptance expectations
    assert short_reply_drop("accept", "haan") is False
    assert short_reply_drop("accept", "हाँ ठीक है") is False
    assert short_reply_drop("haan", "haan theek hai") is False
    assert short_reply_drop("haan", "nahi") is True
    assert short_reply_drop("accept", "kuch aur hi bola") is True

    # Rejection / correction expectations
    assert short_reply_drop("reject", "nahi") is False
    assert short_reply_drop("nahi", "nahi Somvaar") is False  # correction
    assert short_reply_drop("correction", "nahi Mangalvaar") is False
    assert short_reply_drop("nahi", "haan") is True
    assert short_reply_drop("reject", "theek hai") is True

    # hallucinated_words on speech / non-speech
    assert hallucinated_words("") == 0
    assert hallucinated_words("   \t \n ") == 0
    assert hallucinated_words("brake") == 1
    assert hallucinated_words("brake ka part ₹450") == 4
    assert hallucinated_words("ek do teen char paanch") == 5
