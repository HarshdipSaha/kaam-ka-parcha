# R9 — Deep analysis of the real-audio benchmark (PR #17, effort 006)

> Research ticket R9, part of AIDLC effort [`008-real-audio-analysis-council-spec`](../../aidlc-docs/efforts/008-real-audio-analysis-council-spec/requirements-delta.md). Analysed 2026-10-05, offline, from the private bundle [`data/benchmarks/real_audio_2026-10/`](../../data/benchmarks/real_audio_2026-10/README.md) produced by effort [`006`](../../aidlc-docs/efforts/006-real-api-real-audio-benchmark/effort-state.md). **No API calls and no credits.** Reproduce every table with:
>
> ```powershell
> py -3 scripts/analyze_real_audio_benchmark.py data/benchmarks/real_audio_2026-10 var/lab/real_audio_analysis.md
> ```
>
> **Private document.** It contains absolute CER/WER for Gnani Prisma, which `AGENTS.md` and the EULA guard keep out of public material. Only own-pipeline relative deltas may go public, and only after organiser consent. Legend: **[SPEC]** = inference, not measured.

---

## 1. Executive summary

1. **More than half of the reported error is a scoring artefact, not a recognition error.** IndicContextEval's code-mixed references write each English word twice, as a Devanagari transliteration plus its Latin original ("मॉडल model", "करंट Current"). Prisma writes one Devanagari form (Latin-token share in code-mixed hypotheses: 0.0004; in references: 0.145). Removing the Latin gloss and `<tags>` from the reference moves mean CER from **0.162 → 0.070** (transcribe) and **0.159 → 0.066** (verbatim). `summary.json`'s CER is correct by its own definition but overstates error by ~2.3×.
2. **Code-mixing is not the hard case once references are fair.** Scored CER suggests code-mixed speech is 2.4× worse (0.217 vs 0.089). Cleaned, it is *better*: 0.063 vs 0.080. Read code-mixed speech is the easiest cell (0.044). This matters for the Mixed Vibes story: do not tell anyone that "Hinglish is where Prisma struggles" from this data.
3. **Spontaneous speech is the real difficulty.** Extempore cleaned CER is ~0.095 vs Read ~0.044–0.070, roughly 1.5–2×. A mechanic's dictation is extempore, so the realistic operating point is the Extempore row, not the headline.
4. **The engine-idle noise used here is too easy to test Noise Canceller claims.** On G.711, 0 dB of recorded engine idle raises cleaned CER only 8–9% relative; 10 and 5 dB are indistinguishable from clean. Only **AMR-NB 4.75 at 0 dB** bites (+39–41% relative). Per-clip difficulty is nearly the same across conditions (Spearman ρ = 0.949 clean vs 0 dB on cleaned CER). [SPEC] Stationary low-frequency idle noise is largely removed by the 300–3,400 Hz telephone band and is well inside Prisma's telephony training. Impulse noise (wrench, spanner, compressor) was **not** in this run (`impulse_profile: null`).
5. **Transcribe and verbatim are the same recogniser with different number formatting.** 88–91% of paired conditions tie exactly. Mean ΔCER (verbatim − transcribe) is −0.003 (95% CI ≈ [−0.008, 0.000]). The visible difference is ITN: on numeral clips, transcribe emits digits in 14.3% of hypotheses and verbatim in **0%** ("हर **50** मिल" vs "हर **पचास** मिल"). Because references spell numbers as words, transcribe is *penalised for being right in a different format*. **For money, the two passes are complementary views of the same decode**: digits from transcribe, words from verbatim. This directly supports the deterministic numeral grammar on verbatim plus a two-pass agreement check from the 007 verdict, and it shows agreement will usually hold (i002: "50 60" ↔ "पचास साठ"; i020: "50" ↔ "पचास").
6. **Failures are deletions and silent empties, never insertions.** No dataset row had an insertion-heavy hypothesis (hyp/ref length > 1.4). 2.1–5.0% were deletion-heavy (< 0.6), rising slightly at 0 dB. Four rows (clip i109, AMR-NB clean and 0 dB, both modes) returned **HTTP success with an empty transcript**, while the same clip at G.711 scored 0.005 CER. For the product, an empty or truncated result must be treated as "ask again", never as "no items". Deletions are the safe failure direction for abstain-and-re-ask.
7. **No evidence that the 12-word `bias_list` inserts automotive words into non-automotive speech, and also no evidence that boosting ran at all.** Bias words appear in 41/960 hypotheses in *both* modes. Zero verbatim rows carry more bias words than both the reference and the paired transcribe output. Caveat raised in council review: per `docs/notes/02-speech-apis.md`, REST **silently ignores an invalid `bias_list`** (still HTTP 200), and entries must be single letter-only words. The bundle README says the client sent a bias score of 1.0, but **without a positive control** (audio where a biased word measurably changes the output), "no insertions" cannot be told apart from "boosting was ignored". The product uses a **65-word** list, which this run did not test (see the R8 note on distractor-size sensitivity).
8. **One label is wrong, and the workshop slice can't be scored.** Clip i036 returns one identical, coherent, unrelated sentence in all 16 conditions (CER 0.833), which points to a reference/audio mismatch in the source. Exclude it. The five workshop clips are scored against YouTube auto-captions (CER ≈ 0.64–0.75), and their text is redacted in the bundle. They can't be re-scored and say nothing reliable about recognition quality.
9. **The credit spend bought one strong dimension and three near-duplicates.** 4,964.86 estimated credits covered 125 clips × 16 conditions. Three of the four SNR levels added almost no information (finding 4), and **no row carried an amount label**, so the product's core metric (wrong amount confirmed) is still unmeasured. A v2 benchmark should spend on amount-labelled extempore utterances, AMR-NB at 0 dB and below, and impulse noise, not on more engine-idle SNR steps.
10. **Latency per pass is ~2.0 s at p50 and ~7.3–7.5 s at p95 for 6–19 s clips** (~200 ms per audio-second at p50). Intake runs two passes; if they are sequential, the mechanic waits ~4 s typically and up to ~15 s at p95. [SPEC] Running the passes in parallel halves that, but doubles the burst rate against the provider's throttle (429s seen in effort 005).

