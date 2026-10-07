# Kaam Ka Parcha — Feasibility Gates & Credit Tracking

This document records the empirical measurements, credit consumption, go/no-go decisions, and architectural fallbacks for all speech pipeline gates.

All live evaluations follow the zero-leak policy: raw recordings, private metrics, API keys, and customer identifiers are never committed. Public reporting contains only measured own-pipeline deltas with explicit N, settings, and date.

---

## Master Gate Tracking Sheet

The rows below are a plan and an evidence ledger. A dated row is a measured result only when its source artefact is committed or linked from the row. Unsupported historical results are marked not reproducible; future-dated gates remain pending until their commands are run.

| Date | Input Manifest / Hash | Settings | Credits Before / After | Numerator / Denominator | Decision | Fallback |
|---|---|---|---|---|---|---|
| **2026-10-04** | `var/gates/probe_clip.wav` (`a4c89f1e`) | Single-Call Probe: REST `transcribe` (hi-IN) + Timbre 8k $\mu$-law | 5,000.0 / 4,997.6 | 1 / 1 probe calibrated (0.20 cr/s STT, 1.2 cr TTS) | **GO (PASS)** | Rate $\le 0.35$ cr/s; grid cap 2,000 safe |
| **2026-10-05** | `data/generalization_corpus_v1.json` | Generalisation Suite | — | — | Not reproducible: no runner exists (see corrections note) | Require explicit review on ambiguous amounts or ties |
| **2026-10-05** | `data/real_world_samples/mechanic_in_garage_noise.wav` (synthesized mechanic speech mixed with recorded engine rumble) | E2E Sealed Parcha: Intake -> PDF (reported scenario; no committed output) | Not reproducible | Not reproducible | Not reproducible from committed evidence | No linked result artifact |
| *Scheduled 2026-10-06* | `data/synthcall_manifest.jsonl` | Credit Gate: 100 × 2 × 4 baseline grid forecast | TBD | Forecast / 2,000 harness cap | Pending | 60 × 2 × 3 fallback |
| *Scheduled 2026-10-07* | `var/gates/oct7_garage.jsonl` | Garage Dictation: 10 clips beside idling scooter | TBD | Exact amounts / 10 | Pending | Restrict to synthetic line degradation |
| *Scheduled 2026-10-08* | `var/gates/oct8_tts.jsonl` | Timbre 8k $\mu$-law → G.711 → Prisma | TBD | Recovered amounts / 10 | Pending | Voice sweep / pre-normalization |
| *Scheduled 2026-10-10* | `var/gates/oct10_telephony.jsonl` | Telephony short replies at 5 dB | TBD | Drops / 50; idle hallucinations | Pending | Carrier phrase / walk-up fallback |
| *Scheduled 2026-10-15* | `var/gates/oct15_bias.jsonl` | Verbatim bias A/B: 30 automotive parts | TBD | Part recovery delta / 30 | Pending | Disable bias if no gain |
| *Scheduled 2026-10-19* | `data/synthcall_manifest.jsonl` | Line Noise Sweep: 100 × 2 × 4 grid | TBD | Completed / 800 | Pending | Reduced matrix |
| *Scheduled 2026-10-19* | `var/gates/haan_ws.jsonl` | WebSocket 500 ms zero-tail flush | TBD | Recovered affirmatives / 50 | Pending | REST customer transport |

---

## 1. Credit Rate & Single-Call Probe (Task 3)

The single-call probe measures the true billing unit cost on the live Gnani platform for both Prisma STT (`hi-IN`, `format=transcribe`) and Timbre TTS (`timbre-v2.5`, `hi-IN`, `pcm_mulaw` 8 kHz) using a 4–8 second audio clip.

### Probe Execution Contract
```powershell
.\.venv\Scripts\python.exe scripts/probe_api.py --live --clip var/gates/six_seconds.wav
```
- Mandatory `--live` flag prevents accidental paid calls.
- Validates WAV header and duration ($4.0 \le \text{duration} \le 8.0$ s).
- Prompts for or accepts `--initial-balance`, `--mid-balance`, and `--final-balance`.
- Calculates STT credits/second and TTS prompt cost without logging secret keys.

### Single-Call Probe Measurements

| Date | Input Manifest / Hash | Settings | Credits Before / After | Numerator / Denominator | Decision | Fallback |
|---|---|---|---|---|---|---|
| **2026-10-04** | `var/gates/probe_clip.wav` (`a4c89f1e`) | hi-IN `transcribe`, 8k $\mu$-law Nalini | 5,000.0 / 4,997.6 | 1.2 cr STT / 6.0s (0.20 cr/s) + 1.2 cr TTS | **GO (PASS)**: Calibrated `CreditPlan` at 0.20 cr/s | Cap forecast at 2,000 credits confirmed safe |

- **Empirical Calibration Outcome**:
  - Measured STT burn rate: **0.20 credits/second** (1.2 credits for 6.0 seconds audio).
  - Measured Timbre TTS rate: **0.05 credits/character** (1.2 credits for 24-character read-back prompt).
  - Decision: **GO (PASS)**. Rate is well below the 0.35 cr/s limit, ensuring the planned 800-call evaluation sweep can run safely within the 2,000 credit cap.


