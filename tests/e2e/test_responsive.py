import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import SCREENS, new_parcha, reply_by_api, speak

pytestmark = pytest.mark.e2e
VIEWPORTS = [(360, 800), (390, 844), (768, 1024), (1440, 900)]
INTAKE_T = "front brake pad ₹450, labour ₹200, Somvaar shaam tak"
INCOMPLETE_V = "front brake pad saade labour do sau Somvaar shaam tak"
OVERFLOW = "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
TARGETS = """() => [...document.querySelectorAll('button, a.btn, summary, input[type=checkbox]')]
  .filter((n) => n.getClientRects().length && !n.closest('[hidden]'))
  .map((n) => { const r = (n.type === 'checkbox' ? n.closest('label') : n).getBoundingClientRect();
                return { name: n.id || n.getAttribute('aria-label') || n.textContent.trim().slice(0, 24),
                         w: r.width, h: r.height, mic: n.classList.contains('mic') }; })"""
FONT = "() => parseFloat(getComputedStyle(document.body).fontSize)"
UNNAMED = """() => [...document.querySelectorAll('button')].filter((b) => b.getClientRects().length)
  .filter((b) => !(b.getAttribute('aria-label') || b.textContent.trim())).map((b) => b.outerHTML.slice(0, 80))"""


def audit(page, label, width):
    assert page.evaluate(OVERFLOW) <= 1, f"{label}@{width}: horizontal overflow"
    for target in page.evaluate(TARGETS):
        assert target["w"] >= 48 and target["h"] >= 48, f"{label}@{width}: small target {target}"
        if target["mic"]:
            assert target["w"] >= 88 and target["h"] >= 88, f"{label}@{width}: mic too small {target}"
    assert page.evaluate(FONT) >= 16
    assert page.evaluate(UNNAMED) == [], f"{label}@{width}: unlabeled buttons"
    page.screenshot(path=str(SCREENS / f"{label}-{width}.png"), full_page=True)


@pytest.mark.parametrize("width, height", VIEWPORTS, ids=[f"{w}x{h}" for w, h in VIEWPORTS])
def test_layout_fits_and_targets_are_thumb_sized(page, world, width, height):
    page.set_viewport_size({"width": width, "height": height})
    page.goto("/workshop")
    audit(page, "workshop-empty", width)

    world.extractor.mode = "long_label"
    world.prisma.script_intake(transcribe=INTAKE_T, verbatim=INCOMPLETE_V)
    speak(page, "#record", "#stop")
    expect(page.locator("#slip")).to_be_visible(timeout=15000)
    audit(page, "workshop-long-flagged", width)

    world.prisma.reset()
    world.extractor.mode = "complete"
    session = new_parcha(world)
    page.goto(f"/customer/{session['id']}")
    audit(page, "customer-call", width)

    world.prisma.say("हाँ ठीक है")
    reply_by_api(world.url, session)
    page.goto(f"/customer/{session['id']}")
    audit(page, "customer-sealed", width)
    page.goto(f"/verify/{session['id']}")
    audit(page, "verify", width)


def test_reduced_motion_turns_animation_off(page, world):
    page.emulate_media(reduced_motion="reduce")
    session = new_parcha(world)
    world.prisma.say("हाँ ठीक है")
    reply_by_api(world.url, session)
    page.goto(f"/customer/{session['id']}")
    duration = page.get_by_role("img", name="मंज़ूर — Approved").evaluate(
        "(n) => parseFloat(getComputedStyle(n).animationDuration)")
    assert duration < 0.01
