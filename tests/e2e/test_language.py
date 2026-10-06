import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import SCREENS, new_parcha

pytestmark = pytest.mark.e2e


def leads(page, parent):
    """Which language sits on top inside this element: 'en' or 'hi' (CSS order is not DOM order)."""
    top = lambda cls: page.locator(f"{parent} > .{cls}").bounding_box()["y"]
    return "en" if top("en") < top("hi") else "hi"


def test_english_leads_by_default_and_hindi_is_one_tap_away(page):
    page.goto("/workshop")
    expect(page.locator("html")).to_have_attribute("data-lang", "en")
    assert leads(page, ".brand") == "en"
    assert leads(page, "#stepper li[data-step='bolo']") == "en"
    page.locator("#lang-toggle").click()
    expect(page.locator("html")).to_have_attribute("data-lang", "hi")
    expect(page.locator("html")).to_have_attribute("lang", "hi")
    assert leads(page, ".brand") == "hi"
    page.reload()
    expect(page.locator("html")).to_have_attribute("data-lang", "hi")     # remembered
    page.locator("#lang-toggle").click()
    expect(page.locator("html")).to_have_attribute("data-lang", "en")


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
