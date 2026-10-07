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
