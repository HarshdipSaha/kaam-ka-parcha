import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import speak

pytestmark = pytest.mark.e2e


def test_workshop_dictation_reaches_a_complete_parcha(page):
    page.goto("/workshop")
    speak(page, "#record", "#stop")
    expect(page.locator("#card")).to_contain_text("front brake pad", timeout=15000)
    expect(page.locator("#start-readback")).to_be_enabled()