### Credit Budget Forecasting Models

Total speech credits allocated: **5,000 credits**.
Budget ceiling for Line Noise Lab harness (40% reserve cap): **2,000 credits**.
Reserved app interactive headroom:
- Workshop intake reserve: 60 s
- Customer reply reserve: 300 s
- TTS read-back reserve: 100 credits

$$\text{grid\_credits} = \text{clips} \times \text{codecs} \times \text{snrs} \times \text{seconds\_per\_clip} \times \text{credits\_per\_stt\_second}$$
$$\text{total\_credits} = \text{grid\_credits} + ((\text{intake\_seconds} + \text{reply\_seconds}) \times \text{credits\_per\_stt\_second}) + \text{tts\_credits}$$

#### Candidate Grid Projections

1. **Full Grid ($100 \times 3 \times 3$):** 900 STT calls @ 6 s = 5,400 s speech
   - If rate = 0.20 credits/s: $\text{grid} = 1,080$, $\text{total} = 1,252$ credits $\implies$ **PASS** ($\le 2,000$)
   - If rate $\ge 0.35$ credits/s: $\text{grid} \ge 1,890$, $\text{total} \ge 2,116$ credits $\implies$ **EXCEEDS CAP** $\implies$ Trigger reduced grid
2. **Planned Baseline Grid ($100 \times 2 \times 4$):** 800 STT calls @ 6 s = 4,800 s speech
   - If rate = 0.20 credits/s: $\text{grid} = 960$, $\text{total} = 1,132$ credits $\implies$ **PASS** ($\le 2,000$)
   - If rate $\ge 0.39$ credits/s: $\text{grid} \ge 1,872$, $\text{total} \ge 2,112$ credits $\implies$ **EXCEEDS CAP**
3. **Reduced Fallback Grid ($60 \times 2 \times 3$):** 360 STT calls @ 6 s = 2,160 s speech
   - If rate = 0.35 credits/s: $\text{grid} = 756$, $\text{total} = 982$ credits $\implies$ **PASS**
   - If rate = 0.50 credits/s: $\text{grid} = 1,080$, $\text{total} = 1,360$ credits $\implies$ **PASS**

---

## 2. Oct 6: Credit Gate

- **Hypothesis:** Planned grid of 100 utterances across 3 codecs and 3 SNRs burns $\le 40\%$ (2,000 credits) of the initial 5,000-credit allocation.
- **Pass Threshold:** $\text{total\_forecast} \le 2,000$ credits.
- **Fallback:** Shrink matrix to $60 \text{ utterances} \times 2 \text{ codecs (G.711, AMR-NB)} \times 3 \text{ SNRs (clean, 10 dB, 5 dB)}$.

| Date | Input Manifest / Hash | Settings | Credits Before / After | Numerator / Denominator | Decision | Fallback |
|---|---|---|---|---|---|---|
| *Scheduled Oct 6* | `data/synthcall_manifest.jsonl` | 100 clips × 3 codecs × 3 SNRs | TBD / TBD | Forecasted / 2,000 cap | Pending | 60 × 2 × 3 grid |

---

## 3. Oct 7: Garage Dictation Amount Gate

- **Hypothesis:** Prisma REST `format=transcribe` on 10 scripted Hinglish lines recorded in real garage ambient noise (running scooter) recovers numeric amounts accurately.
- **Pass Threshold:** $\ge 70\%$ (7/10) amounts exact match in paise/rupees.
- **Fallback:** Drop the walk-up microphone arm from the product; restrict customer leg to telephony/synthetic line degradation.

| Date | Input Manifest / Hash | Settings | Credits Before / After | Numerator / Denominator | Decision | Fallback |
|---|---|---|---|---|---|---|
| *Scheduled Oct 7* | `var/gates/garage_10.jsonl` | REST transcribe, hi-IN, real scooter noise | TBD / TBD | 0 / 10 exact | Pending | Drop walk-up; phone leg only |

---

## 4. Oct 8: TTS Round-Trip Gate

- **Hypothesis:** Timbre `timbre-v2.5` (`hi-IN`, `pcm_mulaw` 8 kHz) read-back of total amount ("कुल ₹650"), degraded through G.711 and transcribed back via Prisma, preserves the amount and is intelligible to human raters.
- **Pass Threshold:** Amount recovered $\ge 9/10$ ($90\%$) and verified intelligible by 3 independent listeners.
- **Fallback:** Voice sweep across Nalini / alternatives; enforce pre-normalization of number strings (e.g., Hindi word expansion).

| Date | Input Manifest / Hash | Settings | Credits Before / After | Numerator / Denominator | Decision | Fallback |
|---|---|---|---|---|---|---|
| *Scheduled Oct 8* | `var/gates/tts_roundtrip.jsonl` | Nalini, 8k mulaw, G.711 round-trip | TBD / TBD | 0 / 10 recovered | Pending | Sweep voices / pre-normalize |

---

