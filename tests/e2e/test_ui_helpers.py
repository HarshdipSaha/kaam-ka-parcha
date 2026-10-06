import pytest

pytestmark = pytest.mark.e2e


@pytest.fixture
def ui(page):
    page.goto("/workshop")
    page.wait_for_function("() => window.ParchaUI !== undefined")
    return lambda js, arg=None: page.evaluate(f"(arg) => {{ const UI = window.ParchaUI; return {js}; }}", arg)


@pytest.mark.parametrize("paise, text", [
    (0, "₹0"), (65000, "₹650"), (4550, "₹45.50"), (125000, "₹1,250"),
    (12345600, "₹1,23,456"), (10000000, "₹1,00,000"), (None, "₹ —"),
])
def test_format_rupees_matches_the_server(ui, paise, text):
    assert ui("UI.formatRupees(arg)", paise) == text


def test_hindi_delivery_matches_the_server(ui):
    assert ui('UI.hindiDelivery({date: "2026-10-06", window: "evening", spoken: "x"})') == "मंगलवार, 6 अक्टूबर · शाम"
    assert ui("UI.hindiDelivery(null)") == "अभी तय नहीं"


def test_field_paths_become_plain_questions(ui):
    card = {"items": [{"id": "part-1", "label": "front brake pad", "kind": "part", "amount_paise": None}]}
    assert ui("UI.describeField('items.part-1.amount_paise', arg)", card) == {"hi": "front brake pad का दाम?", "en": "Price of front brake pad?"}
    assert ui("UI.describeField('items.part-1.label', arg)", card) == {"hi": "यह पार्ट क्या है?", "en": "Which part is this?"}
    assert ui("UI.describeField('delivery', arg)", card) == {"hi": "गाड़ी कब मिलेगी?", "en": "When will the vehicle be ready?"}


@pytest.mark.parametrize("session, stage", [
    ({"card": None, "status": "draft"}, "bolo"),
    ({"card": {"items": []}, "status": "review", "review_fields": ["delivery"]}, "parcha"),
    ({"card": {"items": []}, "status": "review", "review_fields": []}, "sunao"),
    ({"card": {"items": []}, "status": "awaiting_reply", "review_fields": []}, "haan"),
    ({"card": {"items": []}, "status": "fallback_ready", "review_fields": []}, "haan"),
    ({"card": {"items": []}, "status": "confirmed", "review_fields": []}, "manzoor"),
])
def test_stage_follows_the_decision_table(ui, session, stage):
    assert ui("UI.stageFor(arg)", session) == stage


def test_diff_reports_changed_amounts_and_labels_only(ui):
    prev = {"items": [{"id": "part-1", "label": "a", "amount_paise": 45000}, {"id": "labour-1", "label": "l", "amount_paise": 20000}]}
    nxt = {"items": [{"id": "part-1", "label": "a", "amount_paise": 50000}, {"id": "labour-1", "label": "l", "amount_paise": 20000}]}
    assert ui("Object.fromEntries(UI.diffItems(arg[0], arg[1]))", [prev, nxt]) == {"part-1": {"amountFrom": 45000}}


def test_el_never_parses_markup(ui):
    assert ui("UI.el('div', {}, '<img src=x>').querySelector('img') === null") is True
    assert ui("UI.el('div', {}, '<b>x</b>').textContent") == "<b>x</b>"


def test_flag_count_is_grammatical(ui):
    assert ui("UI.flagCount(1)") == {"hi": "1 चीज़ जाँचनी है", "en": "1 to check"}
    assert ui("UI.flagCount(3)") == {"hi": "3 चीज़ें जाँचनी हैं", "en": "3 to check"}


def test_repeat_detail_keeps_the_money_path_message(ui):
    assert ui("UI.describeHttpError({repeat: true, reason: 'empty_transcript'}, 422)") == "आवाज़ साफ़ नहीं आई — कृपया फिर से बोलिए (Please say it again)"
    assert ui("new UI.HttpError(422, {repeat: true, reason: 'provider_429'}).reason") == "provider_429"
    assert ui("window.describeHttpError('stale revision', 409)") == "stale revision"


def test_whatsapp_share_message_is_hindi_with_total_and_link(ui):
    text = ui("UI.shareMessage({parcha_no: '004217', total_paise: 65000}, 'http://x/customer/abc')")
    assert text.startswith("नमस्ते!") and "№ 004217" in text and "₹650" in text and text.endswith("http://x/customer/abc")
    assert ui("UI.whatsappHref('हाँ ठीक है')") == "https://wa.me/?text=%E0%A4%B9%E0%A4%BE%E0%A4%81%20%E0%A4%A0%E0%A5%80%E0%A4%95%20%E0%A4%B9%E0%A5%88"
