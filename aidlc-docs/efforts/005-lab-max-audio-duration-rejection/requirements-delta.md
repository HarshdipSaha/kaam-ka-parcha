# Effort 005: Lab Handling for Gnani REST Audio Duration Rejection

**Effort ID:** 005
**Reference:** `lab-max-audio-duration-rejection`
**Parent:** `004-enterprise-telephony-compliance` / Issue #7
**Started:** 2026-10-05

## Problem

The transient-noise lab submitted `data/real_world_samples/car_engine_idle_16k.wav` (32.6 seconds) as one request to Gnani's `/stt/v3` REST endpoint. The provider rejected every sweep condition before recognition because the request exceeded 30 seconds. The exact observed response was:

```json
{"success":false,"error":{"type":"MAX_AUDIO_DURATION_EXCEEDED","message":"Audio duration exceeds maximum allowed duration of 30 seconds"}}
```

The resulting rows were API rejections, not successful empty transcriptions and not evidence that the service was unavailable. A 25-second version of the same stationary engine recording was accepted and returned an empty transcript, consistent with a non-speech clip.

## Requirements Delta

1. Never submit a lab REST request longer than the provider's 30-second ceiling. Keep a margin and split audio at 29 seconds.
2. Preserve chronological chunk order and join successful chunk transcripts into one result row per clip/condition.
3. If any chunk is rejected, mark the whole clip/condition as rejected (`transcript: null` plus an error); never score a partial transcript as a complete clip or report it as zero hallucinations.
4. Forecast the number of REST requests after chunking, including codec frame padding at chunk boundaries, while estimating credit from source audio duration and degradation-condition count.
5. Validate with offline regressions and a budget-capped live replay of the previously rejected real recording. Keep live run output under ignored `var/`; do not publish credentials or claim general recognition accuracy from one clip.

## Out of Scope

- Changing production intake chunking or claiming arbitrary-duration production support.
- Treating a single recording as a general noisy-speech benchmark.
- Adding automatic retries for provider throttling; the live probe observed HTTP 429 on two later calls. HTTP 429 denotes rate limiting under [RFC 6585, section 4](https://www.rfc-editor.org/rfc/rfc6585.html#section-4), but the generic client did not expose this provider's response body or rate-limit headers, so its precise policy and retry interval remain unknown.