## 5. Oct 10: WebSocket Telephony Short Reply Gate

- **Hypothesis:** Telephony preset on WebSocket endpoint handles short isolated utterances ("हाँ", "नहीं") at AMR-NB 4.75 kbps with 5 dB SNR without premature cut-off or excessive dropping, and does not hallucinate during idle engine segments.
- **Pass Threshold:**
  - Drop rate $\le 10\%$ (no more than 5 dropped out of 50 clips).
  - Hallucination $\le 1$ word per clip on 20 engine-only background clips.
- **Fallback:** Re-prompt user with longer carrier phrase ("हाँ ठीक है" / "नहीं बदलो"); if drop remains $> 25\%$, fall back to walk-up mode.

| Date | Input Manifest / Hash | Settings | Credits Before / After | Numerator / Denominator | Decision | Fallback |
|---|---|---|---|---|---|---|
| *Scheduled Oct 10* | `var/gates/short_replies_50.jsonl` | WS telephony preset, AMR 4.75, 5 dB | TBD / TBD | 0 / 50 dropped | Pending | Carrier phrase / walk-up fallback |

### Written Organizer Clarification Record
- **Reference:** `organizer-reply-2026-10-10`
- **Question 1 (Filming):** Does scripted real-person roleplay count as synthetic?
  - *Response:* Pending written confirmation on Discord.
- **Question 2 (Public Deltas):** Are own-system comparative deltas permissible under the EULA without absolute competitor WER?
  - *Response:* Pending written confirmation on Discord.

---

## 6. Oct 15: Verbatim Bias A/B Gate

- **Hypothesis:** Prisma REST `format=verbatim` with domain `bias_list` (automotive spare parts and brands) at `bias_score` 1.0 and 1.5 improves part-name recognition over unbiased verbatim baseline.
- **Pass Threshold:** Measurable gain in exact-match part name retrieval on 30 test utterances.
- **Fallback:** Omit `bias_list` from the production pipeline and lab proof cards; document neutral/negative impact.

| Date | Input Manifest / Hash | Settings | Credits Before / After | Numerator / Denominator | Decision | Fallback |
|---|---|---|---|---|---|---|
| *Scheduled Oct 15* | `var/gates/bias_30.jsonl` | verbatim mode, bias_score 1.0 & 1.5 | TBD / TBD | 0 / 30 part gain | Pending | Drop bias boosting from pipeline |

---

## 7. Oct 19: Line Noise Sweep & Final Gate

- **Hypothesis:** Line Noise Lab v0 generates full evaluation matrix (100 utterances $\times$ 2 codecs [G.711, AMR-NB 4.75] $\times$ 4 noise levels [clean, 10 dB, 5 dB, 0 dB]), and zero-pad flush on WebSocket recovers terminal short response ("हाँ") with $\ge 95\%$ reliability.
- **Pass Threshold:** Complete manifest with CER and entity extraction curves; flush recovery $\ge 95/100$.
- **Fallback:** If WebSocket zero-pad flush remains unstable, route customer leg through REST turn-based endpoint.

| Date | Input Manifest / Hash | Settings | Credits Before / After | Numerator / Denominator | Decision | Fallback |
|---|---|---|---|---|---|---|
| *Scheduled Oct 19* | `data/synthcall_manifest.jsonl` | 100 utts × 2 codecs × 4 SNRs + WS flush | TBD / TBD | 0 / 100 recovered | Pending | Customer leg REST turn-based |

---

## 8. Early Gate Runner CLI & Streaming Architecture

The automated gate runner (`scripts/early_gates.py`) enforces strict pre-flight budget boundaries and evaluates speech feasibility before building user interfaces.

### CLI Usage

```powershell
# Pre-flight forecast (dry-run, exits 0, no network calls made)
.\.venv\Scripts\python.exe scripts/early_gates.py --mode garage

# Custom manifest dry-run
.\.venv\Scripts\python.exe scripts/early_gates.py --mode short-replies --manifest var/gates/short_replies_50.jsonl --max-credits 500

# Live execution with paid calls
.\.venv\Scripts\python.exe scripts/early_gates.py --live --mode garage --manifest var/gates/garage_10.jsonl --transport rest --output var/gates/garage-results.jsonl
```

### CLI Flag Reference

| Flag | Type | Default | Description |
|---|---|---|---|
| `--live` | flag | `False` | Run live paid calls against Gnani APIs. If omitted, prints forecast and exits 0. |
| `--mode` | string | *required* | Gate mode: `garage`, `tts-roundtrip`, `short-replies`, or `bias-ab`. |
| `--manifest` | Path | `var/gates/<mode>.jsonl` | Path to JSONL evaluation manifest. |
| `--max-credits` | float | `2000.0` | Maximum credit budget ceiling. |
| `--credits-per-second` | float | `0.2` | STT credit burn rate per second of audio. |
| `--remaining-credits` | float | `5000.0` | Current remaining dashboard balance. |
| `--tts-credit-reserve` | float | `0.0` | Additional credits reserved for TTS synthesis. |
| `--transport` | `rest` \| `ws` | `rest` | Speech transport mechanism for transcription. |
| `--output` | Path | `var/gates/<mode>-results.jsonl` | Destination JSONL path for structured gate results. |

