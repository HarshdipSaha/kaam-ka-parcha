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
| Implementation | Active | Tasks 1–8 complete; Task 0 owner-only pre-flight remains pending |

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

- **Task 7 — Complete:** Added canonical benchmark references, explicit provider-error/empty/ok row outcomes, strict expected-amount labels, four-digit clip IDs, BOM-tolerant JSONL reading, unbiased verbatim mode, and stale-row rejection on resume. Added `data/benchmarks/exclusions.json`. Commit subject: `feat(lab): canonical references, explicit empty outcome, amount labels, bias control mode`.
- **Validation:** 12 passed in `tests/test_lab_v2_runner.py`; 53 passed across the focused lab/dataset regression modules; 423 passed in the full offline suite. Analysis script completed successfully and reported 65 output entries; `var/lab/real_audio_analysis.md` has 110 physical lines because some entries contain embedded newlines. `git diff --check`: PASS.

- **Task 8 — Complete:** Added `src/parcha/lab/money_eval.py` with order-independent transcribe/verbatim pairing, per-amount correct/wrong/abstained outcomes, Wilson upper bounds, number-agreement scoring, and the local `python -m parcha.lab.money_eval` JSON CLI. The CLI accepts repeated result files and manifests, concatenates all result rows, reads manifests as UTF-8-SIG, skips `data/benchmarks/exclusions.json` IDs, and creates the output directory. Condition labels preserve `codec|clean` and `codec|0` for default conditions, retain fractional SNR precision, and append loss/profile details only when non-default. Added regressions in `tests/test_benchmark_v2.py`, including identical wrong values on both passes, provider-error abstention with paired and single error rows, fractional SNR/loss/profile separation, repeated result files, incomplete number agreement, BOM manifests, and exclusions.
- **Task 8 execution checklist:** [x] Write the single-provider-error and CLI/condition-collision regressions and observe their expected RED failures; [x] implement evaluator and CLI fixes; [x] targeted CLI/fractional-SNR/loss/profile regressions (4 passed); [x] full `tests/test_benchmark_v2.py` (10 passed); [x] full offline suite (433 passed); [x] `git diff --check`; [x] no live APIs or Prisma calls.
- **Validation:** `.venv\Scripts\python.exe -m pytest -q tests/test_benchmark_v2.py -k "fractional_snr or nonzero_loss or impulse_profile or cli_reads"`: 4 passed; `.venv\Scripts\python.exe -m pytest -q tests/test_benchmark_v2.py`: 10 passed; `PYTHONPATH=src`, `API_KEY=test-only`, `.venv\Scripts\python.exe -m pytest -q`: 433 passed. Pytest reported one existing Starlette `TestClient` deprecation warning.

## Next

Task 9.
