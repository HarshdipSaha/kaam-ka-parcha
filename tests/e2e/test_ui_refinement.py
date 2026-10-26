"""Concise UI states and recoverable connection failures, using offline services."""
import re

import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import speak

pytestmark = pytest.mark.e2e


def test_correction_label_follows_language_and_marks_active_row(page, world):
    page.goto("/workshop")
    speak(page, "#record", "#stop")
    row = page.locator('[data-item="part-1"]')
    again = row.locator(".reask")
    expect(again).to_have_text("Say again", use_inner_text=True)
    page.locator("#lang-toggle").click()
    expect(again).to_have_text("दोबारा बोलें", use_inner_text=True)
    again.click()
    expect(row).to_have_class(re.compile(r"row--active"))
    expect(page.locator("#confirm-estimate")).to_be_disabled()
    expect(page.locator("#message")).to_contain_text("front brake pad")
    page.locator("#stop").click()
    expect(page.locator(".row--active")).to_have_count(0, timeout=15000)


@pytest.mark.parametrize("status", [404, 503])
def test_failed_session_load_never_silently_replaces_estimate(page, status):
    creates = []
    page.on("request", lambda request: creates.append(request.url)
            if request.method == "POST" and request.url.endswith("/sessions") else None)
    page.route("**/sessions/unavailable", lambda route: route.fulfill(
        status=status, content_type="application/json", body='{"detail":"unavailable"}'))
    page.goto("/workshop?session_id=unavailable")
    if status == 404:
        expect(page.locator("#message")).to_contain_text("Estimate unavailable")
        expect(page.get_by_role("button", name="New estimate")).to_be_visible()
    else:
        expect(page.locator("#message")).to_contain_text("Couldn't connect")
        expect(page.get_by_role("button", name="Retry")).to_be_visible()
    assert creates == []
    assert "session_id=unavailable" in page.url


def test_poll_reports_failure_recovery_and_timeout(page):
    page.goto("/workshop")
    result = page.evaluate("""async () => {
      const events = [];
      let attempts = 0;
      await new Promise(resolve => {
        setTimeout(resolve, 500);
        window.ParchaUI.poll(async () => {
          if (++attempts === 1) throw new Error('offline');
          return {};
        }, {every: 5, maxMs: 35,
          onError: () => events.push('offline'),
          onRecover: () => events.push('online'),
          onTimeout: () => { events.push('timeout'); resolve(); }
        });
      });
      return events;
    }""")
    assert result == ["offline", "online", "timeout"]
