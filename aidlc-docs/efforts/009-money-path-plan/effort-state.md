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
| Implementation | Active | Tasks 1–10 implementation complete; Task 0 owner-only pre-flight remains pending |

## Implementation Progress

- **Task 0 — Pending (owner-only pre-flight):** On 2026-10-06, the owner confirmed hackathon-provided API keys and sufficient credits for Task 10’s 432.1-credit forecast and authorized the synthetic TTS render. The configured key was present and used without logging its value. The exact console balance and billed amount were not independently captured; organizer/Gramvaani outreach remains pending before later public or real-data runs.
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

## Task 9 — Complete: Gold-first v2 amount data

Added `src/parcha/lab/amount_bench.py` and `scripts/make_amount_benchmark.py` to generate seeded estimate, correction, stress-amount, and bias-control datasets. All JSONL rows are validated through `Clip`; amount labels are in spoken order. Added gold-first renderer, stress round-trip, deterministic estimate, correction, and bias-control regressions in `tests/test_benchmark_v2.py`.

- **Task 9 execution checklist:** [x] Add regressions and observe expected missing-module RED; [x] implement seeded generators and writer; [x] generate all four tracked artifacts; [x] validate JSONL rows and ordered amount labels; [x] run focused benchmark tests; [x] run full offline suite; [x] `git diff --check`; [x] no live APIs or paid services.
- **Generated outputs:** `estimates.jsonl` — 120 rows, 296 labels, 86,462 bytes; `corrections.jsonl` — 40 rows, 40 labels, 20,939 bytes; `bias_control.jsonl` — 20 rows, 0 amount labels, 9,897 bytes; `stress_rupees.json` — 37 distinct amounts, 341 bytes.
- **Validation:** Initial RED was 4 missing-module failures and 11 existing passes. `.venv\Scripts\python.exe -m pytest -q tests/test_benchmark_v2.py`: 15 passed. With `PYTHONPATH=src` and `API_KEY=test-only`, `.venv\Scripts\python.exe -m pytest -q`: 438 passed. The suite reported one existing Starlette `TestClient` deprecation warning. Generator printed exactly `estimates=120 (amounts=296) corrections=40 stress_amounts=37`.

## Task 10 — Complete: Multi-voice Timbre renderer and per-character forecast

Added `scripts/render_amount_benchmark.py` and `tests/test_render_forecast.py`. The forecast counts Python string codepoints in the exact `text` sent to `TimbreClient.synthesize`, multiplies by `TTS_CREDITS_PER_CHAR = 0.05`, rounds credits to two decimals, and reports sorted unique voices. The CLI reads UTF-8-SIG JSONL; dry-run prints JSON without loading settings or contacting services. Live mode preflights all required fields and resolved destinations before loading settings, rejects output paths outside the resolved audio root, the root itself, and duplicate destinations, then requires `API_KEY`, reuses one Timbre client per voice, converts mu-law responses to WAV, skips cached files, spaces requests, and closes all clients even if a close fails.

- **Task 10 execution checklist:** [x] Add forecast regression and observe missing-module RED; [x] implement forecast and CLI; [x] cover BOM input, credential-free dry-run, finite non-negative interval validation, cache behavior, per-voice reuse, request spacing, and cleanup failures with offline tests; [x] preflight every live row before settings/client/request/output side effects; [x] reject path escapes, symlink escapes, root destinations, and duplicate resolved outputs; [x] ensure every client close is attempted and preserve synthesis errors when cleanup fails; [x] validate all three generated manifest forecasts; [x] run focused tests; [x] run full offline suite; [x] run three dry-run CLI commands; [x] run the owner-authorized 120 + 40 + 20 live TTS renders; [x] verify 180 WAV files and ffprobe spot-checks; [x] `git diff --check`.
- **Dry-run forecasts:** `estimates.jsonl` - 120 rows, 7,140 characters, 357.00 credits; `corrections.jsonl` - 40 rows, 1,084 characters, 54.20 credits; `bias_control.jsonl` - 20 rows, 418 characters, 20.90 credits. The Task 10 plan arithmetic supplied earlier (6,843 / 342.15 and 1,080 / 54.00) is stale for the current generated manifests. Direct generation from `parcha.lab.amount_bench` matches these current totals; no Task 9 data was changed to force the stale figures.
- **Validation:** `.venv\Scripts\python.exe -m pytest -q tests/test_render_forecast.py`: 26 passed; `PYTHONPATH=src`, `API_KEY=test-only`, `.venv\Scripts\python.exe -m pytest -q`: 464 passed. Three dry runs with API_KEY empty printed the forecast totals. Live runs generated 120 estimate, 40 correction, and 20 bias-control WAVs (180 total) using the configured key; forecast spend was 432.1 credits, actual billed spend was not read from the console. `ffprobe` confirmed `pcm_s16le`, 8,000 Hz, mono for one file from each manifest. One existing Starlette `TestClient` deprecation warning was reported.

## Next

Task 0 owner-only pre-flight.
