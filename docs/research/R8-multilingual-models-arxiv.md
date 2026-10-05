# R8 — What international multilingual models and LLM error-correction papers teach Kaam ka Parcha

> Research ticket R8 for the Gnani "Great Indian AI Internship Challenge" (deadline 10 Nov 2026), part of AIDLC effort [`007-gpu-sprint-multilingual-council`](../../aidlc-docs/efforts/007-gpu-sprint-multilingual-council/requirements-delta.md). Researched 2026-10-05. Papers were discovered with the `arxiv` skill (arXiv export API through `search_arxiv.py` and boolean `ti:`/`abs:` queries) and read by five parallel reader agents, one per cluster, from arXiv HTML/PDF full text. **No Gnani API was called and no credits were spent.** Every number below is the paper's own result on the paper's own data, not a measurement of our pipeline. Legend: **[SPEC]** = our inference, not a published result; **[VERIFY]** = number read through a summarising fetch or flagged by the reader as uncertain; re-check against the paper's table before quoting it anywhere.

---

## 1. Executive summary

1. **Use Evon only as a constrained arbiter between Prisma's two passes. It must not rewrite transcripts freely.** Zero-shot free generation from a single hypothesis made ASR *worse* (LibriSpeech test-other 6.90 → 8.25 WER with 1-best only; 2307.04172 Table 6). Frozen mid-size open LLMs also degraded output (OpenLLaMA-13B: WSJ 11.87 → 13.32; 2309.15649 Table 3). Snapping output to the nearest hypothesis or selecting a hypothesis "reduces substitution errors without increasing deletion errors" (2307.04172). Keeping heterogeneous sources in **separate labelled prompt fields** beat pooling them (14.2 vs 23.3 WER; DualHyp, 2510.13281 Table 8). That matches our `format=transcribe` and `format=verbatim` passes.
2. **Treat disagreement between the passes as our confidence signal.** Prisma exposes no N-best or confidences. RobustGER (2401.10446) turns hypothesis disagreement into a noise embedding, and its gains track that signal. [SPEC] If the normalised passes agree, keep the value untouched. If they disagree, Evon may choose a candidate or abstain, and the read-back stresses that field for the customer.
3. **No paper fixes the case where both hypotheses are wrong.** On radio-degraded audio, correction gained at most 5.5% (RATS, 2401.10446). DualHyp's failure appendix shows the LLM inventing a value found in no hypothesis ("december" from a "november" context). None of the 45 papers treats money amounts as entities. Our one observed failure, `04:30 100` for ₹450 (effort 005), is *not* that case. The transcribe pass was wrong, but the verbatim pass held the right amount; the current Groq extractor chose it. That is the "one pass right, one wrong" case where selection can help. How often real noisy speech instead puts *both* passes wrong is unmeasured (Q1 in §10). **Amounts need a deterministic Hinglish number grammar plus abstention, with the customer's voice confirmation as the final check.** That covers both cases, and it makes the product's read-back loop the right architecture, not a workaround.
4. **For part names, retrieve then select over a closed lexicon.** Phonetic top-3 retrieval with the LLM choosing among candidates cut entity CER 18–34% relative (2602.12287). Phonetic filtering plus LLM revision cut entity WER 32.3 → 22.7 with non-entity WER unchanged (2506.10779). **Giving the LLM the full context raised entity WER to 43.4%** because it hallucinated (same paper). Entity lists can make speech models emit only the listed entities, words that were never spoken (2507.05727). Long bias lists with distractors broke speech LLMs (Yodas 4.17 → 27.92 error on bias words; 2608.05759). Our verbatim-pass `bias_list` needs size A/B testing and cross-checking against the transcribe pass.
5. **The international-model lesson for a 40 GB GPU: curate data, don't change the model.** Continued pre-training and vocabulary extension cost 100B+ tokens and ~10²¹ FLOPs (Swallow 2404.17790; Nemotron-Hindi 2410.14815). Vocabulary extension buys speed, not quality: Swallow's summarisation fell 5–15%. The levers that transfer are Aya Expanse's **multi-teacher generation with an arbiter** (+9.1 win-rate points; 2412.04261 Fig. 3), Airavata's **round-trip filter** (back-translate, keep chrF++ ≥ 50; 2401.15006), Nemotron-Hindi's **transliteration for Hinglish coverage**, and Aya's **data cards and three-tier evaluation** (2402.06619). [SPEC] In our domain the arbiter can be deterministic: line items sum to the total, amounts are integer paise, the date is valid, and the output language is correct.
6. **Keep numbers out of every text generator.** IndicTrans2's first human evaluation found "poor performance in dealing with … dates, numbers", and v2 wraps them in `<dnt>` tags so they are copied verbatim (2305.16307 §5.2). Generating Indic text degrades much more than understanding it (PaLM-2-L English→X 56.9 → 41.9 chrF from high- to low-resource languages vs X→English 68.2 → 62.6; 2404.16816 Table 3). A Bengali or Marathi read-back (a "Main Character" angle) is defensible only with **human-checked templates, numbers rendered by code, and a Timbre→Prisma round-trip exact-match check**. Bengali or Marathi is safer than Tamil (IN22-Conv chrF++: Hindi 49.6, Bengali 49.7, Marathi 48.6, Tamil 39.1; XSTS Tamil 3.68).
7. **Test the input script for Evon instead of assuming one.** RomanSetu's 2.5× token saving for romanized Hindi (7.36 → 2.98 tokens/word) comes from Llama 2's English-centric tokenizer (2401.14280 Table 1). Indic-trained tokenizers are near parity in native script (Hindi 1.16–1.25× English; 2305.15425), and romanizing *raised* token counts for a multilingual tokenizer (XLM-R Arabic 1.18 → 1.94). Native script also won on understanding tasks (IndicSentiment 88.88 vs 82.44). Extraction is closer to understanding than to open generation.
8. **A speech-enhancement front-end before Prisma is more likely to hurt than help.** With a noise-trained ASR, raw single-channel enhancement "does not improve ASR even compared to the observed signals" (2201.06685), and enhancement artifacts delete consonants (2308.12615). For number words that means "saat/aath" and "sau/hazaar". The working mitigation is observation adding: output + ω·input, ~20% relative WER gain on real CHiME-3 for ω 0.3–0.8. It is not universal; it hurt with a stronger SE model in 2308.12615 Table 4. If tried at all, run it as an A/B arm judged on **rupee exact-match**, never as the default.
9. **A synthetic Timbre eval set will likely be optimistic and may rank variants differently from real audio.** TTS speech scored easier than real speech (MMS, 2305.13516 §7.4). Benchmarks can disagree on ranking (rank correlation −0.26; Vistaar 2305.15386). Every TTS-augmentation paper here evaluated on real speech (2010.05549, 2601.00935). We need a **small real-recorded Hinglish anchor set over an actual phone call** to check that synthetic deltas hold.

