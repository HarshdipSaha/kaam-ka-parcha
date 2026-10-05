# Effort State: 006 — Budgeted Real-Audio API Benchmark

**Effort ID:** 006
**Reference:** `real-api-real-audio-benchmark`
**Status:** active (final validation and PR/merge pending)
**Started:** 2026-10-05
**Parent Effort:** `004-enterprise-telephony-compliance`

## Stage Progression

| Stage | Status | Notes |
|---|---|---|
| Research and source review | Complete | First-party source review recorded in [`docs/research/real_audio_benchmark_sources_2026-10.md`](../../../docs/research/real_audio_benchmark_sources_2026-10.md). IndicContextEval selected for a CC BY 4.0 broad professional Hindi slice. |
| Budget and privacy boundary | Complete | User initially selected 4,000 credits, then explicitly waived that limit and stated ten additional keys with 5,000 credits each are available. The sweep used a 5,000-credit local estimate for the configured key at 0.2 credits/second; current balance cannot be read from the configured API. Unredacted user-video data stays under ignored `var/`; the private handoff contains only the attributed CC BY sample audio. |
| Offline safety and metrics | Complete pending final suite | Added both Prisma modes, optional verbatim bias, request spacing, WER, source attribution, validated resume, and stop-on-provider-error behavior. Focused tests pass. |
| Dataset indexing and sample selection | Complete | Refreshed all 3,110 Hindi rows. Prepared 120 speaker-disjoint clips spanning 23 domains, both speech styles, and both code-mixing values; five user-provided video segments are separately marked as auto-caption references. |
| Live API preflight and pilot | Complete | Forecast passed at 4,964.86 estimated credits. The run completed 2,000 unique conditions and 2,000 successful requests; two HTTP 504 attempts were separately retained and each condition succeeded on one retry. |
| Bounded live benchmark | Complete | 120 IndicContextEval clips plus five private workshop clips; two STT modes, two codecs, four SNR levels. All 2,000 planned condition keys appear exactly once in the success output. |
| Aggregation and audit | Complete | Full private aggregates are in `var/lab/real_audio_summary.json`; the handoff bundle is `data/benchmarks/real_audio_2026-10/`. The five YouTube-source rows retain conditions and metrics but redact their source IDs and text; their audio is not bundled. No public report was generated. |
| Final offline validation | Complete | Full suite: 214 passed; compileall and `git diff --check` passed. Final commit and publication checks are pending. |
| Review, PR, merge | Pending | Follow the requested branch and pull-request workflow after all results and documentation are reviewed. |

## Current Implementation Evidence

- RED: new runner tests initially failed because mode/bias configuration did not exist and the runner continued the paid grid after HTTP 429.
- GREEN: focused tests passed during implementation; final `.venv\Scripts\python.exe -m pytest -q` passed 214 tests with one existing Starlette deprecation warning.
- `.venv\Scripts\python.exe -m compileall -q src/parcha scripts`, `git diff --check`, and ignore checks for the private run outputs passed.
- Existing user-provided workshop audio and transcripts remain in ignored `var/benchmark_audio/`; no YouTube-source audio or caption text is copied into the handoff.
- The handoff includes 120 attributed CC BY 4.0 WAVs, the dataset manifest, 2,000 per-condition rows, two failed-attempt records, source/mode/codec/SNR aggregates, and per-audio hashes. The 80 YouTube-source result rows have transcript/reference/source-row text redacted.
- Private live output: `var/lab/real_audio_results.jsonl` (2,000 successful conditions; result SHA-256 is recorded in the ignored aggregate summary). Two HTTP 504 attempts and their successful retries are recorded in ignored `var/lab/real_audio_failed_attempts.jsonl`.
- Estimated usage is 4,964.864 credits for successful conditions and 4,970.2334 credits including both failed attempts, using the repository estimate of 0.2 credits/second. The configured client cannot read the provider dashboard balance.
