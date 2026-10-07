# Handoff (2026-10-07)

Everything runnable is done and on `main` (money-path plan, UI PR #19, prompt reword, fraction-aware cross-check,
two-agreeing-recordings rule, re-ask recovery benchmark, deploy files, owner recorder). See
`aidlc-docs/efforts/009-money-path-plan/effort-state.md` ("Follow-up hardening") and `docs/gates.md`.

Remaining, user-only: deploy (`docs/deploy.md`), record the 80 owner takes (`docs/owner-recording.md`),
human listening labels, Task 0 console balance / Gramvaani permission.

Never commit `.env`, `var/`, private audio. Two unrelated untracked files stay out of commits:
`scripts/benchmark_youtube_samples.py`, `tests/test_youtube_benchmark.py`.

---

# Handoff 2026-10-07: sug.md Part A

**Open PRs (nothing merged; the merge was blocked in the session).** Suggested order: #45, #47 (numeral fixes), #34 (A0), #35 (A12), then #42 (A9, base is #35's branch: retarget to main),
#37 (A1; its branch already contains the #45/#47 fixes), #36 (A2), #43 (A10), #38, #39, #40, #41. Expect small conflicts in `app.py`, `workflow.py`, `ui.js` between #35/#37/#36/#43/#42.

**Do next:** run the full offline suite and `tests/e2e -m e2e` after merging; B1 record the owner takes, then A3; B2 deploy then A6; B3 organiser consent before the public A14 report;
B8 native-speaker review of `src/parcha/languages.py` before showing Tamil/Bengali/Kannada to real customers; refresh `docs/submission/*` numbers after the merges.

**Known limits worth remembering:** evidence is synthetic speech; residual wrong-settle risk is look-alike pairs outside the flagged set (-ty twins, तैंतीस/पैंतीस); Tamil/Kannada echo cannot be scored by digits;
REST STT rejects clips of about 30 s or more (the 60 s doc claim does not hold); CSS+JS is 69 KB vs the 60 KB spec.
