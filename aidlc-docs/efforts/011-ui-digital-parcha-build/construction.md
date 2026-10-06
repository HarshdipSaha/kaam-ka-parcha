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