---

## 2. What was run, and what it can and cannot answer

| Item | Value (from effort 006 and the bundle README) |
|---|---|
| Audio | 120 IndicContextEval Hindi clips (CC BY 4.0; 23 professional domains; Read 80 / Extempore 40; code-mixed 68 / not 52; 6.05–19.12 s, mean 12.4 s; speaker-disjoint) + 5 private workshop clips (auto-caption pseudo-references) |
| Grid | 2 Prisma modes (`transcribe`; `verbatim` with a 12-word automotive bias list) × 2 codecs (G.711, AMR-NB 4.75) × {clean, 10, 5, 0 dB} with recorded engine-idle noise; no packet loss; no impulse profiles |
| Outcome | 2,000 successful conditions; two HTTP 504s, each recovered on one retry; ~4,964.86 credits estimated |
| **Can answer** | Prisma's broad Hindi robustness under telephony codecs and stationary engine noise; the transcribe vs verbatim difference; failure shapes; latency |
| **Cannot answer** | Amount exact-match or false confirmations (no amount labels); mechanic-domain vocabulary (Skilled Trades ≠ mechanics; 4 clips); impulse/non-stationary noise; the 65-word bias list; real phone-network audio |

---

## 3. Scoring artefacts and data quality

| Issue | Evidence | Effect | Fix |
|---|---|---|---|
| Duplicated Latin glosses in code-mixed references | 73/120 references change when a Latin token following a Devanagari token is dropped; Latin share 0.145 in references vs 0.0004 in hypotheses | Inflates code-mixed CER ~3.4× (0.217 → 0.063) | Score against a canonical single-script reference. Keep the original for audit. Report both |
| Disfluency tags (`<stammers>` etc.) | 11/120 references | Small CER inflation | Strip tags before scoring |
| ITN formatting mismatch | Transcribe digits vs word references on 28 numeral clips | Penalises transcribe for correct digits | Canonicalise numerals (words ↔ digits) in a Hinglish normaliser before scoring; score number *values* separately |
| Reference/audio mismatch | i036: identical unrelated transcript across all 16 conditions | One clip at 0.833 CER drags the means | Exclusion rule: a clip with an identical high-error output across every condition gets flagged for manual check |
| Silent empty transcripts | i109 on AMR-NB clean and 0 dB, both modes; G.711 fine | Hidden failure: HTTP 200 with no words | Runner: record `empty_transcript` as its own outcome. Product: an empty result triggers a re-ask |
| Redacted workshop text | 0/80 workshop rows have text in the bundle | Looks like 80 empty outputs if read naively | Analysis treats them as redacted, not failed |

