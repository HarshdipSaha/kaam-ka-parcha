# Mobile and accessibility pass (2026-10-07)

Automated in `tests/e2e/test_a11y_perf.py` (offline fakes, no credits; run with `pytest tests/e2e -m e2e`). Layout, 48 px touch targets, 88 px mic, 16 px body text and unlabeled-button checks at 360x800 and 390x844 were already in `tests/e2e/test_responsive.py`.

| Check | Result |
|---|---|
| First interaction on emulated Fast 3G (Chromium: 562 ms latency, 1.6 Mbit/s down), `/workshop` until the mic is enabled | 2.0 s at 360x800, 1.8 s at 390x844 (local server; budget 6 s) |
| WCAG AA text contrast (4.5:1, 3:1 for large text) on workshop, customer call, customer sealed and verify pages, Hindi-first and English-first | 2 failures found and fixed: the secondary-language text was dimmed with `opacity` (.8 / .85), dropping Hindi muted/green text to 3.4-3.8:1. Both rules now use full opacity; hierarchy comes from size and weight. Gradient backdrops are checked against every colour stop. |
| Keyboard order and focus | No positive `tabindex`; tab order on the customer page follows page order; every focused control shows a visible indicator. |
| Hindi rendering | The body font stack (`Mukta`, `Nirmala UI`, `Noto Sans Devanagari`) measures and renders Devanagari with non-zero width; a screenshot is written to the ignored `var/e2e/` folder. |
| CSS + JS size | 69,017 bytes raw, 19,551 bytes gzip when measured; 75,086 raw / 21,381 gzip after confirm-estimate, live captions and the language selector landed. The UI spec's 60 KB target is **not met** (about 9 KB over raw). Not cheap to fix without a build step (minification), so recorded rather than fixed; the test caps growth at 80,000 raw / 25,000 gzip. |

Limitations: time-to-interaction is measured against the local server with network throttling, not a deployed host; contrast is computed from computed styles and cannot see text over images; no screen-reader pass was run.
