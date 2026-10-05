# Effort State: 005 — Lab Max Audio Duration Rejection

**Effort ID:** 005
**Reference:** `lab-max-audio-duration-rejection`
**Title:** Split Long Lab Audio at the Gnani REST Duration Limit
**Status:** in progress pending PR merge
**Started:** 2026-10-05
**Parent Effort:** `004-enterprise-telephony-compliance`

## Stage Progression

| Stage | Status | Notes |
|---|---|---|
| Requirements and failure characterization | Complete | Reproduced the historical 32.6-second request rejection: `MAX_AUDIO_DURATION_EXCEEDED`, maximum allowed 30 seconds. A 25-second slice was accepted with an empty transcript. |
| Offline regression | Complete | Added 32.6-second splitter/forecast regression and a partial-chunk-rejection regression. The tests require the entire result to remain rejected if any chunk fails. |
| Implementation | Complete pending review | Runner now sends at most 29 seconds per REST request, joins successful chunk transcripts in order, reports attempted `api_chunks`, and stops after the first rejected chunk. Forecast accounts for AMR-NB tail padding and retains source-duration credit estimates. |
| Live replay | Complete | The original 32.6-second idle recording completed as two chunks with no transcription error; output was an empty transcript and `hallucinated_word_count: 0`. Runner-calculated credit estimate: 6.5201 credits; provider billing was not inspected. |
| Real noisy speech spot check | Partial; provider throttled | Four calls on the existing 4.8-second mechanic-plus-garage-noise sample: clean and `impact_wrench` returned the same transcript; `metal_spanner` and `compressor_exhaust` were rejected with HTTP 429. See construction log. This is not a general accuracy result. |
| Audit and merge | Pending | Complete review, CI, publish PR, and update status when merged. |

## Evidence and Limitations

- Detailed run notes: [`construction.md`](construction.md).
- Regression tests: `tests/test_lab_runner.py`.
- Private live outputs: ignored `var/lab/pr15_fixed_idle.jsonl` and `var/lab/pr15_noisy_speech_results.jsonl`; no credentials were written to either file.
- The 4.8-second noisy-speech probe's first two successful transcripts contained `04:30 100` where the intended amount is ₹450, despite correctly retaining labour ₹200 and Tuesday evening. Therefore the REST duration fix resolves the 400 failure, but the real noisy estimate is not yet amount-correct. The later two requests received 429, so those noise variants have no recognition result.
- A single fixture and four calls do not establish robust real-world accuracy. Rate limiting and monetary extraction remain separate gates.
