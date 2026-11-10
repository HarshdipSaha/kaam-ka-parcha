# Effort 016 — call-button-and-submission (2026-11-09 to 2026-11-10)

**State:** complete. Offline suite 826 passed locally (`python -m pytest -q`, the same command CI runs).

## Why
Submission day for the Gnani challenge (deadline 2026-11-10). The demo video needed the real Twilio call to start
from the product, not from a hand-made `POST` in a terminal, and the submission form needed a one-page pitch, a
2-3 minute demo script, and slides. A rehearsal on the live site then surfaced two call bugs.

## Delivered
- **Workshop call button** (`20b5814`). "Call the customer's phone" appears on `/workshop` once the card has no
  flagged amounts; never inside `/stage`, whose page promises a simulated line. Optional `TWILIO_DEFAULT_TO` lets it
  dial a preset number while the page only ever shows the last four digits; without it the button asks for the
  number. After dialling, the page follows the session (2 s poll, 5 min cap) through read-back, any spoken correction
  and re-read, to confirmation. `to_number` on `POST /sessions/{id}/telephony/call` became optional.
- **Correction acknowledged on the call** (`61374dc`). After a spoken correction (`needs_readback`) the call said
  "Samajh nahi aaya. Kripya phir se boliye." before the new read-back, because that outcome fell through to the retry
  phrase. It now says "Theek hai, badal diya. Naya parcha suniye."
- **Number typed any common way** (`5b8d05d`). Rehearsal: tapping the button "did nothing". Cause: the input's strict
  E.164 `pattern` rejected "98765 43210" and "+91 98765 43210", and the warning rendered in the message at the top of
  the page while the button sits in the bottom dock. `telephony.normalize_phone` now accepts spaces, dashes, a leading
  0 or 91 and a missing +91 for Indian mobiles (any E.164 number with a leading +); every call problem is also shown
  as a toast next to the button, including Twilio's own error text.
- **Submission material.** `PITCH.md` (one page, linked from the README top), `docs/submission/demo-recording-script.md`
  (second-by-second call behaviour from the code and the 2026-10-07 live calls, timed script, troubleshooting),
  `docs/submission/problem-slide.{html,png,@2x.png}` and `docs/submission/usp-diagram.{html,png,@2x.png}`.
- **Lighthouse measured** (first time; 12.6.1, mobile, live site, 2026-11-10): `/workshop` performance 83,
  `/stage` 91; accessibility 100 on both; best practices 96; SEO 90.

## Tests
- Added: preset number used when none is typed (and appears in the voice URL); 422 when neither exists; the page shows
  only the last four digits and no number box when a preset exists; the box appears without one; no button without
  Twilio settings; the correction phrase; seven typed formats normalise to E.164 and five non-numbers are refused;
  the endpoint accepts a spaced number.
- Changed on purpose: the "bad number" case moved from "9876543210" (now valid) to "12345".

## Verified
- Each push was confirmed live on Render by a probe session disappearing after the restart, then `/health`.
- Live endpoint probes (no call placed): Twilio settings present (an empty card reaches `409 card needs review`, not
  `503`); a spaced number is accepted after `5b8d05d`.
- A real call from the button was not observed by this effort; the owner was rehearsing at hand-off.

## Remaining
- **GitHub Actions has not run since `20b5814`:** every job reports "The job was not started because your account is
  locked due to a billing issue." Code is not the cause; the owner must clear the billing lock. Until then, the local
  offline suite is the CI evidence.
- `TWILIO_DEFAULT_TO` is not yet set on Render, so the live button shows a number box.
- A correction spoken on a real call has never been tried live; with two items, a label/transcript spelling mismatch
  leads to "Kaunsa item badalna hai?", and the follow-up reply without "nahi" is classed unclear.
- Inherited from 015: sessions are in memory (verify/PDF links in the SMS die on restart); cold start on the free plan.
