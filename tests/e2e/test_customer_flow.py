import re

import httpx
import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import SCREENS, new_parcha, speak

pytestmark = pytest.mark.e2e


def open_customer(page, world, *, consent=True, read_back=True):
    session = new_parcha(world.url, read_back=read_back)
    page.goto(f"/customer/{session['id']}")
    if consent:
        page.locator("#dpdp-consent-checkbox").check()
        expect(page.locator("#customer-record")).to_be_enabled()
    return session


def answer(page, world, words):
    world.prisma.say(words)
    speak(page, "#customer-record", "#customer-stop")


def test_customer_page_opens_like_a_call_with_the_slip(page, world):
    open_customer(page, world, consent=False)
    expect(page.locator("#disclosure")).to_contain_text("यह नकली फ़ोन लाइन है")
    expect(page.locator("#disclosure")).to_contain_text("No call was placed.")
    expect(page.locator("#audio-panel")).to_contain_text("गैराज से कॉल")
    expect(page.locator("#readback-caption")).not_to_be_empty()
    expect(page.locator("#total-cell")).to_have_text("₹650")
    expect(page.locator("#dpdp-consent-checkbox")).not_to_be_checked()
    expect(page.locator("#customer-record")).to_be_disabled()
    expect(page.locator("#play-readback")).to_be_enabled(timeout=10000)
    page.screenshot(path=str(SCREENS / "customer-call-360.png"), full_page=True)


def test_consent_gates_the_reply_mic_and_is_recorded(page, world):
    session = open_customer(page, world, consent=False)
    page.locator("#dpdp-consent-checkbox").check()
    expect(page.locator("#customer-record")).to_be_enabled()
    expect(page.locator("#toast")).to_contain_text("सहमति दर्ज हुई")
    assert httpx.get(f"{world.url}/sessions/{session['id']}").json()["dpdp_consent_granted"] is True
    page.locator("#dpdp-consent-checkbox").uncheck()
    expect(page.locator("#customer-record")).to_be_disabled()


def test_haan_seals_with_a_upi_style_receipt_and_stamp(page, world):
    open_customer(page, world)
    answer(page, world, "हाँ ठीक है")
    receipt = page.locator("#confirmed-banner")
    expect(receipt).to_be_visible(timeout=15000)
    expect(receipt).to_contain_text("पर्चा मंज़ूर हुआ")
    expect(page.locator("#receipt-total")).to_have_text("₹650")
    expect(page.locator("#receipt-said")).to_contain_text("हाँ ठीक है")
    expect(page.get_by_role("img", name="मंज़ूर — Approved")).to_be_visible()
    expect(page.locator("#dock")).to_be_hidden()
    expect(page.locator("#verify-link")).to_have_attribute("href", re.compile(r"^/verify/"))
    page.locator("#whatsapp-copy").click()
    expect(page.locator("#toast")).to_contain_text("कॉपी हुआ")
    assert "650" in page.evaluate("navigator.clipboard.readText()")
    page.screenshot(path=str(SCREENS / "customer-sealed-360.png"), full_page=True)


def test_correction_shows_the_old_amount_struck_and_a_fresh_call(page, world):
    open_customer(page, world)
    answer(page, world, "nahi front brake pad 500")
    row = page.locator('[data-item="part-1"]')
    expect(row.locator("s")).to_have_text("₹450", timeout=15000)
    expect(row).to_contain_text("₹500")
    expect(page.locator("#total-cell")).to_have_text("₹700")
    expect(page.locator("#readback-player")).to_have_attribute("src", re.compile(r"revision=2"))
    expect(page.locator("#customer-status")).to_contain_text("नया पर्चा")
    page.screenshot(path=str(SCREENS / "customer-correction-360.png"), full_page=True)


def test_three_unclear_replies_offer_tap_fallback(page, world):
    open_customer(page, world)
    for _ in range(2):
        answer(page, world, "kya bola aapne")
        expect(page.locator("#customer-status")).to_contain_text("समझ नहीं आया", timeout=15000)
        expect(page.locator("#customer-record")).to_be_enabled()
    answer(page, world, "kya bola aapne")
    expect(page.locator("#fallback-banner")).to_be_visible(timeout=15000)
    page.locator("#fallback-approve").click()
    expect(page.locator("#confirmed-banner")).to_be_visible()
    expect(page.locator("#receipt-how")).to_contain_text("बटन से मंज़ूर")


def test_audio_failure_keeps_reply_available(page, world):
    page.route("**/readback.wav*", lambda route: route.fulfill(status=404, body="missing"))
    open_customer(page, world)
    expect(page.locator("#call-status")).to_contain_text("आवाज़ नहीं चली", timeout=10000)
    expect(page.locator("#readback-caption")).not_to_be_empty()
    expect(page.locator("#customer-record")).to_be_enabled()


def test_stale_reply_offers_reload(page, world):
    page.route("**/sessions/*/reply", lambda route: route.fulfill(
        status=409, content_type="application/json", body='{"detail": "stale revision"}'))
    open_customer(page, world)
    answer(page, world, "हाँ ठीक है")
    expect(page.locator("#customer-message")).to_contain_text("पर्चा बदल गया है", timeout=15000)
    expect(page.get_by_role("button", name=re.compile("ताज़ा करें"))).to_be_visible()


def test_page_waits_for_the_read_back_then_updates_itself(page, world):
    session = open_customer(page, world, consent=False, read_back=False)
    expect(page.locator("#customer-status")).to_contain_text("गैराज पर्चा तैयार कर रहा है")
    httpx.post(f"{world.url}/sessions/{session['id']}/readback",
               data={"expected_revision": session["revision"]}).raise_for_status()
    expect(page.locator("#readback-caption")).not_to_be_empty(timeout=10000)
    expect(page.locator("#readback-player")).to_have_attribute("src", re.compile(r"readback\.wav\?revision=\d+"))
