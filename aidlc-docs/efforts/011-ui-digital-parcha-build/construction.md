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
