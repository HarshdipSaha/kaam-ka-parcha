import re
import time
from urllib.parse import unquote

import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import SCREENS, confirm_amounts_in_ui, reply_by_api, speak

pytestmark = pytest.mark.e2e
INTAKE_T = "front brake pad ₹450, labour ₹200, Somvaar shaam tak"
INCOMPLETE_V = "front brake pad saade labour do sau Somvaar shaam tak"


def dictate(page):
    page.goto("/workshop")
    speak(page, "#record", "#stop")
    expect(page.locator("#slip")).to_be_visible(timeout=15000)


def test_dictation_builds_a_hindi_first_parcha(page, world):
    dictate(page)
    slip = page.locator("#slip")
    for text in ("front brake pad", "पार्ट", "लेबर"):
        expect(slip).to_contain_text(text)
    expect(page.locator("#transcript")).to_contain_text("आपने कहा")
    expect(page.locator("#transcript-content")).to_contain_text("front brake pad")
    expect(page.locator("#total-cell")).to_have_text("Incomplete", use_inner_text=True)
    expect(page.locator("#start-readback")).to_be_hidden()
    confirm_amounts_in_ui(page, world)
    for text in ("₹450", "₹200"):
        expect(slip).to_contain_text(text)
    expect(page.locator("#total-cell")).to_have_text("₹650")
    expect(page.locator("#delivery-info")).to_contain_text("सोमवार, 5 अक्टूबर · शाम")
    expect(page.locator("#parcha-no")).to_have_text(re.compile(r"^\d{6}$"))
    expect(page.locator('#stepper [aria-current="step"]')).to_contain_text("सुनाओ")
    expect(page.locator("#start-readback")).to_be_enabled()
    expect(page.locator("body")).not_to_contain_text("items.part-1")
    expect(page.locator("body")).not_to_contain_text("part-1")
    page.screenshot(path=str(SCREENS / "workshop-slip-360.png"), full_page=True)


def test_listening_swaps_the_mic_for_a_stop_button_in_the_same_place(page):
    page.goto("/workshop")
    mic_box = page.locator("#record").bounding_box()
    assert mic_box["width"] >= 88 and mic_box["height"] >= 88
    page.locator("#record").click()
    stop = page.locator("#stop")
    expect(stop).to_be_visible()
    expect(page.locator("#record")).to_be_hidden()
    expect(page.locator("#dock")).to_have_attribute("data-mic", "listening")
    expect(page.locator("[data-mic-timer]")).to_have_text(re.compile(r"^\d:\d\d$"))
    stop_box = stop.bounding_box()
    assert abs(stop_box["x"] - mic_box["x"]) < 4 and abs(stop_box["y"] - mic_box["y"]) < 4
    time.sleep(0.8)   # let the fake microphone record something
    stop.click()
    expect(page.locator("#slip")).to_be_visible(timeout=15000)
    expect(page.locator("#dock")).to_have_attribute("data-mic", "idle")


def test_flagged_amount_is_asked_on_its_row_and_fixed_by_voice(page, world):
    world.prisma.script_intake(transcribe=INTAKE_T, verbatim=INCOMPLETE_V)
    dictate(page)
    row = page.locator('[data-item="part-1"]')
    expect(row).to_contain_text("front brake pad का दाम?")
    expect(row).to_contain_text("अधूरी रकम — फिर से पूछेंगे")          # money-path abstain label
    expect(page.locator("#review-count")).to_contain_text("2 चीज़ें जाँचनी हैं")
    expect(page.locator("#total-cell")).to_have_text("Incomplete", use_inner_text=True)
    expect(page.locator("#start-readback")).to_be_hidden()
    page.screenshot(path=str(SCREENS / "workshop-flagged-360.png"), full_page=True)
    world.prisma.say("paanch sau")
    again = row.get_by_role("button", name=re.compile("दोबारा बोलें"))
    speak(page, again, "#stop")
    # No earlier candidate for this amount: the first recording is only a candidate, shown as what was heard.
    expect(row).to_contain_text("पक्की करें", timeout=15000)
    expect(row.locator(".row__heard")).to_contain_text("paanch sau")
    speak(page, again, "#stop")      # a second agreeing recording settles it
    expect(page.locator('[data-item="part-1"] .row__amount')).to_have_text("₹500", timeout=15000)
    # the single recording of labour still needs its deliberate second recording
    world.prisma.say("do sau")
    speak(page, page.locator('[data-item="labour-1"]').get_by_role("button", name=re.compile("दोबारा बोलें")), "#stop")
    expect(page.locator('[data-item="labour-1"] .row__amount')).to_have_text("₹200", timeout=15000)
    expect(page.locator("#total-cell")).to_have_text("₹700")
    expect(page.locator("#review-section")).to_be_hidden()
    expect(page.locator("#start-readback")).to_be_enabled()