### Budget Failsafes and Error Halting

1. **Pre-call Cap Validation**: Forecasted total credits are verified against $\min(\text{max\_credits}, \text{remaining\_credits})$. If forecast exceeds this cap, execution terminates before any API calls are made.
2. **Per-Call Allowance Decrement**: Before each utterance is submitted, the runner checks whether remaining allowance $\ge \text{item\_cost}$. If budget is exhausted, the loop halts immediately.
3. **HTTP 403 / 429 Termination**: On authentication failure (403) or rate limit (429), the runner halts immediately without auto-retry, recording partial results and the halt reason.

### WebSocket Telephony Client (`src/parcha/gnani_ws.py`)

- **Protocol**: `wss://api.vachana.ai/stt/v3/stream`
- **Audio Framing**: Mono 8 kHz signed-16-bit PCM chunked into 1024-byte frames (512 samples = 64 ms per frame). Chunks shorter than 1024 bytes are zero-padded to maintain frame timing.
- **Zero-Pad Silence Flush**: Appends 500 ms of zero-padded silence frames ($\lceil 500 / 64 \rceil = 8$ frames of 1024 bytes) after audio transmission to ensure the remote VAD and decoder flush terminal short utterances ("हाँ", "नहीं").
- **Telephony VAD Headers**:
  - `lang_code`: `hi-IN`
  - `x-sample-rate`: `8000`
  - `x-vad-threshold`: `0.7`
  - `x-min-speech-ms`: `200`
  - `x-min-silence-ms`: `500`
  - `x-min-segment-ms`: `100`

### Explicit Metric Scoring Helpers (`src/parcha/credits.py`)

- **Exact Amount Recovery** (`count_exact_amounts`):
  Evaluates integer rupee/paise matching between expected and predicted amounts.
  $$\text{Pass Rate} = \frac{\text{Matches}}{\text{Total Expected}} \ge 70\% \text{ (Garage)} \text{ or } 90\% \text{ (TTS Roundtrip)}$$
- **Telephony Drop Rate** (`drop_rate`):
  Identifies empty or non-speech transcripts on short confirmation utterances.
  $$\text{Drop Rate} = \frac{\text{Empty or Whitespace Replies}}{\text{Total Utterances}} \le 10\%$$
- **Engine Noise Hallucination Rate** (`hallucinated_word_rate`):
  Measures phantom words generated during pure ambient noise segments (e.g., idling scooter).
  $$\text{Hallucination Rate} = \frac{\text{Total Words Emitted}}{\text{Total Noise Clips}} \le 1.0 \text{ word/clip}$$

---

## 9. Lab Report & Guarded Public Delta Export (Task 17)

The lab report module (`src/parcha/lab/report.py`) provides structured aggregation of private laboratory sweeps and generates guarded public relative performance deltas under strict compliance with the zero-leak policy and platform EULA.

### Fail-Closed Permission Guard & Policy
Public distribution of speech evaluation data or absolute competitive benchmarks without explicit written permission violates platform policies. To prevent unauthorized benchmark leakage:
- **Written Consent Mandate**: `public_delta()` strictly enforces that `organizer_consent=True` and a non-empty `consent_ref` string (e.g., `organizer-reply-2026-10-10`) are provided. If either condition is unmet, execution terminates immediately and fails closed:
  ```python
  if not organizer_consent or not consent_ref or not consent_ref.strip():
      raise PermissionError("Public delta export requires written organizer consent and reference")
  ```
- **Competitor Benchmark Rejection**: The export engine strictly forbids and rejects any competitor mentions ("Whisper", "Google", "AWS", "Azure", "OpenAI") or comparative cross-engine claims in input rows, metadata, or output markdown. Detection raises an immediate `ValueError`.
- **Absolute Metrics Ban**: Absolute Character Error Rate (CER) and Word Error Rate (WER) metrics are forbidden in public outputs to prevent external competitive benchmarking. Only relative own-system recovery deltas are permissible.

### Paired Delta Evaluation Methodology
To eliminate confounding variability across speech samples and ambient noise acoustic conditions, public exports pair results strictly by:
$$\text{Tuple} = (\text{clip\_id}, \text{codec}, \text{snr}, \text{loss}, \text{seed})$$

1. **Condition Pairing**: Pairs baseline utterances (`variant == "bias_off"`) directly with domain-adapted utterances (`variant == "bias_1_0"`).
2. **Delta Quantification**: Evaluates exact part-name recovery delta ($\Delta \text{Part Matches}$) and exact numeric amount recovery delta ($\Delta \text{Amount Matches}$):
   $$\Delta \text{Recovery} = \text{Recovery}_{\text{bias\_1\_0}} - \text{Recovery}_{\text{bias\_off}}$$
   $$\Delta \% = \frac{\Delta \text{Recovery}}{N_{\text{pairs}}} \times 100\%$$
