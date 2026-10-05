# Requirements Delta: Effort 006 — Budgeted Real-Audio API Benchmark

**Effort ID:** 006
**Reference:** `real-api-real-audio-benchmark`
**Date:** 2026-10-05
**Baseline:** `aidlc-docs/inception/requirements.md`
**Parent:** `004-enterprise-telephony-compliance`

## Context

The product has mostly been evaluated with synthetic speech and a small number of live API calls. The user requested a diverse real-audio benchmark using their converted workshop videos and public Hindi data, with all work recorded in AI-DLC. The user initially set a 4,000-credit planning limit, then explicitly waived that limit and stated they have ten additional 5,000-credit keys. The last known provider balance (4,990) predates later calls; current balance is unknown and the API does not expose it through the configured client.

## Requirements

- **FR-006.1 — Diverse Speech Sources:** Use a documented, licensed Hindi benchmark with speaker-disjoint sampling across professional domain, speech style, and code-mixing strata. Keep the user-provided YouTube-source workshop clips as a separately labeled, exploratory subset whose captions are pseudo-references, not human gold.
- **FR-006.2 — Reproducible Measures:** Record dataset/source, model mode, audio degradation, latency, CER, punctuation-normalized WER, and task amount match only where a trusted amount label exists. Preserve per-clip outputs privately under ignored `var/`.
- **FR-006.3 — Live API Budget Guard:** Forecast the full request grid before sending requests. Bound estimated total attempts at 5,000 credits for the configured key using the repository's 0.2 credits/second rate. Stop the active process on the first provider error, retain the failed attempt, and resume only from a matching run signature after reviewing a transient failure; do not retry provider errors in a loop.
- **FR-006.4 — Audit Trail:** Record source attribution, manifest hash, exact configuration, preflight estimate, live outcomes, failures, limitations, and validation in this effort. Keep credentials out of Git. The private handoff may include attributed CC BY 4.0 dataset audio/results; keep YouTube-source media and its caption/transcription text out until redistribution rights are verified.

## Constraints and Limits

- The 5,000 limit is enforced by the local forecast/runner using the repository's estimated rate. It is not a provider-side credit cap. Provider dashboard balance remains unknown unless separately checked by the user. The user has authorized use of the configured real API key and states that additional keys are available; additional keys were not copied into the repository or environment.
- Public dataset findings may support broad Hindi speech robustness observations, not automotive repair accuracy. Skilled Trades rows are not assumed to be mechanic speech.
- User-provided YouTube audio is for this requested private evaluation only. Captions are noisy automatic references. Do not publish or commit its audio or caption text without source-specific redistribution permission; do not claim human-verified gold labels.
- Each active process stops on a 429 or any other API failure. A reviewed one-time retry after HTTP 504 was used for this run; the final log keeps both failed attempts separately and confirms each corresponding condition later succeeded. Offline test success does not establish recognition quality.
