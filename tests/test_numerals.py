import pytest
from parcha.numerals import parse_amounts, render_colloquial_amount, render_hindi_amount


def values(text):
    return [(m.status, m.paise) for m in parse_amounts(text)]


@pytest.mark.parametrize("text,expected", [
    ("front brake pad saade chaar sau", [("complete", 45000)]),
    ("फ्रंट ब्रेक पैड साढ़े चार सौ लेबर दो सौ मंगलवार शाम तक", [("complete", 45000), ("complete", 20000)]),
    ("front brake pad ₹450, labour ₹200, Somvaar shaam tak", [("complete", 45000), ("complete", 20000)]),
    ("फ्रंट ब्रेक पैड 04:30 100 लेबर 200 मंगलवार शाम तक", [("complete", 10000), ("complete", 20000)]),  # effort 005
    ("clutch plate dedh hazaar", [("complete", 150000)]),
    ("ढाई सौ रुपये", [("complete", 25000)]),
    ("sava sau", [("complete", 12500)]),
    ("sava do sau", [("complete", 22500)]),
    ("paune do hazaar", [("complete", 175000)]),
    ("पौने सौ", [("complete", 7500)]),
    ("do hazaar pachaas", [("complete", 205000)]),
    ("baarah sau", [("complete", 120000)]),
    ("एक लाख", [("complete", 10000000)]),
    ("ek hazaar do sau", [("complete", 120000)]),
    ("labour pachaas", [("complete", 5000)]),
    ("1,200 rupaye", [("complete", 120000)]),
    ("४५० रुपये", [("complete", 45000)]),
    ("₹ 1,500.50", [("complete", 150050)]),
    ("2 हजार", [("complete", 200000)]),
])
def test_complete_amounts(text, expected):
    assert values(text) == expected


@pytest.mark.parametrize("text", ["brake pad saade", "brake pad saade chaar", "dedh", "sava"])
def test_incomplete_amounts(text):
    assert values(text) == [("incomplete", None)]


@pytest.mark.parametrize("text", [
    "एक रिसर्च में", "do din mein gaadi milegi", "chaar baje aana", "bees minute lagenge",
    "DL 3S AB 1234", "10:30 pe aana",
])
def test_distractors_are_not_money(text):
    assert values(text) == []


@pytest.mark.parametrize("text,expected", [   # real Gramvaani reference phrasing (rows 95, 106, 746, 17)
    ("दस हजार बीस हजार पच्चीस हजार तीस हजार", [("complete", 1000000), ("complete", 2000000),
                                              ("complete", 2500000), ("complete", 3000000)]),
    ("निर्धारित दूरी साढ़े पांच किलोमीटर रखा गया", []),
    ("पौने दो साल पहले इस केंद्र का उद्घाटन", []),
    ("हमारी छब्बीस जनवरी मनाते", []),
    ("लगभग ढाई सौ से अधिक बाल", [("complete", 25000)]),
])
def test_real_phone_speech_number_lists_dates_and_distances(text, expected):
    assert values(text) == expected


def test_vehicle_number_does_not_hide_a_following_amount():
    assert values("DL 3S AB 1234 brake pad saade chaar sau") == [("complete", 45000)]


@pytest.mark.parametrize("rupees", list(range(1, 100)) + [100, 125, 450, 999, 1000, 1050, 1200, 1500, 2050,
                                                          9999, 10000, 45000, 99999, 100000])
def test_render_then_parse_round_trips(rupees):
    assert values(render_hindi_amount(rupees * 100)) == [("complete", rupees * 100)]


def test_render_rejects_non_whole_rupees_and_out_of_range():
    for bad in (0, 150, 10_000_100):
        with pytest.raises(ValueError):
            render_hindi_amount(bad)


@pytest.mark.parametrize("paise,expected", [
    (150_000, "डेढ़ हज़ार"),
    (25_000, "ढाई सौ"),
    (45_000, "साढ़े चार सौ"),
    (12_500, "सवा सौ"),
    (175_000, "पौने दो हज़ार"),
    (120_000, "बारह सौ"),
])
def test_render_colloquial_special_forms_round_trip(paise, expected):
    rendered = render_colloquial_amount(paise)
    assert rendered == expected
    assert values(rendered) == [("complete", paise)]


def test_render_colloquial_fallback_round_trips():
    paise = 12_300
    assert values(render_colloquial_amount(paise)) == [("complete", paise)]


@pytest.mark.parametrize("paise", [0, 150, 10_000_100])
def test_render_colloquial_rejects_non_whole_rupees_and_out_of_range(paise):
    with pytest.raises(ValueError):
        render_colloquial_amount(paise)


@pytest.mark.parametrize("text,expected", [
    ("saade sau", [("complete", 15_000)]),
    ("saade hazaar", [("complete", 150_000)]),
])
def test_half_fraction_can_precede_a_multiplier(text, expected):
    assert values(text) == expected


@pytest.mark.parametrize("text", ["model 2020", "26 जनवरी 2020", "May 2020"])
def test_model_years_and_date_years_are_not_money(text):
    assert values(text) == []


def test_explicit_currency_keeps_a_year_like_number_as_money():
    assert values("₹2020") == [("complete", 202_000)]


@pytest.mark.parametrize("registration", ["DL-3S-AB-1234", "MH-12-AB-1234"])
def test_hyphenated_vehicle_registrations_are_not_money(registration):
    assert values(registration) == []


@pytest.mark.parametrize("registration", ["DL-3S-AB-1234", "MH-12-AB-1234"])
def test_hyphenated_vehicle_registration_does_not_hide_following_amount(registration):
    assert values(f"{registration} brake pad saade chaar sau") == [("complete", 45_000)]


def test_uncued_year_like_number_remains_a_bare_amount():
    assert values("2020") == [("complete", 202_000)]


@pytest.mark.parametrize("text", ["model year 2020", "2020 model", "model do hazaar bees"])
def test_model_year_order_and_spelled_year_are_not_money(text):
    assert values(text) == []


@pytest.mark.parametrize("text", ["26/01/2020", "2020-01-26"])
def test_numeric_date_formats_are_not_money(text):
    assert values(text) == []
