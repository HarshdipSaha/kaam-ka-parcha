# Framed question (as given to all five council seats, 2026-10-05)

Method: `llm-council` skill (Karpathy-style: 5 independent advisors → anonymised peer review → chairman). Inputs: [`R7-a100-gpu-sprint.md`](../../research/R7-a100-gpu-sprint.md), [`R8-multilingual-models-arxiv.md`](../../research/R8-multilingual-models-arxiv.md), [`council-verdict.md`](../council-verdict.md) (2026-10-04), `AGENTS.md`, `README.md`, `docs/abouthack.txt`. Part of AIDLC effort [`007`](../../../aidlc-docs/efforts/007-gpu-sprint-multilingual-council/requirements-delta.md).

---

DECISION: Harshdip (solo student, NSUT Delhi, ~15 h/week, laptop without a GPU) will have **one NVIDIA A100 40 GB for 3 days** (dates not yet fixed) before the **10 Nov 2026** deadline of Gnani AI's "Great Indian AI Internship Challenge". Today is 5 Oct. How should the GPU window, and the weeks around it, be used to make **Kaam ka Parcha** more likely to win an internship offer and one award? Which candidate moves should be done, in what order, and what should be dropped? The user also asked for ideas drawn from **international multilingual-model research** (Aya, BLOOM, Jais, EuroLLM, Swallow, Chinese-LLaMA, NLLB/MMS/Seamless, AI4Bharat Indic models) and from LLM-based ASR error correction.

THE PRODUCT (built, 196 offline tests passing)
A mechanic dictates a Hinglish repair estimate over engine noise. Gnani **Prisma** STT runs two passes on the same audio: `format=transcribe` for inverse text normalisation of numbers, and `format=verbatim` with a 65-word automotive `bias_list`. An extractor builds a job card with line items, amounts as integer paise tied to transcript evidence, and a delivery date; ambiguous fields stay "needs review". Gnani **Timbre** reads the card back to the customer over a *simulated* 8 kHz G.711/AMR-NB line with engine noise, with an on-screen disclosure. The customer confirms or corrects by voice; low confidence or retries fall back to a digital one-tap confirm. The output is a sealed, hash-verified PDF with a QR verify page, plus WhatsApp text. A "Line Noise Lab" harness covers codec × SNR × packet loss × impulse noise and computes CER/WER, rupee exact-recovery and hallucination metrics; its public export fails closed without organiser consent.

CONTEST FACTS
- Must build on Gnani models: Prisma v2.5 (STT), Timbre v2.5 (TTS), **Evon v3.3** (30B MoE, ~3.5B active, 11 Indian languages, Apache-2.0 open weights). Rule 3: the submission names the Gnani models used. ~4,980 API credits remain (Prisma ≈ 0.20 cr per audio-second per pass; Timbre ≈ 0.05 cr per character). Evon is not covered by credits; it must be self-hosted.
- Selection: verified engagement on one nominated LinkedIn and one X post → shortlist → **individual interview decides the offer** (up to ₹1 lakh/month × 6 months). Ten ₹50k awards, max one per entrant. The prior council chose **Noise Canceller** (messy, noisy, real telephonic audio) as primary and **Mixed Vibes** (code-mixed voice) as secondary. Others: Main Character (regional/low-resource language), Jugaad Genius (creative use of Gnani models), Solo Ninja, Demo Day Drop (60-s video), Crowd Favourite.
- Constraints: synthetic data only, no real PII; Rule 7 forbids misleading demos; the EULA guard means publishing only own-pipeline deltas, never competitor comparisons, and no absolute WER without organiser consent. Discord answers on synthetic filming and public numbers are still pending.

VERIFIED WEAKNESSES (checked against code on 2026-10-05)
- W1: **The step that decides the rupee amounts is a non-Gnani LLM.** The extractor defaults to Groq `llama-3.3-70b-versatile` (`config.py:44-50`). Intake and re-ask call `require_extractor()` and fail without it (`app.py:187,223`). `EXTRACTOR_PROVIDER` is read but unused. The README calls the extractor "optional".
- W2: On the only noisy clip, Prisma's transcribe pass returned `फ्रंट ब्रेक पैड 04:30 100 …` where ₹450 ("saade chaar sau") was spoken. The card was right only because the Groq LLM chose the verbatim-pass evidence. The clip is *synthesised* speech mixed with a recorded engine.
- W3: No real human recordings yet. The Oct 7 gate (10 real lines beside a scooter, ≥ 70% amounts exact) is open.
- W4: The 74-case "generalisation corpus" is hand-written romanised text. Its provenance labels name recordings that don't exist, no code runs any extractor on it, and the gate row "74/74 PASS" can't be reproduced.
- W5: HTTP 429 throttling: 2 of 4 back-to-back calls were rejected, and there is no retry or backoff.
- W6: The demo storyboard's proof card shows **unmeasured** numbers ("+20.0% part recovery", "96.0% short-reply flush recovery", "800 synthetic telephony turns").
- W7: The Lab grid has never been run, and the SynthCall audio has never been rendered. W8: no consent yet for public numbers. W9: the extractor payload isn't Evon-ready (no thinking-off flag, no JSON schema).

