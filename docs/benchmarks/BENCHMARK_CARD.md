# Money-Path Safety Benchmark Card

## Summary

This card describes the amount-labelled benchmark built for Kaam ka Parcha's
Hinglish repair-estimate workflow. It records benchmark composition and
reproduction details only. It contains no recognition scores, pass rates,
latency results, or credit totals. Result rows, transcripts, audio, and the
absolute evaluation report remain private under ignored `var/` paths.

The amount-labelled test asks whether spoken amounts can be parsed safely in
scripted estimates and corrections. Separate speech diagnostics use a public
Hindi telephone-speech evaluation slice. Neither is a representative sample of
real repair-shop conversations.

## Composition

| Slice | Composition | Availability and use |
|---|---|---|
| Scripted estimates | 120 generated estimates with 296 labelled amounts | Synthetic text and Timbre-rendered speech |
| Corrections | 40 generated one-amount correction replies | Synthetic text and Timbre-rendered speech |
| Owner takes | 80 prompts for one speaker | Internal-only planned slice; recordings and manifest are not present in this checkout |
| Stress amounts | 37 distinct rupee values, including colloquial and boundary forms | Used for deterministic parser coverage and echo screening |
| Bias control | 20 generated automotive-term prompts | Synthetic text and Timbre-rendered speech |
| Gramvaani telephone speech | 1,032 Hindi clips, approximately 2.80 hours; 291 source clips marked clipped | Speech-quality diagnostic only; no rupee labels |

The scripted slices use 13 configured Hindi Timbre voices. The fixed generation
seeds are `20261005` for estimates, `20261006` for corrections, and `20261007`
for the bias control. The stress amounts are declared in
`src/parcha/lab/amount_bench.py`. Runner degradation uses seed `20261004` by
default. The owner-takes design uses one speaker and is not available for
evaluation until the owner supplies recordings and a manifest.

## Construction

Amount labels are written first in integer paise. Estimate text uses automotive
parts, labour, delivery details, and a mixture of standard Hindi and colloquial
Hinglish amount forms. Correction prompts focus on one spoken amount. Every
manifest row is validated through the benchmark `Clip` schema before writing.
The deterministic amount parser and the model transcript passes are evaluated
separately; a matching transcript is not an independent confirmation of the
amount.

Timbre renders synthetic speech from the generated prompts. The speech runner
can evaluate clean audio, G.711, and AMR-NB 4.75 kbit/s conditions. Echo tests
score whether Prisma recovers every amount spoken by a Timbre voice in a
read-back, for digits and Hindi-word styles. Synthetic speech can make results
look better than real, spontaneous workshop speech.

The Gramvaani slice is taken from the Vistaar Hindi Gramvaani test set. Source
audio is downsampled to 8 kHz mono for the phone-channel workflow. Source
clipping labels come from the original recordings. Gramvaani clips do not have
rupee labels, so this slice cannot score amount safety. Its use is limited to
academic purposes unless the rights holder grants permission for other use.

## Licence and handling

- Generated prompts are project-created. Timbre recordings are synthetic and
  do not represent customer recordings.
- The planned IndicContextEval Hindi material is labelled CC BY 4.0 in its
  dataset documentation; it is not included in these amount-labelled or
  Gramvaani slices.
- Gramvaani source terms allow academic use; other use requires permission
  from Gram Vaani. No permission to publish benchmark results is recorded.
- Owner takes, if later supplied, are for internal evaluation only and require
  documented consent. They will not be redistributed with this repository.
- Do not commit or redistribute source audio, private transcripts, customer
  data, API credentials, or raw result rows. The metadata-only Gramvaani index
  is separate from the private audio and text manifest.

## Exclusions

The broader speech-evaluation harness excludes `i036` because its reference
does not match its audio, and excludes `y001` through `y005` because their
references are auto-caption pseudo-references. These exclusions are recorded in
`data/benchmarks/exclusions.json`. They are not substitutes for review of any
new source material. No missing owner recordings are replaced with synthetic
owner examples.

## Intended use and limits

- Use the scripted slices to test deterministic amount grammar, amount
  cross-check behavior, regression handling, and the read-back loop.
- Use Gramvaani only for general Hindi telephone-speech diagnostics. It has no
  rupee labels and is not an automotive or repair-estimate test set.
