import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import SCREENS, new_parcha

pytestmark = pytest.mark.e2e


def shown(page, parent):
    """Which language is on screen inside this element: 'en' or 'hi'. Exactly one: the other is hidden, not stacked."""
    en = page.locator(f"{parent} > .en").is_visible()
    hi = page.locator(f"{parent} > .hi").is_visible()
    assert en != hi, f"{parent}: exactly one language must be visible (en={en}, hi={hi})"
    return "en" if en else "hi"


def test_english_leads_by_default_and_hindi_is_one_tap_away(page):
    page.goto("/workshop")
    expect(page.locator("html")).to_have_attribute("data-lang", "en")
    assert shown(page, ".brand") == "en"
    assert shown(page, "#stepper li[data-step='bolo']") == "en"
    page.locator("#lang-toggle").click()
    expect(page.locator("html")).to_have_attribute("data-lang", "hi")
    expect(page.locator("html")).to_have_attribute("lang", "hi")
    assert shown(page, ".brand") == "hi"
    page.reload()
    expect(page.locator("html")).to_have_attribute("data-lang", "hi")     # remembered
    page.locator("#lang-toggle").click()
    expect(page.locator("html")).to_have_attribute("data-lang", "en")


def test_only_one_language_is_on_screen_at_a_time(page):
    """The old layout stacked English over Hindi everywhere; a user reads one language."""
    page.goto("/workshop")
    expect(page.locator("#message")).to_be_hidden()  # the empty slip already explains the first action
    for parent in (".empty__title", "#stepper li[data-step='parcha']"):
        assert shown(page, parent) == "en"
    page.locator("#lang-toggle").click()
    for parent in (".empty__title", "#stepper li[data-step='parcha']"):
        assert shown(page, parent) == "hi"


def test_a_real_workshop_page_does_not_call_itself_synthetic(page):
    page.goto("/workshop")
    expect(page.locator(".pill--demo")).to_have_count(0)
    assert "synthetic" not in page.locator("body").inner_text().lower()


def test_the_stage_frames_do_not_repeat_the_header(page):
    """Three titles and three toggles on one screen was the clutter: the frames now defer to the stage header."""
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto("/stage")
    expect(page.locator("#lang-toggle")).to_have_count(1)
    for frame in ("#stage-workshop", "#stage-customer"):
        inner = page.frame_locator(frame)
        expect(inner.locator("html")).to_have_class("embedded")
        expect(inner.locator(".topbar")).to_be_hidden()
        expect(inner.locator("#lang-toggle")).to_be_hidden()


def test_query_param_overrides_the_saved_language(page):
    page.goto("/workshop?lang=hi")
    expect(page.locator("html")).to_have_attribute("data-lang", "hi")


def test_values_follow_the_language_on_the_customer_slip(page, world):
    session = new_parcha(world)
    page.goto(f"/customer/{session['id']}")
    chip = page.locator('[data-item="part-1"] .chip')
    expect(chip).to_have_text("Part", use_inner_text=True)
    expect(page.locator("#delivery-info strong")).to_contain_text("Monday, 5 Oct · evening")
    expect(page.locator("#card-status-badge")).to_have_text("Waiting for customer", use_inner_text=True)
    page.locator("#lang-toggle").click()
    expect(chip).to_have_text("पार्ट", use_inner_text=True)
    expect(page.locator("#delivery-info strong")).to_contain_text("सोमवार, 5 अक्टूबर · शाम")
    page.screenshot(path=str(SCREENS / "customer-hindi-360.png"), full_page=True)


def test_stage_toggle_switches_both_phones(page):
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto("/stage")
    shop = page.frame_locator("#stage-workshop")
    owner = page.frame_locator("#stage-customer")
    expect(shop.locator("html")).to_have_attribute("data-lang", "en")
    page.locator("#lang-toggle").click()
    expect(shop.locator("html")).to_have_attribute("data-lang", "hi")
    expect(owner.locator("html")).to_have_attribute("data-lang", "hi")
