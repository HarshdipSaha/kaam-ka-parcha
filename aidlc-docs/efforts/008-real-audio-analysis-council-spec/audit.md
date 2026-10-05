# Effort 008: Audit

**Audit date:** 2026-10-05
**Status:** Complete. Not committed. Spec publication to GitHub Issues pending `gh`.

| Requirement (from [`requirements-delta.md`](requirements-delta.md)) | Evidence | Audit result |
|---|---|---|
| Deep, reproducible analysis of the PR #17 results | [`R9`](../../../docs/research/R9-real-audio-benchmark-analysis.md); `scripts/analyze_real_audio_benchmark.py` (stdlib only, compiles, re-run twice with identical output, asserts recomputed CER == stored CER on 1,920 rows) | Pass |
| Analysis covers reference quality, paired modes with CIs, codec/SNR, strata, numerals, bias, failure shapes, workshop slice, latency, credits | R9 §1–§8 | Pass |
| Absolute numbers kept private | R9 header marks it private; the verdict and spec keep CER out of public metrics; script output goes to ignored `var/` | Pass |
| Council re-run with the `llm-council` method | [`framed-question`](../../../docs/ideas/council-real-audio/framed-question.md), [`responses-anon`](../../../docs/ideas/council-real-audio/responses-anon.md), [`mapping-secret`](../../../docs/ideas/council-real-audio/mapping-secret.md), [`reviews`](../../../docs/ideas/council-real-audio/reviews.md), [`verdict`](../../../docs/ideas/council-real-audio-verdict.md) | Pass |
| Review corrections fed back | R9 finding 7 (bias boosting unverified) and §6 (agreement is a formatting cross-check) amended; chair's notes in `reviews.md` | Pass |
| Spec written with the `to-spec` skill | [`money-path-safety-spec.md`](../../../docs/specs/money-path-safety-spec.md) (revised with the owner's decisions; committed with effort 009): skill template, project vocabulary, two existing seams, no file paths or code in decisions, out-of-scope list from the verdict | Pass. One derived decision (deterministic attachment of amounts to items) is flagged for owner confirmation |
| Spec published to the issue tracker with `ready-for-agent` | `gh` not installed and no API token, so not published; exact command recorded in the spec | **Partial**: owner action needed |
| AIDLC record and registry | This folder; registry row 008 | Pass |
| No API calls, credit spend, product-code changes or secrets | `git status` shows only docs plus one new analysis script; no `src/` or `tests/` changes | Pass |

## Documentation checks

- `git diff --check`: clean.
- Link and whitespace script over the 12 new or changed markdown files: every relative link resolves once this file exists. The only whitespace hits are registry lines 3–5, which are pre-existing markdown hard line breaks and were not edited.
- `py -3 -m py_compile scripts/analyze_real_audio_benchmark.py`: OK.
- Gendered-pronoun scan of the new council, spec and R9 files: none.
- Application tests were not run. The only new code is a standalone offline script outside the package and the test suite (`AGENTS.md`: documentation-only changes skip application tests). It validates itself against the stored metrics.

## Acceptance

All three asks are met: deep analysis, council re-run and updated spec. Open owner actions, none of them acceptance criteria for this effort:
- record the key balance and the provenance of the ten extra keys;
- send the organiser questions;
- confirm the spec's seams and the derived attachment decision;
- publish the spec once `gh` is available.
