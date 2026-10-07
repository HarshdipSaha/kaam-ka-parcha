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
