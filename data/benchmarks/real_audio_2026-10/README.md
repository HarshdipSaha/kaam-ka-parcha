# Real-audio benchmark bundle (2026-10)

This private handoff bundle contains the 120-clip Hindi subset of AI4Bharat's IndicContextEval that was used in the live API sweep, along with source references, per-condition measurements, and two failed-attempt records. The five user-provided YouTube-source clips were used locally, but their audio and caption/transcription text are not bundled because source-specific redistribution permission is not recorded. The 80 corresponding condition rows remain in `results.jsonl` with their audio-text and source-row fields redacted; all other metrics and condition metadata are retained.

This detailed handoff is intended for the current private repository. Remove the evaluation exports before making the repository public or otherwise redistributing them; the guarded public reporting requirements still apply.

## Attribution and license

Source: AI4Bharat, [IndicContextEval](https://huggingface.co/datasets/ai4bharat/IndicContextEval), Hindi split, licensed CC BY 4.0. Paper: [arXiv:2606.19157](https://arxiv.org/abs/2606.19157). License: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). This bundle redistributes a 120-utterance subset and its reference text with attribution. Audio was resampled/normalized to mono 8 kHz PCM for the benchmark; the source references are preserved in `manifest.jsonl`. This redistribution does not imply endorsement by AI4Bharat.

The manifest contains 120 speaker-disjoint clips spanning the selected sample's 23 professional domains, both Read and Extempore styles, and both values of the code-mixing flag. Speaker IDs are stored as truncated SHA-256 hashes. The WAV files are listed in `audio_sha256.json`.

## Run record

- 125 source clips were evaluated locally: 120 licensed dataset clips and five private YouTube-source clips.
- Grid: two Prisma modes (`transcribe`, `verbatim`), two codecs (`g711`, `amr_nb_4750`), clean / 10 / 5 / 0 dB SNR, no frame loss, no impulse profiles.
- API: Gnani Prisma REST v3 (`/stt/v3`), language `hi-IN`. The client does not record an explicit served model build/version. Verbatim requests use the 12 automotive bias words in `results.jsonl` at the client default bias score of 1.0; transcribe requests have no bias list.
- 2,000 unique conditions succeeded and were each recorded once in `results.jsonl`. Two HTTP 504 attempts are recorded in `failed_attempts.jsonl`; both conditions later succeeded on a single retry.
- Requests were serial with a one-second interval. The local usage estimate is 4,964.864 credits for successful conditions and 4,970.2334 including both failed attempts, using 0.2 credits per source-audio second. This is an estimate, not a provider billing statement or dashboard balance.
- `summary.json` groups CER, WER, latency, condition counts, and estimated usage by source, reference type, mode, codec, and SNR. YouTube-derived reference and hypothesis text is withheld from the bundle, so that slice cannot be independently rescored from this export.

The IndicContextEval subset is broad professional Hindi, not a mechanic-specific corpus. The five YouTube-source clips used automatic captions as pseudo-references, not human gold labels. No sample has a trusted repair-amount label; the run does not measure amount-extraction accuracy or establish safe monetary transcription.
