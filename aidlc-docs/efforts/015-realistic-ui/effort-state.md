# Effort 015 — realistic-ui (2026-10-21)

**State:** complete. Offline suite 807 passed; browser (e2e) suite 67 passed.

## Why
After the real Twilio call worked, the owner opened the live site and receipt as a user and found it still read as
fake and cluttered. Walking the live site found the cause was code, not data:
- The sealed PDF, the verify page (the link in the confirmation SMS) and the verification JSON printed a hard-coded
  vehicle, `KA-01-AB-1234 (Synthetic Demo)`, although the app never captures a vehicle. The PDF title said "(Demo)",
  the PDF said "No real call was placed", and the WhatsApp text said "All demo identities and data are synthetic",
  all of it also on sessions confirmed by a real phone call.
- The workshop header carried a permanent "Synthetic demo data" pill; the customer page said "All names and amounts
  are synthetic".
- Clutter: every string was shown in English and Hindi at once (the toggle only swapped which was the headline);
  `/stage` repeated the title and the language toggle three times (the page plus each phone frame); the mic dock
  covered content; "Rev N" showed on the customer's card.

## Delivered
- `Session.channel` ("phone" | "browser"). `Workflow.start_readback(channel=...)` records a `call_channel` system log
  when the Twilio webhook starts the read-back; it is part of the audit manifest, so it cannot be stripped without
  changing the manifest hash (test).
- PDF, WhatsApp text, verify page/JSON and customer page now say what actually happened. A browser confirmation still
  says the line was simulated (that disclosure is kept, per AGENTS.md); a real call never claims it was simulated.
  The invented vehicle line is gone from the PDF, verify page and JSON (JSON now carries `channel` instead).
- "Synthetic demo data" pill removed; a "Demo mode · scripted speech" badge shows only when `PARCHA_MOCK` is on.
- One language at a time (the toggle picks it; the approval stamp keeps both, like a rubber stamp). English stays the
  default: a browser-language default was tried and reverted because tests record "English leads by default".
- `/stage`: single header and toggle, frames hide their own header (`embedded` class set when inside an iframe), taller
  frames so both phones fit a 1440x900 screen; hint chips smaller; `Rev N` badge hidden (still in the verify audit
  panel); the customer page reserves enough bottom space for its taller dock.
- Static assets are versioned with a content hash (`?v=`), so a visit before a deploy cannot pair new HTML with an old
  stylesheet.

## Tests
- Changed on purpose: tests that pinned the fake plate, "All names and amounts are synthetic", "Synthetic demo data",
  and e2e checks that located elements by their Hindi label while both languages were always visible.
- Added: phone-channel receipt (PDF, WhatsApp, verify, JSON, customer page), channel is in the signed manifest, demo
  badge only in mock mode, asset versioning, one-language-at-a-time and no-repeated-header e2e checks.
- The mic stays 96px: the e2e suite requires a thumb-sized primary button (88px minimum); a 84px attempt failed it.
- e2e ran against the installed Chrome (`--browser-channel chrome`); the bundled Chromium was not installed here.

## Verified
Local mock-mode server, one browser-confirmed and one phone-confirmed session (signed Twilio webhooks), screenshots of
workshop, stage, customer (awaiting and confirmed) and verify at mobile and desktop widths. Measured: the customer
dock is 160px against the old 128px reserve (now 176px, 40px clear).

## Remaining
- Sessions are in memory: when the free Render instance idles (about 15 minutes) or restarts, the verify and PDF links
  in the confirmation SMS return 404. Needs persistent storage (a paid disk or an external database) to fix.
- A first visitor after idle sees Render's "Application loading" page for about 50 seconds. Mitigate with an uptime
  ping on `/health` or the paid plan.
- README/`docs/ui` screenshots were captured from an earlier UI; regenerating them needs a live capture run.
- No vehicle number is captured; a real one would need an optional field and a deliberate privacy decision.
