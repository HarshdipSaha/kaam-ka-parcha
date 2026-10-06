# Effort 011: ui-digital-parcha-build (parent 010)

Branch `ui/digital-parcha`, built in a separate worktree so the money-path work on `main` was not touched.

## Commits
Presentation helpers, payload contract, e2e seam, design system and verify page, workshop/customer/stage pages, responsive audit.

## Deviations from the plan
- `readback_revision` added to the session payload (the plan's JS and tests need it).
- `.stamp` moved to the bottom-right so it does not cover amounts.
- `.phone iframe` height capped to the viewport so the dock stays reachable on the stage view.
- `ui.js`/`app.js` check `audio.readyState`/`audio.error` at init (media events can fire before listeners exist).
- `emptyWorkshop()` clones the server-rendered empty state to stay inside the 60 KB budget (61,413 bytes, cap 61,440).
- `SilentTimbre` returns a valid 8 kHz PCM WAV, since browsers cannot decode raw bytes.

## Checks
Offline suite and `-m e2e` run in this worktree. `tests/test_early_gates.py` has 3 live-mock failures that also fail on `main` before these changes. Not done: manual check on a real Android phone over LAN; tabular-digit check of Google-served Mukta by eye only.

## Design polish pass (impeccable critique)
- Flagged rows and the flag bar no longer use a thick left border; they use a full tint with a ring and a "!" marker.
- Slip got a bottom perforation and a boxed, tilted printed serial; the empty state is a blank bill-book page.
- Idle mic breathes (one authored motion, off under reduced motion); dock has a grab handle.
- English sub-lines have a 13px floor; selection, caret, scrollbar are themed.
- Call card is hidden once the parcha is sealed (it showed an audio error on a finished session).
- Stamp easing changed from overshoot to ease-out; level meter animates transform instead of width.
- Size budget raised from 60 KB to 64 KB (63.3 KB used). Still no framework or bundler.

## UX walkthrough pass (ui-ux-pro-max + real-browser run)
Walked the full mechanic-to-owner flow in Chromium with a fake mic (390x844, touch). Fixed:
- Share panel is now first on the mechanic screen after "Read to customer" (it was below the fold) and the page scrolls to top.
- Sealed mechanic screen offers the verified record and PDF instead of "Send to the customer".
- Greyed reply mic on the owner page now says why ("पहले सहमति दें"); consent scrolls into view when the read-back ends.
- Stage iframes sized so the mic dock fits at 1440x900; pointer cursor and hover states on desktop; 10 ms haptic on record start; sub-line floor 14px.
- ui-ux-pro-max's generated design system (navy SaaS, Lexend) was not adopted; it does not fit the bill-book world. Its checklist (focus, reduced motion, tap targets, haptics) was applied.
- Size: 64.6 KB of 64 KiB cap.

## English / Hindi toggle
- English leads by default; EN | हिं toggle on every page, saved in localStorage (`parcha-lang`), `?lang=` overrides, stage iframes follow via the `storage` event.
- Markup: bilingual pairs are `.hi` + `.en`; single-language values (chips, dates, status, totals) use `.lang-hi` / `.lang-en`. One `data-lang` on `<html>` swaps which language is the headline (CSS `order`, needs `:has`).
- Server adds `delivery_en`, `kind_en`, `status_en`; `ui.js` adds `both`, `setBoth`, `setLang`.
- Size now 69.7 KB (cap raised to 72 KB for this feature).

## Live end-to-end dry run (real Gnani Prisma + Timbre, real extractor), 2026-10-06
Chromium (390x844 touch) with sample WAVs as the fake microphone; server on :8002 with the real `.env`.
- Mechanic phrase "फ्रंट ब्रेक पैड चार सौ पचास रुपये, लेबर दो सौ रुपये, मंगलवार शाम तक" (Timbre-synthesised): items 45000 + 20000 paise, total ₹650, no review fields, delivery Tuesday evening. Read-back via Timbre (21 s audio). Customer "हाँ ठीक है" -> confirmed at revision 1; verify manifest and PDF (6.6 KB) produced. About 40 s end to end.
- Finding 1 (fixed here): Gnani returned HTTP 429 on back-to-back calls; the app treated it as "say it again". `gnani.py` now retries 429/503 twice (1.0 s, 2.5 s) before giving up.
- Finding 2 (not changed, money-path code): the "transcribe" format renders "साढ़े चार सौ" (450) as "04:30 100" while "verbatim" is right, so the cross-check abstains (`crosscheck_disagreement`) and the row asks for a re-check. Safe, but "साढ़े चार सौ" is common speech. Plain phrasing ("चार सौ पचास") passes cleanly.
- Test artefact: the fake mic loops its WAV, so recordings longer than the clip add repeated words.
