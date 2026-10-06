import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import SCREENS, speak

pytestmark = pytest.mark.e2e


def test_stage_runs_the_whole_loop_on_one_screen(page, world):
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto("/stage")
    shop = page.frame_locator("#stage-workshop")
    owner = page.frame_locator("#stage-customer")
    speak(shop, "#record", "#stop")
    expect(shop.locator("#total-cell")).to_have_text("₹650", timeout=15000)
    shop.locator("#start-readback").click()
    expect(owner.locator("#readback-caption")).not_to_be_empty(timeout=10000)
    owner.locator("#dpdp-consent-checkbox").check()
    world.prisma.say("हाँ ठीक है")
    speak(owner, "#customer-record", "#customer-stop")
    expect(owner.locator("#confirmed-banner")).to_be_visible(timeout=15000)
    expect(shop.get_by_role("img", name="मंज़ूर — Approved")).to_be_visible(timeout=10000)
    page.screenshot(path=str(SCREENS / "stage-sealed-1440.png"), full_page=True)