---

## 2. Scope and method

| Item | Detail |
|---|---|
| Question | Which ideas from international multilingual models (Aya, BLOOM, Jais, EuroLLM, Swallow, Chinese-LLaMA, NLLB/Seamless/MMS/Whisper) and Indic models (AI4Bharat suite, Airavata, IndicTrans2, Nemotron-Hindi) can a solo builder with Gnani's stack and one A100 40 GB for 3 days apply to Kaam ka Parcha? |
| Discovery | `arxiv` skill: 14 keyword searches with `search_arxiv.py` (loose; words are OR-matched), 30 landmark papers resolved by ID with `--id`, 9 boolean `abs:`/`ti:` queries against `export.arxiv.org/api/query`, ~4 s spacing for the arXiv rate limit. Full query list in §11. |
| Reading | Five reader agents, one per cluster, read `arxiv.org/html/<id>` (fallback `/abs`, `/pdf`). Each returned per-paper findings with table and section references, applicability, and read depth. Clusters B, E and most of A were read from full text. Clusters C and D were partly read through a summarising fetch, so those numbers carry **[VERIFY]** where the reader flagged them. |
| Exclusions | Paper results are not our results. Nothing here is a Prisma or Timbre measurement. Competitor models (Whisper, Seamless, MMS) are cited only for methodology, never as a comparison to Gnani, per `AGENTS.md` and the EULA guard in `R4` §1.6. |

---

## 3. Paper index