3. **Mandatory Audit Labels**:
   - `"measured by us"` (explicit internal attribution)
   - `"N={len(pairs)}"` (auditable sample size)
   - Date string (e.g., `2026-10-19`)
   - Complete operational settings (codec, SNR, model, score).

### Private Lab Evaluation Summary
Internal reports produced by `private_summary()` compute full diagnostic aggregates grouped by `(codec, snr, loss)`:
- Total clips evaluated ($N$)
- Mean Character Error Rate (CER) and total character counts
- Exact numeric amount matches and percentage ($\%$)
- Latency distribution statistics: mean, median ($p_{50}$), and 90th percentile ($p_{90}$) in milliseconds
- Estimated credit expenditure per condition and overall
- Non-speech / engine idle hallucination rates (hallucinated words per clip) when non-speech clips are present.

### CLI Reference

```powershell
# Generate private markdown summary report (default output: var/lab/private/report.md)
.\.venv\Scripts\python.exe -m parcha.lab.report --results-file var/lab/line_noise_results.jsonl

# Generate guarded public delta export (requires explicit consent flag and reference)
.\.venv\Scripts\python.exe -m parcha.lab.report `
    --results-file var/lab/line_noise_results.jsonl `
    --public-output var/lab/public/delta_export.md `
    --organizer-consent-recorded `
    --consent-ref "organizer-reply-2026-10-10" `
    --date "2026-10-19"
```

---

## 10. 8 kHz WebSocket Telephony Flush Experiment (Task 18)

The 8 kHz WebSocket flush probe (`scripts/ws_flush_probe.py`) isolates and measures the streaming telephony transport (`wss://api.vachana.ai/stt/v3/stream`) for short conversational acknowledgments and affirmative confirmations ("हाँ", "ठीक है", "हाँ ठीक है").

### Zero-Padding Silence Tail Strategy (500 ms / 8 Frames)
The remote telephony streaming endpoint relies on dynamic Voice Activity Detection (VAD) configured with:
- `x-sample-rate`: `8000`
- `x-vad-threshold`: `0.7`
- `x-min-speech-ms`: `200`
- `x-min-silence-ms`: `500`
- `x-min-segment-ms`: `100`

Short affirmative replies often span only 300–700 ms. If the streaming client terminates audio transmission or abruptly closes the WebSocket connection immediately after the last speech frame, the remote VAD decoder buffer fails to detect the speech-to-silence transition, cutting off the terminal syllable or discarding the utterance entirely.

To trigger reliable end-of-utterance segmentation:
1. Audio PCM is packetized into fixed **1024-byte frames** (512 samples = 64 ms per frame at 8 kHz mono signed-16-bit). Any partial final frame is zero-padded to 1024 bytes.
2. A trailing zero-pad silence buffer is synthesized:
   $$\text{Silence Frames} = \left\lceil \frac{500 \text{ ms}}{64 \text{ ms/frame}} \right\rceil = 8 \text{ frames} \quad (8 \times 1024 \text{ bytes} = 8192 \text{ bytes} \implies 512 \text{ ms})$$
3. Frames are streamed at 64 ms paced intervals (`await asyncio.sleep(0.064)`) while a concurrent background receiver task awaits intermediate events and the terminal `transcript` event with bounded timeout ($t \le 10$ s).
4. Socket teardown captures events and close codes cleanly, strictly redacting authentication credentials from execution logs.

### Transport Architectural Decision: REST Primary vs. WS Research Probe
- **REST as Primary Product Transport**: Kaam Ka Parcha uses REST (`PrismaClient.transcribe` with `format=transcribe` / `format=verbatim`) as its primary transport for the customer review and garage intake flows. In simulated browser sessions and progressive web apps, stateless HTTP multipart requests provide superior resilience against socket drops, proxy disconnects, carrier NAT timeouts, and browser tab background suspension.
- **WebSocket Telephony Preset as Research Probe**: The streaming WebSocket protocol is evaluated as an isolated research probe specifically to benchmark end-of-turn latency and affirmative recovery for direct PSTN/telephony trunking (e.g., SIP/FreeSWITCH/Twilio bridges).

### Gate Criteria & Pass Threshold
- **Evaluated Metric**: Explicit recovery numerator and denominator:
  $$\text{Recovery Rate} = \frac{N_{\text{recovered}}}{N_{\text{total}}} \ge 95\% \quad (\ge 0.95)$$
- **Terminal Affirmative Criteria**:
  An utterance passes recovery if the transcript captures the expected affirmative token (e.g., "हाँ", "haan", "ठीक है", "theek hai") without premature VAD truncation. Transcripts yielding empty strings, whitespace, or truncated noise count as failed (dropped) replies.
- **Go/No-Go Decision**:
  - **GO ($\ge 95\%$)**: Zero-pad flush verified stable; telephony streaming eligible for SIP integration.
  - **NO-GO ($< 95\%$)**: WebSocket zero-pad flush fails reliability threshold; customer conversational leg remains strictly routed through the REST turn-based endpoint.

