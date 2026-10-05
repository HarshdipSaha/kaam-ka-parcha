# Framed question (as given to all five council seats, 2026-10-05)

Method: `llm-council` skill (5 independent advisors → anonymised peer review with one evidence file each → chairman). Inputs: [`R9-real-audio-benchmark-analysis.md`](../../research/R9-real-audio-benchmark-analysis.md), effort [`006`](../../../aidlc-docs/efforts/006-real-api-real-audio-benchmark/effort-state.md), the 007 verdict [`council-gpu-multilingual-verdict.md`](../council-gpu-multilingual-verdict.md), [`R8`](../../research/R8-multilingual-models-arxiv.md), `AGENTS.md`, `docs/abouthack.txt`. Part of AIDLC effort [`008`](../../../aidlc-docs/efforts/008-real-audio-analysis-council-spec/requirements-delta.md).

---

DECISION: Harshdip, a solo student building on two laptops, ran the project's first large real-audio benchmark against Gnani's Prisma STT and merged it as PR #17 (effort 006). A deep offline analysis (R9) followed. **What should change in Kaam ka Parcha now: the product, the evaluation harness, the next measurement, the award target and the 007 plan? And which improvements belong in the updated spec?** Today is 5 Oct 2026; the contest deadline is 10 Nov 2026.

THE PRODUCT (unchanged since the 007 council)
A mechanic dictates a Hinglish estimate over engine noise. Prisma runs two passes on the same audio: `transcribe` (inverse text normalisation, so digits) and `verbatim` (with an automotive `bias_list`; the product list is 65 words). An extractor builds a job card with paise amounts tied to transcript evidence. Timbre reads it back over a *simulated* 8 kHz G.711/AMR-NB line. The customer confirms or corrects by voice, and the result is sealed as a PDF and WhatsApp text.
- Today the extractor is Groq Llama-3.3-70B, a non-Gnani model, and it is mandatory for intake and re-ask.
- There is no deterministic numeral grammar, no two-pass agreement check and no system-initiated re-ask yet.
- The one observed money failure (effort 005): the transcribe pass produced `04:30 100` for "saade chaar sau" (₹450), while the verbatim pass held the right words.

THE 007 VERDICT (council, earlier today)
- Core promise: a wrong rupee amount never gets confirmed.
- Money comes from a deterministic grammar plus agreement between the two passes. On disagreement the system abstains and asks a targeted re-ask, on intake and on corrections.
- Evon replaces Groq for line items and part names only.
- The GPU is a bonus measured run, capped at about 12 attended hours.
- Hinglish only. The research belongs in the interview.
- First step: a Discord message to the organisers asking about scripted real-person audio, real phone calls, community Evon quants under Rule 3, and public deltas.
- Its weakest assumption was "W3: no real recordings yet".

WHAT PR #17 / EFFORT 006 RAN
- **Audio:** 120 IndicContextEval Hindi clips (CC BY 4.0; 23 professional domains; Read 80 / Extempore 40; code-mixed 68 / not 52; 6–19 s; speaker-disjoint) plus 5 private workshop clips scored against YouTube auto-captions.
- **Grid:** 2 modes × 2 codecs (G.711, AMR-NB 4.75) × {clean, 10, 5, 0 dB} of recorded *engine-idle* noise. No impulse noise, no packet loss. The verbatim pass used a 12-word bias list.
- **Outcome:** 2,000 successful conditions. ~4,965 credits estimated, which is essentially one full 5,000-credit key. Effort 006 records the user's statement that **ten additional 5,000-credit keys are available**; their provenance isn't recorded.
- **No row carries an amount label.**

R9 FINDINGS (private: absolute numbers; reproducible with one script)
1. **Scoring artefact.** Code-mixed references write each English word twice (Devanagari plus Latin gloss); Prisma writes Devanagari only. Cleaning the reference moves mean CER from 0.162 to 0.070. Code-mixed clips go from looking 2.4× worse to slightly *better* (0.063 vs 0.080 cleaned).
2. **Spontaneous speech is the real difficulty.** Extempore cleaned CER is ~0.095 vs Read ~0.044–0.070. Mechanic dictation is extempore.
3. **Engine-idle noise is too easy.** G.711 at 0 dB is only +8–9% relative, and 10/5 dB match clean. Only AMR-NB 4.75 at 0 dB bites (+39–41%). Per-clip difficulty is nearly constant across conditions (ρ = 0.949). Three of four SNR steps added little information for their credits.
4. **Transcribe and verbatim are one decode with different number formatting.** 88–91% of pairs tie exactly, and ΔCER ≈ −0.003. On numeral clips transcribe emits digits (14% of hypotheses) and verbatim never does ("50" ↔ "पचास"). The passes agree on number values in the examples checked. The second pass costs a full extra 0.2 credits/s and ~2 s for almost no extra recognition, beyond the number cross-check.
5. **Failures are deletions and silent empties, never insertions.** 0% of rows were insertion-heavy and 2–5% deletion-heavy. One clip returned HTTP success with an empty transcript on AMR-NB (clean and 0 dB) but scored 0.005 CER on G.711.
6. **No bias-word insertions** with the 12-word list (0 suspect rows). The product's 65-word list is untested.
7. **One label mismatch (i036)**, which should be excluded. The workshop slice is unscoreable: auto-caption references, and the text is redacted.
8. **Latency** per pass is p50 ~2.0 s and p95 ~7.3–7.5 s. Two sequential passes mean ~4 s typical and ~15 s at p95.

CONTEST FACTS AND RULES (unchanged)
- Must use Gnani models: Prisma, Timbre and Evon (open weights), named per Rule 3. 5,000 programme credits per registration.
- Selection: post engagement and submission review lead to a shortlist; an individual interview decides the offer. Ten ₹50k awards, max one per entrant: Noise Canceller ("messy, noisy, real telephonic audio"), Mixed Vibes (code-mixed), Real Deal (real-world problem), Jugaad Genius, Solo Ninja, Demo Day Drop, and others.
- Synthetic data only, no real PII. No misleading demos. Publish only own-pipeline deltas, never competitor comparisons, and no absolute WER without consent. Organiser answers are still pending.
- Integrity items still open: the README calls the extractor "optional"; `demo.md` has unmeasured numbers; `gates.md` shows an unreproducible "74/74 PASS".

AT STAKE: a ~₹6 lakh internship offer, one ₹50k award, interview credibility with Gnani engineers, about 5 weeks of solo time, and how the newly available credits get spent.

QUESTIONS
(a) What do these results change about the core bet and the 007 verdict? What is now stronger, weaker or wrong?
(b) What should the next measurement be? Design benchmark v2: what to label, how many utterances, which conditions, what the credits go to. How should the amount-labelled set be built (Timbre synthetic, real recordings, or both), given the pending synthetic-data ruling?
(c) Which evaluation-harness fixes are mandatory before any number is trusted or shown?
(d) Which award does the evidence now support: Noise Canceller, Mixed Vibes or Real Deal?
(e) Keep two Prisma passes on every intake, or move to verbatim plus a targeted transcribe of the amount span (or another design)?
(f) What must the updated spec contain, and what should it explicitly leave out?