| Cluster | arXiv ID | Paper | Year | Read depth |
|---|---|---|---|---|
| A. LLM error correction | [2309.15701](https://arxiv.org/abs/2309.15701) | HyPoradise | 2023 | Full (LoRA column; H2T-ft column garbled in extraction) |
| A | [2309.15649](https://arxiv.org/abs/2309.15649) | Task-Activating Prompting (TAP) | 2023 | Full |
| A | [2307.04172](https://arxiv.org/abs/2307.04172) | Can Generative LLMs Perform ASR Error Correction? | 2023 | Full |
| A | [2401.10446](https://arxiv.org/abs/2401.10446) | RobustGER: LLMs are Efficient Learners of Noise-Robust ASR | 2024 | Full |
| A | [2310.13013](https://arxiv.org/abs/2310.13013) | GER for code-switching ASR | 2023 | Full |
| A | [2510.13281](https://arxiv.org/abs/2510.13281) | DualHyp: Two Heads Are Better Than One | 2025 | Full |
| A | [2409.09785](https://arxiv.org/abs/2409.09785) | GenSEC challenge and baselines | 2024 | Full |
| B. Entities, biasing, Hinglish | [2602.12287](https://arxiv.org/abs/2602.12287) | RASTAR: retrieval-augmented NE correction | 2026 | Full |
| B | [2506.10779](https://arxiv.org/abs/2506.10779) | NE in classroom speech: LLM revision + phonetic context | 2025 | Full |
| B | [2506.11091](https://arxiv.org/abs/2506.11091) | Customizing ASR with LLM feedback | 2025 | Full |
| B | [2608.05759](https://arxiv.org/abs/2608.05759) | Context biasing vs speech LLMs for new words | 2026 | Full |
| B | [2507.05727](https://arxiv.org/abs/2507.05727) | ContextASR-Bench | 2025 | Full |
| B | [2603.06373](https://arxiv.org/abs/2603.06373) | Doctor or Patient? Hinglish medical extraction | 2026 | Full |
| B | [2503.21670](https://arxiv.org/abs/2503.21670) | COMI-LINGUA (Hinglish multitask dataset) | 2025 | Full + HF card |
| C. International multilingual LLMs | [2402.07827](https://arxiv.org/abs/2402.07827) | Aya Model | 2024 | Full (summarised fetch, two passes) |
| C | [2402.06619](https://arxiv.org/abs/2402.06619) | Aya Dataset | 2024 | Full (summarised) |
| C | [2405.15032](https://arxiv.org/abs/2405.15032) | Aya 23 | 2024 | Full (summarised); Table 8 [VERIFY] |
| C | [2412.04261](https://arxiv.org/abs/2412.04261) | Aya Expanse | 2024 | Full (summarised) |
| C | [2211.05100](https://arxiv.org/abs/2211.05100) | BLOOM | 2022 | Partial |
| C | [2308.16149](https://arxiv.org/abs/2308.16149) | Jais | 2023 | Full (summarised) |
| C | [2409.16235](https://arxiv.org/abs/2409.16235) | EuroLLM | 2024 | Full (summarised) |
| C | [2404.17790](https://arxiv.org/abs/2404.17790) | Swallow (Japanese continual pre-training) | 2024 | Full (summarised) |
| C | [2304.08177](https://arxiv.org/abs/2304.08177) | Chinese-LLaMA/Alpaca | 2023 | Full (summarised) |
| C | [2410.14815](https://arxiv.org/abs/2410.14815) | Nemotron-Mini-Hindi | 2024 | Full (summarised, two passes) |
| D. Indic LLMs, script, tokens | [2401.14280](https://arxiv.org/abs/2401.14280) | RomanSetu | 2024 | Full (summarised; Hindi rows checked twice) |
| D | [2305.15425](https://arxiv.org/abs/2305.15425) | Tokenizers Introduce Unfairness Between Languages | 2023 | Full PDF |
| D | [2305.13707](https://arxiv.org/abs/2305.13707) | Do All Languages Cost the Same? | 2023 | Summarised; figure values not extracted |
| D | [2609.00378](https://arxiv.org/abs/2609.00378) | Token-cost ledger for the multilingual tax | 2026 | Summarised; Table 1 verbatim |
| D | [2401.15006](https://arxiv.org/abs/2401.15006) | Airavata | 2024 | Summarised |
| D | [2403.06350](https://arxiv.org/abs/2403.06350) | IndicLLMSuite | 2024 | Summarised |
| D | [2305.16307](https://arxiv.org/abs/2305.16307) | IndicTrans2 | 2023 | Full PDF |
| D | [2404.16816](https://arxiv.org/abs/2404.16816) | IndicGenBench | 2024 | Full PDF |
| E. Speech, noise, synthetic data | [2201.06685](https://arxiv.org/abs/2201.06685) | How Bad Are Artifacts? | 2022 | Full |
| E | [2308.12615](https://arxiv.org/abs/2308.12615) | NAaLoss | 2023 | Full |
| E | [2212.04356](https://arxiv.org/abs/2212.04356) | Whisper | 2022 | Targeted sections |
| E | [2305.13516](https://arxiv.org/abs/2305.13516) | MMS: Scaling Speech Technology to 1,000+ Languages | 2023 | Targeted sections |
| E | [2308.11596](https://arxiv.org/abs/2308.11596) | SeamlessM4T | 2023 | Targeted sections |
| E | [2403.01926](https://arxiv.org/abs/2403.01926) | IndicVoices | 2024 | Main text |
| E | [2305.15386](https://arxiv.org/abs/2305.15386) | Vistaar | 2023 | Full |
| E | [2208.11761](https://arxiv.org/abs/2208.11761) | IndicSUPERB | 2023 | Targeted sections |
| E | [2010.05549](https://arxiv.org/abs/2010.05549) | Augmented code-switched TTS for ASR | 2020 | Full |
| E | [2601.00935](https://arxiv.org/abs/2601.00935) | Code-switching ASR with TTS augmentation | 2026 | Full |
| E | [2503.23576](https://arxiv.org/abs/2503.23576) | Code-switched synthetic data quality is task dependent | 2025 | Full |

Also resolved but not read in depth: NLLB [2207.04672](https://arxiv.org/abs/2207.04672), Glot500 [2305.12182](https://arxiv.org/abs/2305.12182), Whispering LLaMA [2310.06434](https://arxiv.org/abs/2310.06434).

---

## 4. Cluster A: LLM generative error correction (GER) for ASR

| Paper | Headline result (paper's data) | What failed | Transferable mechanism |
|---|---|---|---|
| HyPoradise 2309.15701 | LLaMA-13B + LoRA (r=8): CHiME-4 noisy 11.1 → 6.6 (−40.5%), accented CommonVoice 14.8 → 11.0, SwitchBoard phone 15.7 → 14.1 (−10%) (Table 2). GPT-3.5 with 10 examples in the prompt: −10–21% (Table 3). Mandarin code-switch −24.5% with 15–20k pairs. | Full T5 fine-tune overfit on 1,728 pairs (CORAAL 21.4 → 23.1). Proper nouns over-corrected ("ward" → "warde"). | Report two upper bounds next to every result: best hypothesis in the list (o_nb) and best word-level combination (o_cp). |
| TAP 2309.15649 | Frozen InstructGPT + TAP: WSJ 11.87 → 8.72, ATIS 8.82 → 6.39 (Table 3; ~27% relative; the paper's 31–38% headline did not match any extracted row). LoRA OpenLLaMA: WSJ 2.11. | **Frozen OpenLLaMA-13B worsened WER** (11.87 → 13.32); GPT-2 → 29.56. | Prime the model on the task before showing hypotheses. Mid-size open models need LoRA, not zero-shot. |
| 2307.04172 | Transducer 5-best, ChatGPT one-shot, closest mapping: test-other 6.90 → 6.24, TED-LIUM3 13.53 → 10.13 (Table 2). | **1-best only: 6.90 → 8.25.** Whisper hypotheses with inconsistent ITN: worse (3.89 → ~4.96). Zero-shot truncated 14 sentences. | **Closest mapping** (snap to nearest hypothesis) and **selection** mode. Normalise formatting across hypotheses before the LLM sees them. |
| RobustGER 2401.10446 | LLaMA-2-7B: CHiME-4 12.8 → 6.9 (GER) → 5.9 (RobustGER, −53.9%). ~5k pairs ≈ full 9.6k data (Table 4). | Gains shrink with noise: metro 0 dB −10.1% vs 20 dB −30.3%. Radio (RATS) only −5.5%. | Hypothesis disagreement as a noise/confidence feature. |
| CS-GER 2310.13013 | Mandarin-English: −20.9% (Whisper), −24.5% mixing 3 systems. 1k pairs → −8.2%, 15k → −20.9% (Table 2). LoRA r=4 on Q/K/V, 0.06% of parameters. | No failure analysis. | Closest analogue to Hinglish. Mixing heterogeneous sources helps. |
| DualHyp 2510.13281 | Up to −57.7% on LRS2. LoRA r=16, 1.1–3B models, one A6000, ~8 h, 45.8k utterances. | Trusting a plausible-wrong hypothesis; inventing "december". **A weak second source made results worse** (German 55.7 → 100.4). | Separate labelled fields per source plus reliability tags. |
| GenSEC 2409.09785 | LLaMA2-7B: 11.82 → 8.33, beating the n-best oracle 9.32 (Table 1). | No hallucination study. | Protocol: a held-out set never used in prompts, metrics with and without normalisation, both oracle bounds, compare against a select/re-rank baseline. |

**Implication for us [SPEC].** We have two 1-best strings from different decoding modes. That is the regime where free generation hurt and selection or snapping was safe. A 3-day QLoRA on Evon is not supported by these papers when trained only on synthetic data: their fine-tuning gains needed ~1k–5k *real* labelled pairs. Start with constrained prompting and a deterministic fallback. Treat LoRA as an experiment, judged on a frozen held-out set.

---

## 5. Cluster B: entity and number correction, biasing, Hinglish extraction

| Paper | Finding | Design consequence for Kaam ka Parcha |
|---|---|---|
| RASTAR 2602.12287 | Phonetic top-k retrieval, then the LLM selects: NE-CER −18% (AISHELL-1), −34% (homophones). k=3 chosen because larger k adds irrelevant entities. Plain SFT was as good (6.01 vs 6.21). Non-entity CER rose slightly (5.35 → 5.43). Oracle lexicon includes test entities. | Part names: phonetic key over a **romanised, normalised** lexicon, top-3, Evon selects or abstains. The lexicon is ours and closed, so the oracle caveat matters less. |
| 2506.10779 | Phonetic filter + LLM revision: NE WER 32.3 → 22.7, non-entity WER unchanged at 7.0. **Full context in prompt: 43.4%** (longer, hallucinated revisions, p<0.0001). Prompt rule: "leave unchanged if no suitable alternative". | Never paste the full parts catalogue into Evon's prompt. Pass only matched candidates. Double Metaphone is English-only, so a Hinglish phonetic key is needed. |
| 2506.11091 | Text-LLM rewriting gave the best entity WER on food ordering (13.50 vs 13.80 RL-tuned ASR vs 17.79 baseline; Table IV). Domain context matters (13.80 → 14.42 without it). | Supports post-ASR LLM correction on a black-box ASR. Give a domain prompt. |
| 2608.05759 | With 250 distractors, a dedicated biasing method beat speech LLMs on all four sets. Speech LLMs collapsed (VibeVoice 4.17 → 27.92). | Test `bias_list` size empirically (curated ~30 vs full catalogue). Score error on non-bias words separately to catch damage. |
| ContextASR-Bench 2507.05727 | Explicit entity lists cut missed entities 26.84% → 4.55% (Table 2) but caused "severe hallucinations": models emitted only the prompt entities. Defines NE-WER (fuzzy) and NE-FNR = 1 − H/N. | Accept a verbatim-pass part name only if the transcribe pass corroborates it. Adopt NE-FNR. |
| Doctor or Patient? 2603.06373 | Hinglish noisy far-field medical conversations: in-domain ASR fine-tune was the big step (25.73 → 19.61 tcpWER). Unicode normalisation −0.34, GPT-4.1 correction only −0.68. Translating to English first added nothing. 6-shot hurt the end-to-end model (45.60 → 38.78). Dropped segments under 0.4 s to avoid hallucinations. | Canonicalise Unicode and script before any matching. Keep extraction prompts code-mixed. Use few examples. LLM correction is a small lever; conservative beats aggressive. |
| COMI-LINGUA 2503.21670 | 125,615 Hinglish instances, Roman/Devanagari/mixed. NER κ=0.852. One-shot Claude-3.5 85.0 F1 vs zero-shot GPT-4o 60.1. **No MONEY/QUANTITY/PRODUCT tags.** CC BY 4.0. | Can't evaluate our extractor. Its result supports 1–2 Hinglish examples in the prompt. We need our own gold set. |

**Implication for us [SPEC].** Evaluate at field level, not WER: amount exact-match in paise, date exact-match, part-name precision/recall, NE-FNR, non-entity damage, review rate, and **confident-wrong rate** (a wrong value presented without a review flag). That last metric is the one a garage customer cares about.

---

## 6. Cluster C: international multilingual LLMs (what Aya, BLOOM, Jais, EuroLLM, Swallow, Chinese-LLaMA and Nemotron-Hindi learned)

| Model / paper | Lever and result | Solo-builder verdict (3 A100-days) |
|---|---|---|
| Aya Model 2402.07827 | Translation-heavy mix shipped because it won on generation (FLORES spBLEU X→En 29.1 vs mT0x 20.2), even though another mix won discriminative tasks. **A 25% weight on 199.5K human examples, each seen 30+ times, was the worst mix (overfit).** GPT-4 judge 86–87% win vs humans 77%; GPT-4 ties 3% vs humans 15%. Humans pruned 50.2% of English templates. | **Borrow:** upweight a small gold set without repeating it dozens of times; human-prune templates; report LLM-judge vs human agreement. |
| Aya Dataset 2402.06619 | 204,114 human annotations, 65 languages, 2,997 contributors; edit counted only if Levenshtein ≥ 5; three-tier eval (native-written, machine-translated, human post-edited); data card per artefact. | **Borrow:** three-tier eval design and a data card for our Hinglish job-card set. |
| Aya 23 2405.15032 | **Depth beat breadth:** 23 languages vs 101, up to +41.6% multilingual MMLU. Synthetic data = strong model answering translated prompts *directly in the target language*. GPT-4 judge 82.4% win vs human ~51% average; Hindi 43.0% (8B) [VERIFY Table 8]. | **Borrow:** go deep on Hindi/Hinglish (plus at most one regional language). Generate natively, don't translate answers. |
| Aya Expanse 2412.04261 | Win rate vs Gemma-2-9B: 39.1 → 48.2 (arbitrage) → 53.3 (merge) → 60.4 (DPO) (Fig. 3). Weighted averaging beat SLERP/TIES/DARE. Changing the judge moved results 9.3 points. | **Borrow:** multi-teacher generation with a *deterministic* arbiter (sum check, paise integrity, date validity, language ID). Weighted LoRA averaging is cheap; expect small gains at small scale. |
| BLOOM 2211.05100 | Indic ≈ 4% of ROOTS [SPEC sum]. Tokenizer fertility within ~10% of monolingual (Hindi +9%). Regex PII redaction; RAIL licence. | **Borrow:** audit Evon tokenizer fertility on our transcripts. Redact phone and vehicle numbers in any released data. |
| Jais 2308.16149 | Arabic fertility 1.050 vs GPT-2 4.171. Dropped instruction tasks that break under translation. Layered safety: data, prompt, classifier, keyword filter. | **Borrow:** layered pre-read-back checks; drop templates that don't survive translation. |
| EuroLLM 2409.16235 | 20% parallel data with no harm to other scores. Filtered with Bicleaner + CometKiwi (reference-free MT QE ≥ 0.7). Final annealing phase on high-quality data. Loss only on answer tokens. | **Borrow:** a reference-free quality filter for any synthetic regional read-back text; finish training on the best hand-checked examples. |
| Swallow 2404.17790 | +11,176 tokens → 56.2% fewer tokens, up to 78% faster, but QA ±10% and summarisation −5–15%. 90:10 JA:EN beat 50:50. Parallel data helped only translation. | **Avoid** vocabulary extension. **Borrow:** keep ~10% general data in any domain LoRA so the model doesn't forget other skills. |
| Chinese-LLaMA 2304.08177 | 32k → 49,953 vocab, ~2× fewer tokens; LoRA r=8/64 with trainable embeddings; 8-bit llama.cpp ≈ FP16 perplexity. | **Borrow only:** 8-bit serving is safe. No extension. |
| Nemotron-Mini-Hindi 2410.14815 | 400B tokens; 60B IndicTrans2-translated; **whole Hindi corpus transliterated to Roman for Hinglish**; back-translation filter; English instruction tuning + small Hindi DPO. Hindi MMLU 38.20 → 49.89. 128 A100s. | **Borrow:** transliteration-based augmentation for romanised Hinglish variants; back-translation-style round-trip filtering. **Foundation-scale only:** the pre-training itself. |

**The trap.** Trusting LLM judges and translated test sets. Judges inflated win rates (86% vs 77% for humans), switching the judge moved results 9.3 points, and translationese is acknowledged but never measured in these papers. **None of the ten papers evaluates code-mixed or romanised input.** A small, honest Hinglish job-card benchmark therefore fills a documented gap.

---

## 7. Cluster D: Indic LLMs, script choice, token cost, translation

| Paper | Finding | Consequence |
|---|---|---|
| RomanSetu 2401.14280 | Llama 2 tokens/word: Hindi 7.36 native vs 2.98 romanised; Tamil 12.11 vs 4.89. Romanised wins En→Indic generation (chrF 37.40 → 46.87). **Native wins classification** (IndicSentiment 88.88 vs 82.44). Latency not measured. | Don't convert Prisma output to another script for Evon by default. Measure on Evon's tokenizer. |
| Petrov et al. 2305.15425 | cl100k premium: Hindi 4.79×, Bengali 5.84×, Tamil 7.65×. Indic-trained tokenizers: Hindi MuRIL 1.16, XLM-R 1.25. Romanising helps English-centric tokenizers but **hurts multilingual ones** (XLM-R Arabic 1.18 → 1.94). Processing time ~linear in tokens. | If Evon's tokenizer is Indic-aware, romanised Hinglish may cost *more* tokens. Test both scripts. |
| Ahia et al. 2305.13707 | ~5× cost for mid-resource non-Latin Indic languages vs English; Telugu XLSUM items often can't fit even one worked example in 4k context. | Keep prompts schema-driven and short; few examples. |
| Token ledger 2609.00378 | Hindi cl100k 4.76× → 2.54× with a tiny script-matched tokenizer; information floor 1.02×. Telugu 8.29× (GPT-4) vs 1.93× (GPT-4o). | The extra cost comes from representation, not from the language. With an Indic tokenizer, choose script by accuracy. Small preprint: supporting evidence only. |
| Airavata 2401.15006 | IndicTrans2-translated instructions kept only if back-translation chrF++ ≥ 50 (404k → 385k). LoRA r=16, α=32, all attention+MLP projections, lr 5e-4, 4 epochs, bf16; checkpoint average 0.6·e3 + 0.4·e4. Full fine-tune hurt English. Weak at mixed-language contexts. | Copy the round-trip filter as *parse → render → re-parse = same card*. Copy the LoRA settings as a starting point, with per-epoch checkpoints and a general held-out test set. |
| IndicLLMSuite 2403.06350 | Sangraha 251B tokens including **72B romanised** via IndicXlit; Anudesh 43.3K crowdsourced prompts allowing code-mixed input. | Romanised Indic text is now a normal training channel. Check Anudesh's licence before any use. |
| IndicTrans2 2305.16307 | v1 human eval: poor on "dates, numbers"; v2 uses `<dnt>` tags and digit normalisation. IN22-Conv En→X chrF++: hi 49.6, bn 49.7, mr 48.6, ta 39.1. XSTS: hi 4.53, bn 4.18, mr 4.06, ta 3.68. MIT licence. | Numbers and dates are placeholders filled by code. Bengali/Marathi over Tamil. IndicTrans2 is non-Gnani: at most an offline template pre-translation aid, and only after a rules check. |
| IndicGenBench 2404.16816 | One-shot En→X chrF: GPT-4 hi 48.6 / bn 40.0 / mr 39.2 / ta 34.5; Gemma-7B-IT hi 35.7. In-language one-shot examples work best. chrF over BLEU for low-resource. | Read-back QA design: 30–50 cards, human Bengali references, chrF + exact match on every amount and date, one-shot in-language example. |

---

## 8. Cluster E: multilingual speech, Indic benchmarks, enhancement, synthetic data

| Paper | Finding | Consequence for Line Noise Lab |
|---|---|---|
| How Bad Are Artifacts? 2201.06685 | Raw SE didn't beat the unenhanced noisy input. Artifacts, not residual noise, drive harm. Observation adding (ω 0.3–0.8) ≈ 20% relative gain on real CHiME-3, insensitive to ω. | Any SE arm comes with OA arms. Lab has clean and noise separately, so it can compute SAR per arm and correlate with Prisma CER and rupee accuracy. |
| NAaLoss 2308.12615 | SE hurts clean input (4.86 → 5.10), helps noisy (8.32 → 7.21/6.62). PESQ doesn't predict WER. OA helped weak SE, hurt strong SE (6.62 → 6.92), destroyed a clean-trained ASR (10.21 → 15.01). Artifacts delete consonants. | Judge on rupee exact-match. Always include a clean "no-harm" arm. The noise-ignorance term matches our engine-idle clips. |
| Whisper 2212.04356 | Formatting alone moved WER up to 50%. BasicTextNormalizer strips Unicode M-category characters, so it **mangles Devanagari**. Hallucination described only qualitatively. No-speech gating needed several combined signals. | Build a Hinglish normaliser (NFKC, keep combining marks, canonical numerals). Measure edge deletions: totals are spoken last. Confidence gates combine signals. |
| MMS 2305.13516 | Synthesised speech scored *easier* than real FLEURS. Domain-bias metric: frequency of training-domain words appearing in output. | Timbre eval sets understate real error, so report deltas only. Adapt the bias-word metric to idle clips: count numbers, ₹ and part names that appear without being spoken. |
| SeamlessM4T 2308.11596 | Noisy FLEURS at SNR 10 … −20 dB; speaker robustness via coefficient of variation across speakers saying the same text. | Extend the SNR grid to −5/−10 dB to find where Prisma breaks. Render each line in several Timbre voices and report CoefVar. |
| IndicVoices 2403.01926 | Part recorded over a real 8 kHz telephony bridge. Template + entity substitution for payment prompts. L1 verbatim vs L2 standardised transcripts; 89 noise tags. | Template-and-substitute rupee amounts; keep verbatim and canonical references; record a small real phone-bridge slice. |
| Vistaar 2305.15386 | Benchmarks can rank systems oppositely (ρ = −0.26). Telephone Hindi (Gramvaani) hardest (26.8–59.9 WER). Tuning on dev overfits (> 6.5 points). | Per-condition tables; check that rankings hold across conditions; freeze the test split before tuning post-processing. |
| IndicSUPERB 2208.11761 | Clean/known 12.4 → noisy/unknown 16.2 average WER. | Hold out Timbre voices from any tuning; cross voice × noise. |
| CS-TTS 2010.05549 | TTS-only gain small (72.1 → 71.0); real 12 h huge (→ 59.9); TTS pre-training + real best (55.2). All eval on real speech. | Synthetic is a supplement and a stress test, never the only evidence. |
| CS-TTS 2026 2601.00935 | Random-speaker TTS beat same-speaker; best at 2–3× real volume; TTS-only worse than real. UTMOS barely moved while MER fell 21.8 → 13.8. | Voice diversity matters more than polish; MOS is a poor gate. |
| Synthetic CS quality 2503.23576 | Human-rated naturalness didn't correlate with ASR gains; perplexity and OOV (diversity) did (0.89, 0.84). | Favour lexical and switch-point diversity and real mechanic vocabulary over polished sentences. |

---

## 9. Cross-cutting design proposals for Kaam ka Parcha

These are **[SPEC]** proposals derived from §4–§8. They feed the council in [`docs/ideas/council-gpu-multilingual/`](../ideas/council-gpu-multilingual/framed-question.md). None is implemented.

| # | Proposal | Grounding | Award lever | Survives without GPU? |
|---|---|---|---|---|
| P1 | **Two-pass arbiter.** Normalise both Prisma passes (Unicode, script, numerals) → deterministic Hinglish number grammar on the verbatim pass ("saade chaar sau" → 45000 paise) → compare with the transcribe pass's ITN value → **agree: keep; disagree: Evon chooses among the candidates or returns UNRESOLVED and quotes the span it used**. Reject any amount not in the candidate set. Disagreement turns into a stressed read-back question ("brake pad saade chaar sau, sahi hai?"). | 2307.04172, 2510.13281, 2401.10446, 2305.16307 | Noise Canceller, Mixed Vibes, Jugaad Genius (Gnani's LLM arbitrating Gnani's STT) | Yes: rules and the agree path run on CPU; Evon only on disagreement, and it can be a quantised CPU/free-tier build or a recorded run. |
| P2 | **Part names: retrieve then select.** Romanised phonetic key over the `vocabulary.py` lexicon, top-3 candidates, Evon selects or abstains. Never send the full catalogue. | 2602.12287, 2506.10779 | Mixed Vibes | Yes |
| P3 | **`bias_list` hygiene experiment.** Curated ~30 vs full list; score bias-word error and non-bias damage separately; accept a verbatim-only part name only if the transcribe pass corroborates it. | 2608.05759, 2507.05727 | Noise Canceller interview evidence | Yes (API credits, not GPU) |
| P4 | **Evaluation upgrades to Line Noise Lab:** o_cp upper bound ("is the right amount in either pass?"), correct→wrong damage rate, confident-wrong rate, NE-FNR, critical-insertion rate on idle clips, edge-deletion rate, CoefVar across Timbre voices, SNR to −10 dB, held-out voices, Hinglish normaliser, frozen test split, real phone-call anchor slice. | 2309.15701, 2409.09785, 2212.04356, 2305.13516, 2308.11596, 2305.15386 | Noise Canceller; interview | Yes |
| P5 | **"Parcha-Bench" data artefact:** a small Hinglish job-card benchmark with a data card. Three tiers: (a) native-written scripts, (b) the same scripts through the codec × noise chain, (c) a real phone-call anchor. Multi-teacher generation (Evon + rules) with a deterministic arbiter; round-trip filter; PII redaction; synthetic identifiers only. | 2402.06619, 2412.04261, 2401.15006, 2403.01926 | Interview ("speech data engineering"), Jugaad Genius | Yes: the dataset outlives the GPU. |
| P6 | **One regional read-back language (Bengali or Marathi), done safely:** human-checked templates, amounts and dates rendered by code, Evon only for item-name phrasing, Timbre→Prisma round trip requires an exact match on every number before the read-back is allowed. | 2305.16307, 2404.16816 | Main Character (only if it is a working leg, not a stretch) | Yes |
| P7 | **Speech enhancement only as an A/B arm** (none / SE / SE+OA ω∈{0.3,0.5,0.8} / clean no-harm), judged on rupee exact-match. **Rule flag:** a non-Gnani model in the product path; confirm with organisers before shipping it. | 2201.06685, 2308.12615 | Noise Canceller interview evidence | Yes (the result is a table) |
| P8 | **Script test for Evon:** 50 transcripts in Devanagari vs romanised: token count and extraction accuracy. | 2401.14280, 2305.15425, 2609.00378 | Engineering credibility | Yes |

**Do not do (evidence says it won't pay in 3 days):** vocabulary extension or continued pre-training (2404.17790, 2304.08177, 2410.14815); free-form LLM transcript rewriting (2307.04172, 2506.10779); LLM-generated numbers in any language (2305.16307); LLM-as-judge without a human-agreement check (2402.07827, 2412.04261); public absolute WER/CER or competitor comparisons (`AGENTS.md`); treating a Timbre-only eval as proof of real-world accuracy (2305.13516, 2010.05549).

---

## 10. Open questions and things to verify

| # | Question | Why it matters | How to check |
|---|---|---|---|
| Q1 | Does Prisma's verbatim pass ever contain the right amount when the transcribe pass is wrong (o_cp > o_nb on our clips)? | If not, P1's LLM arm can't help, and only abstention + read-back can. | Score existing lab outputs offline. The `04:30 100` clip is one data point; it needs ≥ 50. |
| Q2 | Is Evon's tokenizer Indic-aware (fertility on Devanagari vs romanised Hinglish)? | Decides P8 and prompt budget. | Load the tokenizer only (no GPU needed) and count tokens on 50 transcripts. |
| Q3 | Does Evon zero-shot follow a "choose-or-UNRESOLVED" schema reliably? The 2026-10-04 council notes recorded it as weak at instruction-following. | TAP shows frozen mid-size open models can hurt. | 30-case offline harness on a rented/quantised Evon before any LoRA. |
| Q4 | Is a non-Gnani enhancement model or IndicTrans2 template aid allowed? | Rule 3 ("uses Gnani AI technology") and Rule 7. | Ask on Discord, in writing. |
| Q5 | Aya 23 Table 8 human-eval numbers; Aya/Expanse judge figures. | Read through a summarising fetch. | **[VERIFY]** against the PDF before quoting. |

---

## 11. Research log

**Skill and tooling.** `arxiv` skill installed at `~/.claude/skills/arxiv/` (from `NousResearch/hermes-agent`, `skills/research/arxiv`). Searches ran through `scripts/search_arxiv.py` and a stdlib Atom parser against `https://export.arxiv.org/api/query`, with ~4 s between calls. Raw output was kept in the session scratchpad (not committed).

**Keyword searches (`search_arxiv.py "<q>" --max 6`; loose OR-matching, many off-topic hits):**
1. generative error correction large language model speech recognition hypotheses → 2309.15649, 2409.09785, 2507.09116, 2309.15701
2. LLM ASR error correction multilingual low-resource → 2605.17152 (not read), 2105.14779
3. code-switching Hindi English speech recognition → 1810.00662 (Hindi-English CS corpus; not read)
4. Hinglish code-mixed large language model → 2107.03760 HinGE (not read), 2602.21933
5. Indic large language model Hindi instruction tuning → 2308.16149 Jais
6. multilingual instruction-following model 101 languages → 2503.07539 XIFBench (not read)
7. massively multilingual speech recognition 1000 languages → off-topic hits
8. Indian languages speech recognition benchmark dataset → off-topic hits
9. romanization Indic languages large language models → off-topic (2610.00223 Noor, etc.)
10. tokenizer unfairness across languages cost → 2305.15425, 2609.00378, 2605.24718, 2609.39001
11. speech enhancement front-end hurts automatic speech recognition → 1811.04224 (weak match)
12. spoken number inverse text normalization → off-topic hits
13. synthetic TTS data augmentation code-switched ASR → 2010.05549, 2503.23576, 2601.00935
14. telephone narrowband 8 kHz speech recognition noise robust → off-topic hits

**ID lookup (`--id`, one request, 30 IDs, all resolved):** 2402.07827, 2402.06619, 2405.15032, 2412.04261, 2211.05100, 2207.04672, 2308.11596, 2305.13516, 2212.04356, 2305.16307, 2401.15006, 2403.06350, 2401.14280, 2403.01926, 2305.15386, 2208.11761, 2308.16149, 2305.15425, 2305.13707, 2309.15701, 2409.09785, 2310.06434, 2307.04172, 2404.17790, 2304.08177, 2409.16235, 2410.14815, 2201.06685, 2305.12182, 2404.16816.

**Boolean queries (direct API, `max_results=8`):**
- `abs:"error correction" AND abs:ASR AND (abs:Hindi OR abs:Indic OR abs:code-switching OR abs:code-switched)` → 2310.13013, 2510.13281, 2603.06373
- `abs:ASR AND abs:LLM AND (abs:"named entities" OR abs:numerals OR abs:"numeric entities")` → 2507.05727, 2506.10779, 2506.11091, 2602.12287, 2512.21828, 2608.05759, 2603.25460
- `abs:Hinglish AND (abs:speech OR abs:ASR)` (first attempt returned an empty body; retried, sorted by date) → 2603.06373, 2503.21670
- `(abs:Indic OR abs:"Indian languages") AND abs:speech AND abs:"large language model"` → 2607.23808 Indic DiarBench, 2605.12242 (not read)
- `abs:Gnani` → only 1901.00413 (unrelated Kannada OCR). **Gnani's own research is on its website, not arXiv** (see R4).
- `abs:"N-best" AND abs:LLM AND abs:noisy` → 2401.10446, 2406.04432
- `abs:"spoken language understanding" AND abs:multilingual AND abs:LLM` → 2404.10922, 2408.03900, 2501.06117 (not read)
- `ti:"speech enhancement" AND (abs:"downstream ASR" OR abs:artifacts)` → 2201.06685, 2308.12615, 2603.02641

**Reading.** Five reader agents ran in parallel, one per cluster (A: 7 papers, B: 7, C: 10, D: 8, E: 11). Each was given the project context, cluster-specific questions, and a fixed return format with read depth. Reader-reported discrepancies kept in this document: TAP's headline vs table rows; HyPoradise's garbled H2T-ft column; RobustGER Table 4 split labels differing between two fetches; 2601.00935 inconsistent about model size; Aya 23 Table 8 to be re-checked.
