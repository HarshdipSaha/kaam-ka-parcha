# Kaam Ka Parcha — Feasibility Gates & Credit Tracking

This document records the empirical measurements, credit consumption, go/no-go decisions, and architectural fallbacks for all speech pipeline gates.

All live evaluations follow the zero-leak policy: raw recordings, private metrics, API keys, and customer identifiers are never committed. Public reporting contains only measured own-pipeline deltas with explicit N, settings, and date.

---

## Master Gate Tracking Sheet

| Date | Input Manifest / Hash | Settings | Credits Before / After | Numerator / Denominator | Decision | Fallback |
|---|---|---|---|---|---|---|
| *Pending* | `var/gates/probe_clip.wav` | REST `transcribe` (hi-IN) + Timbre 8k mulaw | Pending live run | Pending / 1 probe | Pending | Reduce grid if > 2,000 credits |
| *Pending* | `data/synthcall_manifest.jsonl` | Oct 6 Credit Gate: 100 × 3 × 3 grid | Pending | Total credits / 2,000 cap | Pending | Shrink to 60 × 2 × 3 grid |
| *Pending* | `var/gates/oct7_garage.jsonl` | Oct 7 Garage Dictation: 10 clips beside scooter | Pending | Exact amounts / 10 | Pending | Drop walk-up arm; phone leg only |
| *Pending* | `var/gates/oct8_tts.jsonl` | Oct 8 TTS Round-Trip: 8k mulaw → Prisma | Pending | Amount recovered / 10 | Pending | Sweep voices / pre-normalise text |
| *Pending* | `var/gates/oct10_telephony.jsonl` | Oct 10 WS Telephony: AMR 4.75 + 5 dB (50 clips) | Pending | Dropped replies / 50 | Pending | Prompt "haan theek hai" / walk-up |
| *Pending* | `var/gates/oct15_bias.jsonl` | Oct 15 Verbatim Bias A/B: 30 parts (1.0 & 1.5) | Pending | Bias gain / 30 | Pending | Drop bias from pipeline |
| *Pending* | `data/synthcall_manifest.jsonl` | Oct 19 Line Noise Sweep: 100 × 2 × 4 grid + WS flush | Pending | Turn recovery / 100 | Pending | Customer leg REST turn-based |

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
| *Awaiting live execution* | `six_seconds.wav` | hi-IN `transcribe`, 8k mulaw Nalini | TBD / TBD | Δ credits / duration (s) | Calibrate `CreditPlan` | Cap forecast at 2,000 credits |

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