def test_repeat_request_is_a_friendly_state(page, world):
    world.prisma.script_intake(transcribe="", verbatim="")
    page.goto("/workshop")
    speak(page, "#record", "#stop")
    expect(page.locator("#message")).to_contain_text("कृपया फिर से बोलिए", timeout=15000)
    expect(page.locator("#message")).not_to_contain_text("HTTP")
    expect(page.locator("#record")).to_be_visible()
    expect(page.locator("#record")).to_be_enabled()


def test_mic_blocked_shows_hindi_guidance(page):
    page.add_init_script(
        'navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException("blocked", "NotAllowedError"));'
    )
    page.goto("/workshop")
    page.locator("#record").click()
    expect(page.locator("#message")).to_contain_text("माइक की इजाज़त दें")
    expect(page.locator("#record")).to_be_enabled()
    expect(page.locator("#stop")).to_be_hidden()


def test_hostile_label_renders_as_text(page, world):
    world.extractor.mode = "hostile_label"
    dictate(page)
    expect(page.locator("#card img")).to_have_count(0)
    expect(page.locator("#card")).to_contain_text('<img src=x onerror="window.__xss=1">')
    assert page.evaluate("window.__xss") is None


def test_read_back_opens_a_share_sheet_with_copy_and_whatsapp(page, world):
    dictate(page)
    confirm_amounts_in_ui(page, world)
    page.locator("#start-readback").click()
    share = page.locator("#share")
    expect(share).to_be_visible(timeout=15000)
    expect(page.locator('#stepper [aria-current="step"]')).to_contain_text("हाँ")
    session = page.evaluate("window.getCurrentSession()")
    customer_url = f"{page.url.split('/workshop')[0]}/customer/{session['id']}"
    expect(page.locator("#customer-link")).to_have_attribute("href", f"/customer/{session['id']}")
    page.locator("#copy-link").click()
    expect(page.locator("#toast")).to_contain_text("कॉपी हुआ")
    assert page.evaluate("navigator.clipboard.readText()") == customer_url
    wa = unquote(page.locator("#whatsapp-open").get_attribute("href"))
    assert wa.startswith("https://wa.me/?text=नमस्ते!") and "₹650" in wa and wa.endswith(customer_url)
    expect(share).to_contain_text("अपने आप कुछ नहीं भेजा जाता")
    page.screenshot(path=str(SCREENS / "workshop-share-360.png"), full_page=True)


def test_customer_approval_stamps_the_mechanics_slip(page, world):
    dictate(page)
    confirm_amounts_in_ui(page, world)
    page.locator("#start-readback").click()
    expect(page.locator("#share")).to_be_visible(timeout=15000)
    world.prisma.say("हाँ ठीक है")
    reply_by_api(world.url, page.evaluate("window.getCurrentSession()"))
    expect(page.get_by_role("img", name="मंज़ूर — Approved")).to_be_visible(timeout=10000)
    expect(page.locator("#message")).to_contain_text("ग्राहक ने मंज़ूर किया")
    expect(page.locator('#stepper li[data-step="manzoor"]')).to_have_attribute("data-state", "done")
    page.screenshot(path=str(SCREENS / "workshop-sealed-360.png"), full_page=True)


def test_live_captions_appear_while_speaking_and_never_become_amounts(page, world):
    world.prisma.script_intake(transcribe=INTAKE_T, verbatim=INCOMPLETE_V)
    page.goto("/workshop")
    speak(page, "#record", "#stop", seconds=1.5)
    expect(page.locator("#slip")).to_be_visible(timeout=15000)
    expect(page.locator("#captions")).to_be_visible(timeout=10000)
    expect(page.locator("#captions-text")).to_contain_text("front brake pad paanch sau")
    # the caption said "paanch sau" but amounts come only from the finished recording's two REST passes
    expect(page.locator('[data-item="part-1"] .row__amount')).not_to_contain_text("₹500")
    expect(page.locator("#total-cell")).to_have_text("Incomplete", use_inner_text=True)
