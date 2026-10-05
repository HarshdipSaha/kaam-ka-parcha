# Audit: Effort 006

**Status:** live sweep complete; final tests and publication workflow pending
**Date:** 2026-10-05

## Scope and controls

- User authorized real API evaluation, initially selected a 4,000-credit maximum, then explicitly waived that planning cap and stated ten additional 5,000-credit API keys are available.
- Local runner cap and forecast use the repository estimate of 0.2 credits per source-audio second. This is not a provider-side limit; current dashboard balance is unknown.
- Live requests were serial with a one-second interval. Each active process stopped at its first provider error. Two HTTP 504 attempts were retained in the private failure log; after checking the transient failure and validating the saved run signature, each missing condition was retried once and succeeded.
- The private handoff contains only the attributed CC BY 4.0 Hindi audio and source text. It includes the complete condition metrics, but redacts the five YouTube clips' audio, captions, source-row IDs, and transcript/reference text because redistribution permission is not recorded. Full local material remains under ignored `var/`; `.env` and API credentials are never committed.
- Public dataset results are not mechanic-domain accuracy claims. User-provided YouTube-derived results use auto-caption pseudo-references and remain a separate exploratory slice.

## Evidence

Dataset preparation complete: 120 CC BY 4.0 Hindi clips (120 distinct speakers, 23 domains, Read/Extempore, both code-mixing values), plus five private user-provided workshop segments with auto-caption pseudo-references. Combined manifest has 125 clips; its SHA-256 is recorded in the construction log. The grid forecast is 2,000 conditions, 24,824.3 source seconds, and 4,964.86 estimated credits.

## Findings

The completed grid contains 2,000 unique successful conditions and 2,000 successful API requests: 120 dataset references and five auto-caption references, each across two STT modes, two codecs, and four SNR levels. There are zero active error rows in the final success file. Two HTTP 504 requests failed on their first attempt; both were retried once and succeeded. The private aggregate summary confirms exactly 16 successful conditions per source clip and records the result-file hash. Estimated usage is 4,964.864 credits for successful conditions and 4,970.2334 including both failed attempts. Current provider balance and invoice usage were not available through the configured client.

The complete local grouped summary is stored at ignored `var/lab/real_audio_summary.json`. The private handoff copy is `data/benchmarks/real_audio_2026-10/summary.json`, with the curated results at `results.jsonl` and licensed audio in `audio/`. The guarded public exporter was not run because there is no recorded organizer written-consent reference and these results do not form a matched own-pipeline relative delta.

## Limitations

The benchmark's Hindi corpus is broad professional speech, not verified automotive speech. The five private workshop clips use automatic YouTube captions, so their references are noisy and not human gold. No sample has trusted repair-amount labels, so amount extraction accuracy is unmeasured. Do not claim mechanic-domain accuracy or safe monetary extraction from this run. The two 504 retries recovered, but the predecessor effort's separate four-request garage probe still had two HTTP 429 failures and amount errors in its successful transcripts. Provider billing remains estimated, and the configured API client could not confirm balance changes.
