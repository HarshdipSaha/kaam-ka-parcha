from parcha.lab.language_echo import CONDITIONS, build_cards, readback_text, score, summarize
from parcha.languages import LANGUAGES


def test_cards_are_reproducible_and_valid():
    assert [c.amounts for c in build_cards(10)] == [c.amounts for c in build_cards(10)]
    for card in build_cards(10):
        assert 2 <= len(card.amounts) <= 3 and all(p % 100 == 0 and p > 0 for p in card.amounts)
        assert card.card.delivery is not None


def test_every_language_readback_contains_each_amount_as_digits():
    card = build_cards(1)[0]
    for code in LANGUAGES:
        text = readback_text(card, code)
        for paise in card.amounts:
            assert f"₹{paise // 100}" in text
        assert f"₹{sum(card.amounts) // 100}" in text


def test_score_accepts_digit_forms_commas_and_native_digits():
    card = build_cards(1)[0]
    rupees = sorted(card.expected_numbers)
    transcript = " ".join(f"₹{n:,}" for n in rupees)
    assert score(card, transcript) == {"recovered": True, "missing": [], "phantom": []}
    assert score(card, " ".join(str(n) for n in rupees))["recovered"]
    native = " ".join("".join(chr(ord("௦") + int(d)) for d in str(n)) for n in rupees)   # Tamil digits
    assert score(card, native)["recovered"]


def test_score_reports_missing_amounts_and_phantom_insertions():
    card = build_cards(1)[0]
    rupees = sorted(card.expected_numbers)
    result = score(card, " ".join(str(n) for n in rupees[1:]) + " 8800000")
    assert not result["recovered"] and result["missing"] == [rupees[0]] and result["phantom"] == [8800000]
    boilerplate = f"2023 {card.card.delivery.date.day}/{card.card.delivery.date.month}/{card.card.delivery.date.year} " + " ".join(map(str, rupees))
    assert score(card, boilerplate)["phantom"] == []


def test_summary_ranks_voices_by_their_worst_condition():
    rows = []
    for voice, fails in (("A", 0), ("B", 3)):
        for cond in CONDITIONS:
            for i in range(10):
                rows.append({"language": "ta-IN", "voice": voice, "condition": cond, "recovered": not (cond == CONDITIONS[-1] and i < fails),
                             "phantom": []})
    summary = summarize(rows)
    assert summary["ranking_by_worst_condition"]["ta-IN"][0][0] == "A"
    assert summary["cells"]["ta-IN"]["B"][CONDITIONS[-1]]["recovered"] == 7
    assert summary["cells"]["ta-IN"]["A"]["ALL"]["rate"] == 1.0