EVON ON ONE A100 40 GB (R7, verified on Hugging Face 2026-10-05)
- BF16 weights are 63.5 GB and don't fit. The only ready-made fit is the community **GGUF Q8_0 (31.45 GiB) on llama.cpp**. No official FP8/AWQ/GPTQ build exists. Self-made FP8 weight-only ≈ 33 GB (tight) and W4A16 ≈ 18 GB, both estimates.
- KV cache ≈ 6 KB/token (only 6 of 52 layers are attention). Both HF repos are ungated, so there is no access wait.
- 16-bit LoRA ≈ 60 GB (no). 4-bit QLoRA ≈ 35 GB peak, but the tooling is fragile.
- After the GPU is returned: quantised GGUF on a free HF ZeroGPU Space, Modal, or Kaggle, or a deterministic CPU fallback.

R7 RANKED GPU SHORTLIST (best pick = #1 + #2, "Evon cross-examines Prisma")
1. Evon replaces Groq as extractor, plus the first real extraction eval (fixes W1/W4). 2. Rupee Cross-Examiner: a deterministic Hindi-numeral grammar on the verbatim pass ("saade chaar sau" → 450) plus an Evon reconciler comparing both passes. An amount is auto-accepted only when they agree; otherwise `amount=None` and Timbre asks a targeted re-ask ("Brake pad kitne ka? Sirf rakam boliye"). Metric: false-confirmation rate before/after. 3. Gold-first synthetic corpus v2 (truth first, Evon verbalises it into mechanic Hinglish, ~160 Timbre→codec→Prisma cases). 4. Live three-model demo with latency, recorded during the GPU window. 5. Post-GPU hosting kit (quant ladder, ZeroGPU/Modal/Kaggle, CPU fallback). 6. QLoRA adapter (high risk). 7. Tanglish/Benglish numeral leg.
- R7's plan needs **~20–24 h of pre-GPU work** (numeral grammar, eval runner, Evon-ready extractor, credit-spending batch with 429 backoff, 3–5 real speakers × 10 lines) and **~38–42 attended hours** inside the 72-h window. Credits: ≈ 1,150–1,700, leaving ≈ 1,650 buffer after reserving the Lab grid and judging demos.

R8 LITERATURE FINDINGS (45 arXiv papers; paper results, not our measurements)
- LLM error correction helps when fine-tuned on real pairs or given N-best lists. With **only a 1-best hypothesis, free LLM generation made ASR worse** (6.90 → 8.25 WER). Frozen mid-size open LLMs also hurt (13B: 11.87 → 13.32). Constrained modes (choose a hypothesis, or snap to the nearest one) were safe. Separate labelled fields per source beat pooled lists (14.2 vs 23.3). Hypothesis disagreement tracks noise.
- **No paper recovers when both hypotheses are wrong** (radio-degraded audio: ≤ 5.5% gain), and LLMs invent plausible values. None treats money as an entity, so amounts need a deterministic grammar plus abstention, with the customer's confirmation as the final check.
- Part names: phonetic top-3 retrieval with the LLM selecting cut entity errors 18–34%. Putting the full context in the prompt raised entity WER to 43.4% (hallucination). Entity bias lists can make models output entities that were never spoken.
- International-model lessons that fit a 40 GB GPU: data curation, not model surgery. Vocabulary extension buys speed, not quality (Swallow: summarisation −5–15%). Aya Expanse's multi-teacher generation with an arbiter gave +9.1 win-rate points; here the arbiter can be deterministic (items sum to total, integer paise, valid date). Airavata's round-trip filter. Nemotron-Hindi's transliteration for Hinglish. Aya 23: **depth beat breadth** (23 languages > 101). Aya's data cards and three-tier evaluation. LLM judges inflate scores (86% vs 77% human). None of the ten papers evaluates code-mixed input.
- Keep numbers out of every text generator: IndicTrans2 had to tag numbers and dates to stop mangling. A Bengali/Marathi read-back is defensible only with human-checked templates and amounts filled in by code. Tamil was the weakest of the three on conversational MT (chrF++ 39.1 vs ~49).
- A speech-enhancement front-end tends to hurt a noise-trained ASR, because artifacts delete consonants. Synthetic TTS eval sets score easier than real speech and can rank variants differently, so a small real phone-call anchor set is needed.
- R8 proposals: P1 two-pass arbiter (≈ R7 #2), P2 retrieve-then-select part names, P3 `bias_list` size A/B, P4 Lab metric upgrades (upper bound "right amount in either pass", correct→wrong damage, confident-wrong rate, critical insertions on idle clips, voice CoefVar, SNR to −10 dB, Hinglish normaliser, frozen split, real anchor), P5 "Parcha-Bench" Hinglish job-card benchmark with a data card, P6 one regional read-back done safely, P7 enhancement only as an A/B arm (non-Gnani rule flag), P8 script test for Evon's tokenizer.

AT STAKE: a ~₹6 lakh internship offer, a ₹50k award, credibility in a one-to-one interview where Gnani engineers will probe every claim, 3 GPU-days that won't recur, and ~75 remaining build hours (15 h/week × 5 weeks), which must also cover filming, posting and social engagement.

QUESTIONS
(a) Is "Evon cross-examines Prisma" (Evon replaces Groq + numeral grammar + constrained reconciler + targeted re-ask) the right core bet, or is there a better use of the GPU and the weeks around it?
(b) Rank the candidate moves (R7 #1–#7, R8 P1–P8). What should be dropped?
(c) What must happen before, during and after the GPU window? What if the GPU never materialises or arrives late?
(d) Add a regional-language read-back (Main Character) or a Tanglish/Benglish leg, or stay deep on Hinglish?
(e) How should the integrity issues (W1 Groq in the critical path, W4 unreproducible corpus gate, W6 unmeasured proof-card numbers) be handled: fixed quietly, disclosed, or turned into part of the story?
(f) Which multilingual-model lesson, if any, belongs in the public demo or post, and which stays for the interview?