The lab's `cer()` uses NFKC + casefold with no script or numeral canonicalisation. The stored values reproduce exactly (assertion in the script). The artefact is in the reference, not the code.

---

## 4. Headline numbers (dataset slice; private)

| Slice | Mode | n | CER scored | CER cleaned | WER scored | WER cleaned |
|---|---|---|---|---|---|---|
| all | transcribe | 960 | 0.1617 | 0.0703 | 0.2121 | 0.1489 |
| all | verbatim | 960 | 0.1586 | 0.0661 | 0.2095 | 0.1457 |
| code-mixed | transcribe | 544 | 0.2171 | 0.0630 | 0.2596 | 0.1522 |
| code-mixed | verbatim | 544 | 0.2125 | 0.0567 | 0.2559 | 0.1478 |
| not code-mixed | transcribe | 416 | 0.0893 | 0.0799 | 0.1499 | 0.1445 |
| not code-mixed | verbatim | 416 | 0.0882 | 0.0784 | 0.1487 | 0.1430 |

| Style | Code-mixed | Clips | CER scored | CER cleaned | WER cleaned |
|---|---|---|---|---|---|
| Read | no | 32 | 0.0744 | 0.0704 | 0.1263 |
| Read | yes | 48 | 0.1706 | 0.0444 | 0.1159 |
| Extempore | no | 20 | 0.1116 | 0.0931 | 0.1717 |
| Extempore | yes | 20 | 0.3208 | 0.0971 | 0.2319 |

16.7% of clips have cleaned CER = 0 and 65.8% have ≤ 0.05 (transcribe, G.711, clean). WER stays well above CER after cleaning because Hindi spelling variants (सिफारिश/सिफ़ारिश, नीती/नीति) count as whole-word errors. A Hinglish normaliser with nukta/spelling folding would narrow this [SPEC].

---

## 5. Noise and codec

| Mode | Codec | Clean | 10 dB | 5 dB | 0 dB | 0 dB vs clean |
|---|---|---|---|---|---|---|
| transcribe | G.711 | 0.0594 | 0.0603 | 0.0606 | 0.0643 | +8.2% |
| transcribe | AMR-NB 4.75 | 0.0727 | 0.0701 | 0.0740 | 0.1013 | **+39.3%** |
| verbatim | G.711 | 0.0548 | 0.0559 | 0.0563 | 0.0599 | +9.3% |
| verbatim | AMR-NB 4.75 | 0.0686 | 0.0671 | 0.0693 | 0.0970 | **+41.4%** |

*(Cleaned CER. Scored CER is in the reproducible output.)*

