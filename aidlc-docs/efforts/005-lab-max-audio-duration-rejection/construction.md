# Effort 005: Construction Log

**Date:** 2026-10-05
**Scope:** Reproduce and fix `MAX_AUDIO_DURATION_EXCEEDED` in the Issue #7 transient-noise lab runner.

## Reproduction

The live matrix used the recorded `data/real_world_samples/car_engine_idle_16k.wav` fixture (32.6 seconds). The REST API response from the pre-fix probe was:

```json
{"success":false,"error":{"type":"MAX_AUDIO_DURATION_EXCEEDED","message":"Audio duration exceeds maximum allowed duration of 30 seconds"}}
```

All 24 calls in that earlier matrix used the same over-limit recording, so all 24 were rejected before the speech recognizer evaluated the audio. This was a request-size error, not evidence of an API outage. A direct request with a 25-second trim succeeded and returned an empty transcript.

## Change

- Added a 29-second REST chunk ceiling for normalized mono 8 kHz PCM in `src/parcha/lab/runner.py`.
- Split degraded audio into chunks after applying noise, impulse, codec, and packet-loss conditions; submit chunks in order and concatenate non-empty transcript pieces.
- Record attempted `api_chunks` for each row and count chunks in the preflight request forecast, including conservative AMR-NB frame-padding allowance. Credit forecast continues to use original clip duration times grid conditions.
- If any chunk raises `GnaniError`, stop submitting later chunks, set the aggregate transcript to `null`, and retain the provider error. This avoids compounding spend or throttling for an already rejected row and prevents partial audio from being scored as complete.
- Added offline regression coverage for a 32.6-second clip and for one chunk failing with HTTP 429.

## Validation

### Offline

- Before implementation, the new 32.6-second regression failed because forecast reported one REST call rather than two.
- Focused runner tests after implementation: **7 passed**, with one existing Starlette/httpx deprecation warning.
- Full suite: **196 passed**, with one existing Starlette/httpx deprecation warning.

### Live original failure replay

- Audio: `car_engine_idle_16k.wav`, 32.6 seconds.
- Grid: one G.711 clean condition; forecast was two REST calls and 6.52 credits.
- Result: two chunks, no provider error, empty transcript, zero recognized words for this stationary-noise sample; runner-calculated credit estimate: 6.5201 credits. Provider billing was not inspected.
- This confirms the original 400 was caused by exceeding the REST duration ceiling. It does not test recognition quality on speech.

### Noisy speech spot check

- Audio: `mechanic_in_garage_noise.wav`, 4.8 seconds (existing synthesized mechanic speech mixed with recorded Volvo engine rumble).
- Four G.711 calls: clean, `impact_wrench`, `metal_spanner`, and `compressor_exhaust`; forecast credit estimate 3.84 credits. Provider billing was not inspected.
- Clean and `impact_wrench` returned: `फ्रंट ब्रेक पैड 04:30 100 लेबर 200 मंगलवार शाम तक`.
- The intended amount in this demonstration phrase is ₹450 and labour is ₹200. The returned `100` is wrong for the brake-pad item. This is an observed real failure of estimate accuracy; duration chunking does not fix recognition or money extraction.
- `metal_spanner` and `compressor_exhaust` returned HTTP 429; they are rejected calls, not zero hallucinations. HTTP 429 means the server is rate limiting requests ([RFC 6585, section 4](https://www.rfc-editor.org/rfc/rfc6585.html#section-4)); the generic client stores only the status and does not expose the response body or `Retry-After` header, so the provider-specific policy and wait time remain undetermined. Two of four calls succeeding shows the service was not wholly down during the probe.
- Public web search found the Vachana STT overview but no primary endpoint reference documenting 30-second limits or 429 semantics. The duration limit above is based on the direct API response.

Live outputs are ignored under `var/lab/`. No key or authorization header was logged.