- Synthetic speech can flatter recognition and echo results. It cannot support
  a claim about spontaneous mechanic speech or real customer calls.
- The planned owner-takes slice would represent one speaker only; it is absent
  until the recordings and manifest are supplied.
- A passing transcript or agreement between two passes on one recording is not
  evidence of independent amount confirmation. The product requires a second
  deliberate recording before an amount is accepted.
- Absolute benchmark metrics are private. Public reporting requires the
  applicable written dataset and organizer permissions.

## Reproduction

Run commands from the repository root. The examples below show the Windows
PowerShell syntax used by the project. Dry runs and forecasts are the default
where supported. Live flags make paid requests and should be used only for an
authorized run with an explicit credit cap. Keep existing output files; choose
a fresh private output path before starting a new live run.

### Generate the scripted amount manifests

```powershell
.\.venv\Scripts\python.exe scripts/make_amount_benchmark.py
```

### Forecast or render synthetic speech

```powershell
foreach ($name in "estimates", "corrections", "bias_control") {
  .\.venv\Scripts\python.exe scripts/render_amount_benchmark.py `
    --manifest "data/benchmarks/amount_v2/$name.jsonl" `
    --audio-dir var/benchmark_audio/amount_v2
  # Add --live only for an authorized TTS render.
}
```

### Prepare and evaluate the Gramvaani slice

The preparation command requires a locally available source parquet file:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_gramvaani.py `
  --parquet <path-to-vistaar-gramvaani-test.parquet>
```

Forecast the runner first. The shown live command uses a per-run cap; add
`--live` only after checking the printed forecast and the applicable data-use
permissions. Before each runner forecast, read the current balance in the
account console and enter it when prompted. The runner does not query or verify
the account balance: `--remaining-credits` is only a forecast input, not a
balance check or proof that credits are available. `--max-credits` is a separate
forecast cap.

```powershell
$bias = .\.venv\Scripts\python.exe -c "from parcha.vocabulary import AUTOMOTIVE_BIAS_WORDS as W; print(','.join(W))"
$remainingCredits = Read-Host "Current credits shown by account console"
.\.venv\Scripts\python.exe -m parcha.lab.runner `
  --manifest var/benchmark_audio/gramvaani/manifest.jsonl `
  --audio-root var/benchmark_audio/gramvaani `
  --codecs none --snr-dbs clean --impulse-profiles none `
  --stt-modes transcribe,verbatim `
  --bias-words $bias `
  --request-interval-seconds 1 --remaining-credits $remainingCredits --max-credits 5000 `
  --output var/lab/gramvaani.jsonl
