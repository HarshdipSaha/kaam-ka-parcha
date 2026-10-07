from collections import defaultdict

import pytest

from parcha.money import decide_amounts
from parcha.numerals import _DEVA_1_99, _key, _spelling_variants, parse_amounts


@pytest.mark.parametrize("spoken, rupees", [
    ("उन्तीस सौ", 2900), ("उन्तीस हज़ार", 29000),          # Prisma's spelling of उनतीस, seen in live estimates
    ("तेंतीस हज़ार", 33000), ("तेतीस हज़ार", 33000),        # तैंतीस
    ("उन्चास हज़ार", 49000),                                # उनचास
    ("अट्ठारह सौ", 1800), ("अठ्ठाराह सौ", 1800),            # अठारह
    ("चौतीस सौ", 3400), ("साढ़े तेतीस हज़ार", 33500),       # चौंतीस; a fraction on top of a variant
])
def test_prisma_spelling_variants_are_valued_not_dropped(spoken, rupees):
    [mention] = parse_amounts(spoken)
    assert (mention.status, mention.paise) == ("complete", rupees * 100)


def test_a_variant_spelling_is_never_read_as_a_bare_unit():
    """The failure that settled ₹100 for ₹2,900: the unknown word was skipped and 'सौ' alone became ₹100."""
    [mention] = parse_amounts("ऑयल फ़िल्टर उन्तीस सौ रुपये")
    assert mention.paise == 290000
    [decision] = decide_amounts("ऑयल फ़िल्टर उन्तीस सौ रुपये", "ऑयल फ़िल्टर उन्तीस ₹100 रुपये", expected_count=1)
    assert decision.paise != 10000                      # either abstains on the disagreement or reads ₹2,900, never ₹100


def test_variant_rules_never_make_two_numbers_share_a_spelling():
    owners = defaultdict(set)
    for number, word in enumerate(_DEVA_1_99, 1):
        owners[_key(word)].add(number)
        for variant in _spelling_variants(word):
            owners[_key(variant)].add(number)
    assert {key: nums for key, nums in owners.items() if len(nums) > 1} == {}


def test_standard_spellings_keep_their_values():
    for number, word in enumerate(_DEVA_1_99, 1):
        [mention] = parse_amounts(f"{word} सौ") if number < 100 else []
        assert mention.paise == number * 100 * 100
