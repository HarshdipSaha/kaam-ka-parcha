import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import confirm_amounts_in_ui, speak

pytestmark = pytest.mark.e2e


def test_workshop_dictation_reaches_a_complete_parcha(page, world):
    page.goto("/workshop")
    speak(page, "#record", "#stop")
    expect(page.locator("#card")).to_contain_text("front brake pad", timeout=15000)
    confirm_amounts_in_ui(page, world)
    expect(page.locator("#start-readback")).to_be_enabled()