### CLI Usage & Budget Guard
```powershell
# Pre-flight forecast and manifest validation (dry run, exits 0, zero network calls)
.\.venv\Scripts\python.exe scripts/ws_flush_probe.py --manifest var/gates/haan_ws.jsonl

# Parameterized silence tail probe across multiple durations
.\.venv\Scripts\python.exe scripts/ws_flush_probe.py --silence-ms 250,500,750 --max-credits 500

# Live paid evaluation against Gnani WebSocket endpoint
.\.venv\Scripts\python.exe scripts/ws_flush_probe.py `
    --live `
    --manifest var/gates/haan_ws.jsonl `
    --silence-ms 500 `
    --max-credits 2000 `
    --output var/gates/ws_flush_results.jsonl
```

## 11. Money-Path Safety and Benchmark v2 (Effort 009)

These dated run records use private result files under ignored `var/lab/`. They
record sample counts, credit estimates, and dry-run forecasts, not console
billing. Runner estimates are row-summed; echo totals use the runner's validated
usage accounting.
The owner-reported balance is approximately 235,000 credits; it was not read
from the account console during these runs. An internal Gramvaani telephone-speech diagnostic existed (2026-10-06); it is excluded from the project, demo and
submission under the contest data rule (no recorded calls), and its index and tooling were removed from the repo.
A separate internal mechanic-video set is likewise not part of the submission.

| Date | Reproduction reference | Output | Completed N | Credit estimate |
|---|---|---|---:|---:|
| 2026-10-06 | Amount-labelled runner settings and command in [`BENCHMARK_CARD.md`](benchmarks/BENCHMARK_CARD.md): estimates and corrections, G.711/AMR-NB 4.75, clean/0 dB, transcribe/verbatim, 1 s request spacing, 5,000 per-run forecast cap | `var/lab/v2_estimates.jsonl`, `var/lab/v2_corrections.jsonl` | 1,280 result rows | 1,141.24 row-summed credits |
| 2026-10-06 | Synthetic bias-control command in [`BENCHMARK_CARD.md`](benchmarks/BENCHMARK_CARD.md): verbatim with/without bias, clean condition, 1 s spacing | `var/lab/bias_control.jsonl` | 40 result rows | 12.86 row-summed credits |
| 2026-10-06 | `scripts/run_echo_test.py --stage screen --resume-from var/lab/echo_screen_resumed3_20261006.jsonl --request-interval-seconds 1 --output var/lab/echo_screen_resumed4_20261006.jsonl --live` | `var/lab/echo_screen_resumed4_20261006.jsonl` and matching summary | 2,886 result rows; 2,890 STT attempts | Prisma 6,147.27; Timbre accounted lower bound 6,728.30 |
| 2026-10-06 | `scripts/run_echo_test.py --stage confirm --from var/lab/echo_screen_resumed4_20261006.jsonl --request-interval-seconds 1 --output var/lab/echo_confirm_live2_20261006.jsonl --live` | `var/lab/echo_confirm_live2_20261006.jsonl` (interrupted, HTTP 503) | 1,044 rows | Prisma 3,064.78; Timbre accounted 3,384.65 |
| 2026-10-06 | `scripts/run_echo_test.py --stage confirm --from var/lab/echo_screen_resumed4_20261006.jsonl --resume-from var/lab/echo_confirm_live2_20261006.jsonl --output var/lab/echo_confirm_resumed2_20261006.jsonl --request-interval-seconds 1 --live` | `var/lab/echo_confirm_resumed2_20261006.jsonl` and matching summary (`status=complete`) | 1,080 rows (3 pairs × 120 cards × 3 conditions); 1,081 STT attempts | Prisma 3,168.85 (15,844.24 s); Timbre accounted 70,224 chars / 3,511.20 |
| 2026-10-06 | Offline scoring: `.venv\Scripts\python.exe -m parcha.lab.money_eval` with estimates/corrections result and manifest pairs | `var/lab/money_eval_after_repeat_gate.json` | 1,344 amount outcomes | No additional API credits; see private report for exact counts |

The single-recording money gate passes its zero-wrong-accept criterion by
requiring deliberate independent confirmation; this is not a recognition
accuracy claim. The transcribe cross-check is retained after an offline
one-pass counterfactual showed it can turn otherwise wrong parser accepts into
abstentions; detailed results are in private `var/lab/transcribe_crosscheck_analysis_replay.json`.

The Task 16 award decision is **Real Deal**. The owner-takes manifest is absent,
and Task 13 human listening is still pending. No absolute speech-quality metrics
are included here.

**Read-back decision (Task 16 Step 2, 2026-10-06).** Confirm-stage results on
`amr_nb_4750|0` (120 cards each, synthetic Timbre speech, one Prisma pass):
Vikrant/words 120/120, Roopesh/digits 119/120, Chitra/words 113/120. Control and
`g711|clean` were 120/120 for all three pairs. Product default is now
**Vikrant + words** (`TTS_VOICE`, `make_readback(amount_style="words")`); zero,
fractional-paise and over-range amounts fall back to digits. Nalini was not a
confirm finalist, so the tie-break did not apply. Known risk: all 8 failures
were recognizer insertions, not wrong read-back amounts — 7 from the closing
prompt "बदलाव" heard as "बार लाख" (phantom large amount) and 1 from "पार्ट एक"
heard with an extra "साठ". Item amounts and totals were correct in every failed
row (model review, private `var/lab/echo_model_verdict.md`; **human listening
pending**). Synthetic speech flatters results; this is not real-speech accuracy.
Spend is runner-estimated, not console-billed; an interrupted resume attempt
(`echo_confirm_resumed_20261006.jsonl`, 1,063 rows, no summary) was abandoned and
its small unrecorded duplicate spend is not included above. Private report:
`.\.venv\Scripts\python.exe -m parcha.lab.bench_report --echo var/lab/echo_screen_resumed4_20261006.jsonl --echo var/lab/echo_confirm_resumed2_20261006.jsonl` → `var/lab/benchmark_report.md`.

### Regional read-back echo probe (2026-10-07, A10)

`scripts/run_language_echo_bench.py --live`: Timbre speaks the product's regional read-back (digit amounts, consent line, closing prompt) over control / G.711 clean / AMR-NB 4.75 0 dB, Prisma
transcribes it in the same language (`transcribe` format), and a card passes when every amount and the total appear as digits. Synthetic speech, about 1,500 credits in total (forecast, not console billing).
Runs: Tamil 24 rows (stopped on purpose, see below; `var/lab/language_echo_ta.jsonl`); Bengali and Kannada 8 cards x 2 voices x 3 conditions = 96 rows (`var/lab/language_echo_probe.jsonl`).

| Language | Voice | Digit-recovery pass rate | Valid as an echo measure? |
|---|---|---|---|
| Bengali | Dhruva | 21/24 | Yes: Prisma returns amounts as digits ("₹22,000", "₹23,500"). Small sample (8 cards), not a ranking. |
| Bengali | Kirra | 20/24 | same |
| Kannada | Kavin / Saanvi | 13/24 and 12/24 | No: the formatter mixes number words with digits ("ಒಟ್ಟು ಇಪ್ಪತ್ತ್ಮೂರು ₹1,500"), and the Act year was read as "2,000 ಇಪ್ಪತ್ತಮೂರರ"; a digit scorer cannot tell a bad voice from a formatting choice. |
| Tamil | Brinda (first 24 rows) | 0/24 by digits | No: amounts come back partly as Tamil number words ("ஐநூற்றி ₹50" for 550, "நாற்பத்தாறாயிரத்தி ஐநூற்றி ₹50" for 46,550), so the full 5-voice x 60-card grid was not run. |

Conclusion: only Bengali yields a usable digit-based echo rate; Tamil and Kannada need a per-language number-word scorer (or the human listening labels, B1c) before a voice can be chosen on evidence.
The regional read-back therefore stays "preview" with each pack's default voice unmeasured; the Hindi default (Vikrant, words) is unaffected.
### Look-alike and lost-tail guard, fresh held-out run (2026-10-07, A2)

`scripts/run_reask_bench.py --count 100 --held-out --seed 20261010 --live --max-credits 5000 --output var/lab/reask_heldout2.jsonl`, then `--rescore`: 930 rows (fresh amounts, 2 Timbre voices, 5 conditions),
about 2,900 credits (forecast, not console billing). Synthetic speech. Pair rule with the third-recording step for look-alike number words and amounts under Rs 100:
**0 wrong settled in 930 pairs at every condition** (Wilson upper 0.41%); 76.8% settle on the first pair, 3.7% need another recording, 19.6% need a third. Single recording alone: 98.2% recovered but 13 wrong accepted (1.4%).
Offline replay of the earlier runs (free): 0 wrong settled (was 4 of 1,000 and 2 of 930); 15.2% and 18.9% of pairs need a third recording. Residual risk: look-alikes outside the flagged set (the -ty twins, e.g. पंद्रह heard as पचास; तैंतीस heard as पैंतीस seen once in the A1 run).
### Whole-estimate repeat benchmark (2026-10-07, A1)

`scripts/run_estimate_repeat_bench.py --count 100 --live --max-credits 5000 --interval 1.0` (resumed after one Prisma read timeout; retries added), then `--rescore`.
100 synthetic estimates of 2-4 priced items x 2 Timbre voices x 5 conditions = 1,000 clips, 2,000 Prisma calls; output `var/lab/estimate_repeat.jsonl`; about 4,400 credits
(forecast, not console billing). Scoring replays the saved transcripts through the real `Workflow.intake` + `confirm_estimate` (both voice directions, 1,000 estimates / 2,990 items).
Synthetic speech, so this is application-logic evidence.

| Condition | Items settled by two recordings | Wrong settled | Estimates fully settled |
|---|---|---|---|
| control | 92.5% | 0 of 598 | 89.5% |
| G.711 clean | 92.5% | 0 of 598 | 89.5% |
| AMR-NB 4.75 clean | 86.1% | 0 of 598 | 84.0% |
| G.711 0 dB | 88.6% | 0 of 598 | 86.0% |
| AMR-NB 4.75 0 dB | 63.9% | 3 of 598 | 59.5% |
| all | 84.7% | 3 of 2,990 (Wilson upper 0.29%) | 81.7% |

Recordings per estimate: 2.0 regardless of item count. The 3 wrong settles are all AMR-NB 0 dB: a lost tail ("तेईस सौ" heard twice as "तेईस") and a look-alike (तैंतीस heard twice as पैंतीस); the
under-₹100 rule in A2 (PR #36) covers the first, the second is residual risk. The benchmark found two grammar bugs, fixed in PRs #45 and #47: Prisma spellings such as उन्तीस were
dropped so "उन्तीस सौ" read as ₹100 (this settled wrong on clean audio before the fix), and a comma after "साढ़े N हज़ार" made estimates abstain (items settled in control rose from 72% to 93%).
The remaining unsettled items abstain safely, mostly Prisma's partly formatted forms such as "उन्तीस ₹100".
### Live captions and the REST length limit (2026-10-07, A9)

Live probes with one synthetic Timbre clip (10 s, Vikrant) on the realtime socket `wss://api.vachana.ai/stt/v3/stream` and on REST `/stt/v3`; roughly 100 credits (estimate, not console billing).
- **Without** `x-partials`: only one `transcript` event, after the whole phrase (about 12.8 s into a 10 s clip including the silence flush). Not useful as live captions.
- **With** the undocumented `x-partials: true` header: a `partial_transcript` about every 0.6 s (first words at about 1 s) and a `final_transcript` (not `transcript`) at segment end. Through the product's own relay (`parcha.captions.relay_captions`, real socket, 40 ms chunks): first caption at 1.03 s, last partial at 3.91 s, final at 4.59 s. The relay now handles `final_transcript` and requests partials by default (`CAPTION_PARTIALS=0` to disable).
- Display only: the final text is Prisma's formatted pass ("04:30 100 रुपये"), which is exactly why amounts still come only from the two REST passes over the finished recording.
- **REST length**: single requests of about 30 s, 41 s, 50 s and 60 s all returned HTTP 400, so the documented 60 s limit is **not** usable; the code's 29 s chunk limit (`REST_MAX_AUDIO_SECONDS`) is left unchanged.

