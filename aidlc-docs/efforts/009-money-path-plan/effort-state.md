# Effort State: 009 — Money-Path Safety Implementation Plan

**Effort ID:** 009
**Reference:** `money-path-plan`
**Status:** active
**Started:** 2026-10-05
**Parent:** `008-real-audio-analysis-council-spec`

## Stage Progression

| Stage | Status | Notes |
|---|---|---|
| Requirements | Complete | [`requirements-delta.md`](requirements-delta.md) |
| Data verification | Complete | Gramvaani parquet, Timbre voices, rates, bias list and code interfaces were checked; see [`construction.md`](construction.md) §2 |
| Prototyping | Complete, partial by owner request | 311 tests passed in a scratch copy. The remaining checks are deferred to implementation |
| Plan | Complete | [`2026-10-05-money-path-safety.md`](../../../docs/superpowers/plans/2026-10-05-money-path-safety.md) |
| Spec sync | Complete | [`money-path-safety-spec.md`](../../../docs/specs/money-path-safety-spec.md) corrected and committed |
| Audit | Complete | [`audit.md`](audit.md) |
| Implementation | Active | Task 1 complete; Task 0 owner-only pre-flight remains pending |

## Implementation Progress

- **Task 0 — Pending (owner-only pre-flight):** Verify console balance and key provenance, and complete organizer/Gramvaani outreach before live runs. These require owner account access and external outreach; they were not completed in this coding task.
- **Task 1 — Complete:** Corrected README speech/extractor settings, removed unmeasured README/demo claims, and corrected the gate ledger and audio provenance. Commit subject: `docs: remove unmeasured claims and mark extractor required`.
- **Validation:** README uses `GNANI_BASE_URL` and not `API_BASE_URL`; margin claims absent; generalisation/E2E rows remain not reproducible and future gates pending; `git diff --check`: PASS.

- **Task 2 — Complete:** Added deterministic Hinglish/Devanagari/ITN amount parsing and Hindi/colloquial renderers in `src/parcha/numerals.py`, with public-interface coverage in `tests/test_numerals.py`, including half-multiplier, year/date, and hyphenated-registration safety cases. Commit subject: `feat(money): deterministic Hinglish amount grammar`.
- **Validation:** 175 passed in `tests/test_numerals.py`.

- **Task 3 — Complete:** Wired deterministic Hinglish numeral parsing into `Workflow.intake` with dual-pass cross-checking (`src/parcha/money.py`), added `RepeatRequest` on empty transcripts/504/429, and recorded system abstention logs atomically. Commit subject: `feat(money): amounts only from grammar with abstain-and-re-ask at intake`.
- **Validation:** 30 passed in `tests/test_money_path.py tests/test_workflow.py tests/test_app.py`.

- **Task 4 — Complete:** Amount re-ask (`Workflow._reask_amount`) uses numeral grammar and cross-checks, never the extractor. Correctly abstains on multi-number corrections and preserves unrelated card fields. Commit subject: `feat(money): amount re-asks use grammar and cross-check, never the extractor`.
- **Validation:** 22 passed across `tests/test_money_path.py tests/test_workflow.py`.

- **Task 5 — Complete:** Workshop UI repeat request error handling with Hindi user notices (*"आवाज़ साफ़ नहीं आई — कृपया फिर से बोलिए"*) and inline reason badges for abstained fields. Commit subject: `feat(app): repeat request and per-amount re-ask reasons in the workshop UI`.
- **Validation:** 2 passed in `tests/test_app_repeat.py`; 407 passed in full suite.

- **Task 6 — Complete:** Evon extractor wiring with JSON schema enforcement (`CARD_RESPONSE_SCHEMA`) ensuring `amount_paise: null`, thinking off (`enable_thinking: False`), `<think>` stripping, and removal of Groq fallback in configuration. Tested live with real `.env` credentials. Commit subject: `feat(extract): Evon as the line-item extractor; no Groq fallback`.
- **Validation:** 13 passed in `tests/test_extract_evon.py tests/test_config.py`; 411 passed in full test suite. Live extraction smoke test passed.

## Next

Task 7: Line Noise Lab: canonical references, outcomes, labels, bias control.
