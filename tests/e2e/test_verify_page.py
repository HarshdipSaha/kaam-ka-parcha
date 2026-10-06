import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import SCREENS, new_parcha, reply_by_api

pytestmark = pytest.mark.e2e


def test_verify_shows_a_big_verdict_and_folds_the_hashes(page, world):
    session = new_parcha(world.url)
    world.prisma.say("हाँ ठीक है")
    reply_by_api(world.url, session)
    page.goto(f"/verify/{session['id']}")
    expect(page.get_by_role("heading", name="असली पर्चा")).to_be_visible()
    expect(page.locator("#manifest-digest")).to_be_hidden()          # folded under "तकनीकी सबूत"
    page.get_by_text("तकनीकी सबूत").click()
    expect(page.locator("#manifest-digest")).to_be_visible()
    expect(page.get_by_role("img", name="मंज़ूर — Approved")).to_be_visible()
    page.screenshot(path=str(SCREENS / "verify-360.png"), full_page=True)
