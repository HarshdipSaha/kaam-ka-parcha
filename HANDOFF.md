# Handoff (2026-10-07)

Everything runnable is done and on `main` (money-path plan, UI PR #19, prompt reword, fraction-aware cross-check,
two-agreeing-recordings rule, re-ask recovery benchmark, deploy files, owner recorder). See
`aidlc-docs/efforts/009-money-path-plan/effort-state.md` ("Follow-up hardening") and `docs/gates.md`.

Remaining, user-only: deploy (`docs/deploy.md`), record the 80 owner takes (`docs/owner-recording.md`),
human listening labels, Task 0 console balance / Gramvaani permission.

Never commit `.env`, `var/`, private audio. Two unrelated untracked files stay out of commits:
`scripts/benchmark_youtube_samples.py`, `tests/test_youtube_benchmark.py`.

---

# Handoff 2026-10-07: docs/dev-notes/sug.md Part A

**Status:** all Part A PRs (#34-#43, #45, #47, #48, #49) are merged into `main`; combined main passes the offline suite (743) and the e2e suite.

**Do next:** run the full offline suite and `tests/e2e -m e2e` after merging; B1 record the owner takes, then A3; B2 deploy then A6; B3 organiser consent before the public A14 report;
B8 native-speaker review of `src/parcha/languages.py` before showing Tamil/Bengali/Kannada to real customers; refresh `docs/submission/*` numbers if anything changes.

**Known limits worth remembering:** evidence is synthetic speech; residual wrong-settle risk is look-alike pairs outside the flagged set (-ty twins, तैंतीस/पैंतीस); Tamil/Kannada echo cannot be scored by digits;
REST STT rejects clips of about 30 s or more (the 60 s doc claim does not hold); CSS+JS is 69 KB vs the 60 KB spec.

---

# Handoff 2026-10-07: deploy hardening + real Twilio phone leg

**Status:** deployed live at `https://kaam-ka-parcha.onrender.com` (Render free plan). Offline suite 781 passed.
See `aidlc-docs/efforts/013-deploy-hardening/effort-state.md` and `aidlc-docs/efforts/014-twilio-phone-leg/effort-state.md`.

**What's new:** CI, MIT `LICENSE`, `PARCHA_MOCK=1` offline demo mode, `src/parcha/redact.py` (masks phone/Aadhaar/PAN
before the external extractor), Gnani `API_KEY` can list several comma-separated keys with automatic failover on
401/403 (`src/parcha/gnani.py:KeyPool`), `MAX_SPEECH_CALLS_PER_DAY` app-wide spend cap, 29.5 s Prisma recording cap,
optional `AUDIO_CLEANUP` (unmeasured). A real customer phone call via Twilio (`src/parcha/telephony.py`,
`/telephony/twilio/*`) now runs alongside the simulated line — **live-verified with a real call**: session
`PjN3-GlUfgLocLvsiihW4NMB` reached `confirmed`, total ₹650, parcha no. `644793`. A later run (`uj-Al-6o8YceseXKlLZYnnFo`, parcha no. `859653`) also delivered the confirmation SMS with the verify link to the owner's phone.

**Do next:** `/workshop` has no button yet for the phone call (API-only: `POST /sessions/{id}/telephony/call`);
no WhatsApp delivery (SMS with the verify link is sent on a phone confirmation); real-call accuracy scoring (~20 calls via
`parcha.lab`) not yet run; `AUDIO_CLEANUP` A/B not yet measured.

**Known limits worth remembering:** Twilio trial plays its own disclaimer and requires an actual on-screen keypad
tap (a phone side button does nothing) before it calls our webhook at all; trial calls are capped at 10 minutes,
verified numbers only, 30-day account expiry. `aidlc-docs/`, `docs/raw/`, `docs/webattack_artifacts/` are still
tracked in the repo; several docs link into them, so moving them needs its own pass.

---

# Handoff 2026-10-21: realistic UI (effort 015)

The sealed PDF, verify page, WhatsApp text and customer page no longer call a real phone call simulated or synthetic
(`Session.channel`, recorded in the audit manifest); the invented `KA-01-AB-1234 (Synthetic Demo)` vehicle is gone; the UI
shows one language at a time and `/stage` no longer repeats its header. Offline 807 passed, e2e 67 passed
(`pytest -m e2e --browser-channel chrome`). See `aidlc-docs/efforts/015-realistic-ui/effort-state.md`.

**Do next:** persistent session storage (the verify/PDF link in the confirmation SMS returns 404 once the free Render
instance idles or restarts); keep the instance warm before demos; regenerate the README/`docs/ui` screenshots from a
live capture run; a "Call customer" button in `/workshop`.