```

### Run amount-labelled speech sweeps

The following command is a forecast by default. Run it for the estimates and
corrections manifests. Add `--live` only for an authorized run.

```powershell
$bias = .\.venv\Scripts\python.exe -c "from parcha.vocabulary import AUTOMOTIVE_BIAS_WORDS as W; print(','.join(W))"
$remainingCredits = Read-Host "Current credits shown by account console"
foreach ($name in "estimates", "corrections") {
  .\.venv\Scripts\python.exe -m parcha.lab.runner `
    --manifest "data/benchmarks/amount_v2/$name.jsonl" `
    --audio-root var/benchmark_audio/amount_v2 `
    --codecs g711,amr_nb_4750 --snr-dbs clean,0 --impulse-profiles none `
    --stt-modes transcribe,verbatim `
    --bias-words $bias `
    --request-interval-seconds 1 --remaining-credits $remainingCredits --max-credits 5000 `
    --output "var/lab/v2_$name.jsonl"
}
```

The bias positive control uses the same clean input with both biased and
unbiased verbatim modes:

```powershell
$bias = .\.venv\Scripts\python.exe -c "from parcha.vocabulary import AUTOMOTIVE_BIAS_WORDS as W; print(','.join(W))"
$remainingCredits = Read-Host "Current credits shown by account console"
.\.venv\Scripts\python.exe -m parcha.lab.runner `
  --manifest data/benchmarks/amount_v2/bias_control.jsonl `
  --audio-root var/benchmark_audio/amount_v2 `
  --codecs none --snr-dbs clean --impulse-profiles none `
  --stt-modes verbatim,verbatim_nobias `
  --bias-words $bias `
  --request-interval-seconds 1 --remaining-credits $remainingCredits --max-credits 5000 `
  --output var/lab/bias_control.jsonl
```

### Register owner takes (internal, when recordings exist)

The current checkout has no owner recordings or owner manifest. This command
waits without creating a replacement dataset if the takes directory is empty.

```powershell
.\.venv\Scripts\python.exe scripts/register_owner_takes.py `
  --prompts data/benchmarks/amount_v2/owner_prompt_sheet.md `
  --takes-dir var/benchmark_audio/owner/takes `
  --audio-dir var/benchmark_audio/owner `
  --manifest var/benchmark_audio/owner/manifest.jsonl
```

When the files exist, add the owner result and manifest to the amount-evaluation
command above with another `--results var/lab/v2_owner.jsonl` and
`--manifest var/benchmark_audio/owner/manifest.jsonl` pair.

### Score amounts and run the read-back echo test

The scoring command needs result files and their matching manifests. Add the
owner result and manifest arguments only after the owner takes exist.

```powershell
.\.venv\Scripts\python.exe -m parcha.lab.money_eval `
  --results var/lab/v2_estimates.jsonl --results var/lab/v2_corrections.jsonl `
  --manifest data/benchmarks/amount_v2/estimates.jsonl `
  --manifest data/benchmarks/amount_v2/corrections.jsonl `
  --out var/lab/money_eval_after_repeat_gate.json
```

Echo commands forecast by default. A live screen is paid and may be resumed
only into a new output file. The confirm stage consumes a completed screen
ranking.

```powershell
.\.venv\Scripts\python.exe scripts/run_echo_test.py `
  --stage screen --output var/lab/echo_screen_resumed_20261006.jsonl --request-interval-seconds 1
# Add --live only for an authorized run; keep the source output unchanged on resume.

# Resume the interrupted 2026-10-06 screen into new outputs. Each continuation
# uses the immediately preceding JSONL and preserves it unchanged:
.\.venv\Scripts\python.exe scripts/run_echo_test.py `
  --stage screen --resume-from var/lab/echo_screen_live_20261006.jsonl `
  --output var/lab/echo_screen_resumed_20261006.jsonl --request-interval-seconds 1 --live

.\.venv\Scripts\python.exe scripts/run_echo_test.py `
  --stage screen --resume-from var/lab/echo_screen_resumed_20261006.jsonl `
  --output var/lab/echo_screen_resumed2_20261006.jsonl --request-interval-seconds 1 --live

.\.venv\Scripts\python.exe scripts/run_echo_test.py `
  --stage screen --resume-from var/lab/echo_screen_resumed2_20261006.jsonl `
  --output var/lab/echo_screen_resumed3_20261006.jsonl --request-interval-seconds 1 --live

.\.venv\Scripts\python.exe scripts/run_echo_test.py `
  --stage screen --resume-from var/lab/echo_screen_resumed3_20261006.jsonl `
  --output var/lab/echo_screen_resumed4_20261006.jsonl --request-interval-seconds 1 --live

.\.venv\Scripts\python.exe scripts/run_echo_test.py `
  --stage confirm --from var/lab/echo_screen_resumed4_20261006.jsonl `
  --output var/lab/echo_confirm_live2_20261006.jsonl --request-interval-seconds 1
# Interrupted at 1,044 rows (HTTP 503). Completed by resume into a new output:
.\.venv\Scripts\python.exe scripts/run_echo_test.py `
  --stage confirm --from var/lab/echo_screen_resumed4_20261006.jsonl `
  --resume-from var/lab/echo_confirm_live2_20261006.jsonl `
  --output var/lab/echo_confirm_resumed2_20261006.jsonl --request-interval-seconds 1 --live
# Add --live only for an authorized run after checking the forecast.
```

### Build the private aggregate report

The report CLI accepts only echo JSONL files whose matching summary reports a
complete run. Missing or interrupted echo stages are left unavailable; the
partial rows are not counted.

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m parcha.lab.bench_report
```

The default output is `var/lab/benchmark_report.md`. Keep it private. Do not
publish it or quote absolute metrics without the required written permissions.
