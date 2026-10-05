# Construction Log: Effort 006

Date: 2026-10-05
Branch: `eval/real-world-speech-benchmark`

## Research and Source Qualification

- Read the project gates/demo guidance and searched primary dataset cards, papers, and source terms. Details and source links: [`docs/research/real_audio_benchmark_sources_2026-10.md`](../../../docs/research/real_audio_benchmark_sources_2026-10.md).
- Recommended source: `ai4bharat/IndicContextEval`, Hindi split, CC BY 4.0. The dataset contains professional domains, read/extempore speech, code-mixing metadata, and speaker IDs. `Skilled Trades` is a domain tag, not a guarantee of vehicle-repair content.
- Public source use is distinct from the user-provided YouTube-source clips. The latter will be labeled exploratory and scored against auto-captions as pseudo-references.
- Existing `var/benchmark_audio/indiccontext/pages/` metadata cache covers offsets 0–500 and 1200–1800 (1,300 rows). Aggregate in that cached subset: 23 domains; 743 Read / 557 Extempore; 893 code-mixed / 407 non-code-mixed; 1,088 utterances in the 6–22s target band. Only two sampled Skilled Trades rows are Extempore+code-mixed in those pages, so no claim of mechanic-specific coverage is justified.

## Implementation and Offline Verification

- Added runner mode selection (`transcribe`, `verbatim`), optional verbatim bias terms, request spacing, forecast accounting by mode, and a stop-after-first-provider-error behavior.
- Added punctuation-normalized WER beside the existing CER, and source/stratum metadata in output rows. Amount matching is null when no trusted expected amount exists.
- Added deterministic IndicContextEval row selection with duration filtering, domain/style/code-mixing strata, and one selected utterance per speaker. Added a downloader/preparer that caches only selected audio and writes artifacts under `var/`.
- TDD: added regression tests before implementation. The mode/bias test failed on the unsupported config; the 429 test failed because the original runner made four calls. Both pass after the implementation.
- Focused command: `.venv\Scripts\python.exe -m pytest -q tests/test_lab_metrics.py tests/test_lab_runner.py tests/test_real_audio_dataset.py` — 18 passed, 1 existing Starlette deprecation warning.
- Syntax command: `.venv\Scripts\python.exe -m compileall -q src/parcha/lab scripts/prepare_indiccontext_benchmark.py` — passed.

## Corpus Preparation and Safety Finding

- Refreshed the official dataset viewer metadata and verified all 3,110 Hindi rows. Selected 120 clips from 120 speakers, covering all 23 domains, Read and Extempore styles, and both code-mixing values. The 6–22 second sample has min 6.05s, mean 12.31s, max 19.12s. Manifest SHA-256: `d58ae930f7cac2d91cda54e258b1851294064ab3797ffe53fb80a2a5593f574b`.
- Prepared five user-provided video segments, one per video; 11.21–17.04s, mean 14.86s. They are labeled auto-caption pseudo-references with no trusted amount labels. Manifest SHA-256: `6231a9dfaf5a6338c0668f492b9e0850e6da4963a7c8dca67fe9fc18cf1b9703`.
- Combined private manifest has 125 rows (120 dataset references, 5 auto-caption references), validated audio paths, SHA-256 `25bd513da01b9a81517808ce9a1408f6026932f55bdb6a2164e018a4bb253082`.
- Debugging found FFmpeg's streamed WAV header can declare `2^31-1` frames while containing a short valid PCM payload. Both the dataset duration validator and runner forecast now count actual decoded frames; regression tests reproduce this header.
- The user superseded the initial 4,000-credit planning limit, stating ten additional 5,000-credit API keys are available. This full grid uses a local estimate cap of 5,000 credits; it remains serial and stops on the first provider error.
- Full-grid preflight: 125 clips × 2 modes × 2 codecs × 4 SNR conditions = 2,000 conditions; 24,824.3 source seconds; projected 4,964.86 credits at 0.2 credits/second. Recorded engine-idle background noise is used for the non-clean SNR conditions; no transient impulse profiles are enabled.

## Live Runs

- The paid sweep ran serially with a one-second request interval through the configured `.env` credential. The preflight grid was 125 clips x 2 STT modes x 2 codecs x 4 SNR levels = 2,000 conditions, estimated at 4,964.86 credits before calls.
- The first process completed 102 conditions before local audio preprocessing exposed a peak-clipping issue in the 0 dB mix. The failing condition had not reached the API. `mix_at_snr` was corrected to apply common gain to the complete mix, preserving SNR; the regression test covers this case. The saved 102 conditions were validated and resumed without duplicate calls.
- The provider returned HTTP 504 twice during later processes: `i089 / transcribe / AMR-NB 4.75 / 10 dB` and `i108 / verbatim / G.711 / clean`. Each active process stopped on its first provider error. The failed-attempt rows were preserved separately under ignored `var/`, then each missing condition was retried once under the matching run signature; both retries succeeded.
- Final result: 2,000 unique successful condition rows, exactly 16 per clip; 2,000 successful API requests; two HTTP 504 attempts plus two successful retries (2,002 total requests); zero active error rows in the successful-results file. The generated private summary validates all 2,000 unique keys and confirms both failed-attempt keys succeeded on retry.
- Estimated usage from successful conditions is 4,964.864 credits. Including both failed attempts at the same 0.2 credits/second estimate gives 4,970.2334. These are local estimates, not a dashboard balance or verified provider invoice. The configured client cannot report current balance. No additional API keys were loaded or rotated.
- Input manifest SHA-256: `d097047e56913147c4a9120e33a86513bf66f11a958300f76b317373197c53b3`. Private result SHA-256: `fece463510203786ddef26e4357fec9239112a7ae3a2bee1c3411eb6b5a18153`.
- Private handoff bundle: `data/benchmarks/real_audio_2026-10/` (26,972,626 bytes). It contains the 120 CC BY 4.0 WAVs with attribution, sample manifest, audio SHA-256 list, 2,000 condition rows, two failed-attempt rows, and grouped metrics. The 80 YouTube-source condition rows retain their conditions and scores, but source-row IDs and transcript/reference text are redacted. The five YouTube-derived WAVs, captions, and unredacted result rows remain only in ignored `var/` because no source-specific redistribution permission is recorded.
- The complete unredacted run output, private grouped aggregate, and raw user-provided audio remain under ignored `var/`. No public report was generated: there is no recorded organizer written-consent reference, and this run does not provide a matched own-pipeline relative delta. The private repository's JSON handoff contains the detailed aggregates for teammate review.
- Slice limitations: IndicContextEval is broad professional Hindi, not a mechanic benchmark; five private workshop clips are scored against YouTube auto-captions, which are noisy pseudo-references; no slice has trusted repair-amount labels. Do not use these results to claim safe amount extraction or mechanic-domain accuracy.
