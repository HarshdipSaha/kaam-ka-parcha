import pytest

from parcha.money import decide_amounts, normalise_transcribe_fractions


@pytest.mark.parametrize("formatted, expected", [
    ("ऑयल फ़िल्टर साढ़े 30 हज़ार, सर्विस चार्ज 6,000", "ऑयल फ़िल्टर ₹30500, सर्विस चार्ज 6,000"),
    ("बेयरिंग साढ़े 12 हज़ार, फिटिंग", "बेयरिंग ₹12500, फिटिंग"),
    ("साढ़े 23 हज़ार।", "₹23500।"),
    ("साढ़े 4,000 रुपये", "₹4500 रुपये"),
])
def test_a_comma_after_the_unit_word_is_a_separator_not_part_of_the_number(formatted, expected):
    assert normalise_transcribe_fractions(formatted) == expected


def test_a_digit_group_is_still_not_split():
    text = "साढ़े 4 हज़ार,500"               # a digit group after the unit: leave it for the parser to disagree with
    assert normalise_transcribe_fractions(text) == text


def test_comma_separated_estimate_with_fractions_settles_each_amount():
    verbatim = ("क्लच प्लेट चौबीस सौ, ब्रेक पैड साढ़े चार हज़ार रुपये, ऑयल फ़िल्टर साढ़े तीस हज़ार, "
                "सर्विस चार्ज साढ़े पंद्रह हज़ार रुपये।")
    transcribe = "क्लच प्लेट 24 सौ, ब्रेक पैड साढ़े 4,000 रुपये, ऑयल फ़िल्टर साढ़े 30 हज़ार, सर्विस चार्ज साढ़े 15,000 रुपये।"
    decisions = decide_amounts(verbatim, transcribe, expected_count=4)
    assert [(d.paise, d.reason) for d in decisions] == [(240000, None), (450000, None), (3050000, None), (1550000, None)]


@pytest.mark.parametrize("formatted, expected", [
    ("सर्विस चार्ज 4,900 पचास।", "सर्विस चार्ज ₹4950।"),
    ("प्लग 4,100 पचास, फिटिंग", "प्लग ₹4150, फिटिंग"),
    ("₹4,900 पचास रुपये", "₹4950 रुपये"),
    ("1,600 पचास", "₹1650"),
    ("49 पचास", "49 पचास"),                   # not a multiple of 100: leave it for the parser to disagree with
    ("तीन पचास", "तीन पचास"),
])
def test_prisma_leaves_the_word_for_fifty_unformatted_after_hundreds(formatted, expected):
    assert normalise_transcribe_fractions(formatted) == expected


def test_a_trailing_fifty_never_hides_a_real_disagreement():
    [decision] = decide_amounts("एक हज़ार छह सौ पचास", "1,600 पचास", expected_count=1)
    assert decision.paise == 165000
    [decision] = decide_amounts("एक हज़ार छह सौ", "1,600 पचास", expected_count=1)      # speech says 1,600, formatting says 1,650
    assert decision.paise is None and decision.reason == "crosscheck_disagreement"