- At clean, AMR-NB is worse than G.711 on 38 clips, better on 17, and the same on 65 (mean +0.013, dominated by i109's silent empty).
- There is a knee between 5 and 0 dB on AMR-NB only. [SPEC] The next grid should probe AMR-NB at 0, −5 and −10 dB, plus impulse profiles, and drop 10 and 5 dB on G.711.
- **Own-pipeline delta candidates** (shareable after consent, as relative changes only):
  - AMR-NB vs G.711 at 0 dB.
  - Clean vs 0 dB on AMR-NB.

---

## 6. Transcribe vs verbatim

| Codec | SNR | ΔCER verbatim − transcribe [95% CI] | Verbatim better | Transcribe better | Ties |
|---|---|---|---|---|---|
| G.711 | clean | −0.0034 [−0.0083, −0.0004] | 9 | 3 | 108 |
| G.711 | 0 dB | −0.0032 [−0.0083, 0.0000] | 9 | 3 | 108 |
| AMR-NB | clean | −0.0029 [−0.0079, 0.0001] | 9 | 6 | 105 |
| AMR-NB | 0 dB | −0.0031 [−0.0082, 0.0000] | 10 | 7 | 103 |

All eight cells are in the reproducible output. Interpretation:
- The passes share the decode. Their difference is formatting, mostly numerals. Verbatim's tiny edge is the ITN-digit penalty, not better hearing.
- **Consequence for the money path:** the transcribe pass supplies digits, and the verbatim pass supplies number words for the grammar. Agreement between them is the expected case. Disagreement (like effort 005's `04:30 100` vs "saade chaar sau") is the rare signal that something went wrong. That is exactly when to abstain and re-ask.
- **Limitation (from the 008 council):** both passes come from one decode, so their agreement detects **formatting/ITN errors only**. A mishearing ("saade teen" for "saade chaar") or a dropped multiplier ("dhai [hazaar]") passes both passes identically. Protection against those has to come from three other places: grammar *completeness* rules (for example, a fraction word with no unit, or an amount out of range for the line item), abstaining on empty or truncated output, and the customer read-back. Agreement is a cheap guard, not independent verification.
- **Consequence for cost:** the second pass costs a full extra 0.2 credits/s and ~2 s for almost no extra recognition. It earns its cost only through the number cross-check. [SPEC] If the grammar reads amounts reliably from verbatim alone, a single verbatim pass plus a targeted transcribe pass on the amount span is an option worth measuring.

---

## 7. Bias list, failure shapes, latency

- **Bias list:** 41/960 hypotheses contain a bias word in each mode, and none look like bias-driven insertions. Boosting is unverified (no positive control; REST silently ignores invalid lists). Untested: the product's 65-word list.
- **Failure shapes:** CER > 0.5 in 2.5–4.2% of rows. Deletion-heavy rows make up 2.1–5.0% and insertion-heavy rows 0%.
  - Worst clips by cleaned CER: i036 (label mismatch), i034, i017, i050 (extempore, domain jargon: "हाइपर कमोडिटी" for "Hyper Competitive"), and i109 (silent empty on AMR).
- **Latency (per pass):**

  | Mode | Codec | p50 ms | p95 ms | max ms |
  |---|---|---|---|---|
  | transcribe | G.711 | 2,010 | 7,514 | 9,589 |
  | verbatim | AMR-NB | 1,972 | 7,443 | 13,079 |

---

## 8. Implications

| For | Implication |
|---|---|
| The 007 verdict | **Strengthened:** money from a deterministic grammar on verbatim, agreement with transcribe's digits, abstain on disagreement or empty output. **Weakened:** "W3: no real recordings" (real Hindi now exists, but not mechanic speech and not amount-labelled). **Changed:** credit assumptions (one key spent; ten more exist) |
| Line Noise Lab | Add reference canonicalisation and numeral canonicalisation, a silent-empty outcome, a label-mismatch flag, extempore stratification and impulse profiles. Cut redundant SNR steps |
| Noise Canceller claim | Can't rest on engine-idle results. The only real degradation is AMR-NB at 0 dB. Needs impulse noise and real phone calls |
| Mixed Vibes claim | Fair scoring shows code-mixed Hindi is handled well. The open risk is spontaneous speech and numbers, not code-mixing |
| Public material | Absolute numbers stay private. Candidate relative deltas: codec and SNR within our own pipeline, and later the false-confirmation delta from the money path |

---

## 9. Method notes

- The script mirrors `parcha.lab.metrics` (NFKC + casefold for CER; punctuation-stripped tokens for WER) and asserts equality with stored CER on all 1,920 dataset rows.
- Cleaning drops a Latin-script token that directly follows a Devanagari token, and strips `<...>`/`[...]` tags. Hypotheses are never modified.
- Confidence intervals are clip-level bootstraps (2,000 resamples, seed 7). Clips are the unit, since the 16 conditions per clip are not independent.
- Numeral clips are references containing Hindi number words or digits (28/120). Bias detection uses the 12 Latin bias words plus common Devanagari spellings.