### Follow-up hardening (2026-10-07)

All private outputs are under ignored `var/lab/`; credits are runner estimates, not console billing.

| Item | Reproduction | Result |
|---|---|---|
| Read-back prompt reword | `scripts/run_echo_test.py --stage confirm --from var/lab/echo_screen_resumed4_20261006.jsonl --output var/lab/echo_confirm_prompt2_20261007.jsonl --request-interval-seconds 1 --live` (closing prompt now "Kuch galat ho toh bataiye.") | 1,080 rows, `status=complete`. `amr_nb_4750\|0`: Vikrant/words 120/120 (120/120 on control and G.711), Roopesh/digits 119/120, Chitra/words 117/120 (was 113/120). Prisma 3,040.61 + Timbre 3,283.55 estimated credits. The phantom "लाख" insertion no longer occurs; the 4 remaining failures are one Roopesh total misheard and three Chitra "पार्ट एक" → extra ₹60 insertions. |
| Re-ask recovery (single amount, 100 amounts × 2 voices × 5 conditions) | `scripts/run_reask_bench.py --live`, then `--rescore` | 1,000 rows. Logic as first run: 73.3% recovered, 23 wrong accepted. After the transcribe-fraction fix (clock-time, "साढ़े N,000" and "N हज़ार" forms included): 96.3% recovered, 24 wrong accepted (2.4%, all at 0 dB); every clean/control row recovers. |
| Two agreeing recordings (pairs of the two voices) | `--rescore` | 93.4% settle on the first pair, 4 wrong (0.4%, Wilson upper 1.0%), 66 need one more recording. Clean and control conditions: 0 wrong in 600 pairs. All 4 wrong are one amount (₹31,000 heard as ₹21,000 in both voices at 0 dB), a systematic confusion the customer read-back must catch. |

| Held-out re-ask run (fresh amounts, none used to tune the normaliser) | `scripts/run_reask_bench.py --live --held-out --seed 20261008 --output var/lab/reask_heldout.jsonl`, then `--rescore` | 930 rows. Single recording: 96.8% recovered but 20 wrong accepted (2.2%) — still unsafe. Two agreeing recordings: 94.8% settle at the first pair, 2 wrong (0.2%, both G.711 0 dB), 46 need one more recording; clean and control conditions 0 wrong in 558 pairs. |

Offline check of "accept when both modes agree" on the saved Task 14 runs: 475 of 1,344 amounts would be accepted and 19 of those (4.0%, 10.2% at 0 dB) would be wrong, so that rule was not adopted.

### Internal mechanic-video diagnostic (2026-10-07; not part of the submission)

An internal sanity check ran Prisma over five third-party mechanic videos. Those voices are not covered by the contest's synthetic/consented-data
rule, so the set, its quotes and its numbers are excluded from the project, demo and submission, and nothing from it is cited as evidence.
Its only conclusion was a reminder: labelled real mechanic speech (the owner's own consented takes) is still the test that matters.

