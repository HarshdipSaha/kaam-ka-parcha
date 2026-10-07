# Effort 014 — twilio-phone-leg (2026-10-07)

**State:** complete. Live-verified with a real phone call.

## Scope
A real customer phone call via Twilio, as an additional leg alongside the existing in-browser simulated line
(never a replacement). From `HARSHDOTHIS.md` P1-1 — the single highest-value item for the Noise Canceller award,
since it turns "simulated phone line" into real telephone audio.

## Delivered
- `src/parcha/telephony.py` (commit `af1675d`): plain TwiML string builders (`twiml`, `say`, `play`, `record`,
  `hangup`), Twilio request-signature validation (`signature_valid`), `place_call` and `download_recording` —
  both raw `httpx` calls against Twilio's REST API, no `twilio` SDK dependency added.
- Three routes in `app.py`:
  - `POST /sessions/{id}/telephony/call` — places an outbound call once the card is ready (same precondition as
    the browser read-back route); guarded (added `/telephony/call` to `guard.GUARDED_PATH_PARTS`).
  - `POST /telephony/twilio/voice` — plays the read-back, then `<Record>`.
  - `POST /telephony/twilio/recording` — runs the recording through the existing `workflow.reply` classification;
    `<Redirect>` back to a fresh read-back on `needs_readback`, another `<Record>` on `ask_field`/`retry`,
    `<Hangup/>` on `confirmed` or `fallback`.
  - `POST /telephony/twilio/status` — logs call status, 204, no state change.
  - All four verified against `X-Twilio-Signature`; exempted from `DEMO_ACCESS_CODE` (Twilio can't carry that
    cookie) via a middleware path exemption.
- `Workflow.start_readback` / `.reply` gained a `degrade: bool = True` parameter — a real call already passes
  through a real line's codec, so this leg sets `degrade=False` and skips the simulated noise+codec layer that
  the browser leg still applies.
- Settings: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, `PUBLIC_BASE_URL`,
  `Settings.require_twilio()`. Documented in `.env.example`, `render.yaml` (as `sync: false` secrets),
  `docs/deploy.md`.

## Bug found and fixed during live verification (commit `85a26ff`)
First real call ("an application error has occurred"). Twilio's own Request Inspector for the call (`CA2e351d...`)
showed the webhook itself returned 200 with valid TwiML, but the `<Play>` URL 404'd. Root cause: `start_readback()`
returns the WAV bytes; only the browser-facing `/sessions/{id}/readback` route ever wrote them to
`var/sessions/{id}/{revision}.wav` — the new `/telephony/twilio/voice` handler never did. Fixed by writing the
file in that handler too, matching the browser route. Added a regression test that fetches the `<Play>` URL
through the test client and asserts 200/`audio/wav`; confirmed it fails (404) on the pre-fix code via `git stash`.

## Tests
- `tests/test_telephony.py`, 18 tests: TwiML builders, `signature_valid` checked against the official
  `twilio/twilio-python` SDK's own `tests/unit/test_request_validator.py` vector (fetched from the real repo,
  2026-10-07) — not just self-consistency; `place_call`/`download_recording` against a mocked transport; the full
  app routes (call placement validation, signature rejection, voice/recording webhook outcomes including the
  `<Play>`-is-fetchable regression, the `DEMO_ACCESS_CODE` exemption).
- Offline suite: 758 → 776 passed (effort 013's count → after this effort). Full suite re-run green after the
  WAV-write fix: 776 passed.

## Live verification (real Twilio call, real voice, no simulation)
- Twilio trial account: number bought `+19783505146` ($1.15/mo, covered by trial credit), caller ID
  `+91 92281 82636` verified by the user via Twilio's own OTP flow.
- Built two test sessions on the live deployment using Timbre-synthesized Hinglish dictation (same "synthetic
  speech into a fake mic" pattern as `scripts/capture_live_screens.py`) to reach a complete, non-review card:
  `front brake pad ₹450` + `labour ₹200` = `₹650`, delivery Monday evening.
- Attempt 1 (`CA2e351d...`): hit the WAV-write bug above; fixed and redeployed (`85a26ff`, live on Render).
- Attempt 2 (`CA40e374...`): call connected and ran 13s, but Twilio's own trial disclaimer/keypress pre-roll
  never advanced into our `Url` webhook (confirmed via the call's own Request Inspector: only the `Calls.json`
  create and the final status callback appear, `/telephony/twilio/voice` never requested). Root-caused against
  Twilio's official trial-limitations doc ("a short trial message [plays] before your TwiML is executed") — not
  an app bug; most likely the keypress during the trial message wasn't a real DTMF tap (phone side button vs.
  on-screen dialer digit).
- Attempt 3 (`CA4fa4ee...`): user tapped an actual on-screen keypad digit — call reached `/telephony/twilio/voice`,
  played the read-back, recorded "haan, theek hai", classified as `confirmed`.
- Final state, verified via `GET /sessions/{id}`: session `PjN3-GlUfgLocLvsiihW4NMB`, `status: "confirmed"`,
  `total_paise: 65000`, `parcha_no: "644793"`. PDF and verify page fetched and confirmed reachable:
  `/sessions/{id}/pdf`, `/verify/{id}`.

## Remaining (follow-up, not required to prove the concept)
- No `/workshop` UI button yet — the call is placed via the API directly. Deferred until the live path was proven
  (this effort), per the plan recorded in the prior turn.
- No automatic WhatsApp/SMS delivery of the confirmed PDF after a phone confirmation; the TwiML's spoken line says
  it will be sent, but nothing sends it yet (same "nothing is sent automatically" design as the browser leg).
- Real-call scoring (~20 calls through `parcha.lab`, per `HARSHDOTHIS.md` P1-1 step 6) not yet run — this effort
  covers correctness, not an accuracy benchmark.
- Twilio trial limits apply to every future call: verified numbers only, a trial announcement prefix, 30-day
  account expiry, 10-minute per-call cap.
