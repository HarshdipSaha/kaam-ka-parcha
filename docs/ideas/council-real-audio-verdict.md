# Council Verdict: What the real-audio benchmark changes (2026-10-05)

> Method: `llm-council` skill (5 advisors → anonymised peer review by 5 reviewers, each fact-checking against one evidence file → chairman). Transcript: [`framed-question.md`](council-real-audio/framed-question.md), [`responses-anon.md`](council-real-audio/responses-anon.md), [`mapping-secret.md`](council-real-audio/mapping-secret.md), [`reviews.md`](council-real-audio/reviews.md). Input analysis: [`R9`](../research/R9-real-audio-benchmark-analysis.md). Supersedes conflicting parts of the [007 verdict](council-gpu-multilingual-verdict.md). The resulting spec draft (`docs/specs/money-path-safety-spec.md`) is held back for revision before commit. AIDLC effort [`008`](../../aidlc-docs/efforts/008-real-audio-analysis-council-spec/effort-state.md). Recommendation only; nothing here is implemented.

## Where the Council Agrees

- **PR #17 measured transcription, not the promise.** All five advisors say so. It ran 2,000 conditions and labelled zero amounts. The First Principles Thinker (E) calls CER on professional-domain Hindi "a proxy for a proxy". The one real unknown is how often a wrong amount reaches the customer's "haan".
- **The ten extra keys are a hard stop.** The Outsider (A), the Contrarian (B), the Executor (C) and E won't spend them until their provenance is written down. Review 4 confirms that console keys draw on one registration's 5,000 credits. Only the Expansionist (D) says "if clean", and every reviewer flagged that.
- **Real Deal is the award.** A, C, D and E name it. B rules out Noise Canceller because claiming it would be a misleading demo. Surviving engine-idle noise is Prisma's win, not Harshdip's.
- **Drop the middle SNR steps.** C, D and E keep G.711 clean and AMR-NB 4.75 at 0 dB, the only condition that hurt.
- **Integrity items come before any new number** (A, B, C).

## Where the Council Clashes

**Is two-pass agreement a safety net?** B and E say finding 4 breaks the 007 verdict. One decode written twice is one witness, so a dropped "hazaar" or a misheard "saade teen" gets past both passes. D calls it "the agreement signal the 007 verdict asked for". C keeps both passes because they "caught" ₹450, and no check existed to do that. Ruling: the logic in B and E holds, and D is wrong to call this verification. But R9 rates grammar plus agreement "strengthened" and calls deletions "the safe failure direction" (Review 1). So B's and E's failure cases are untested inference. Benchmark v2 must test them rather than assume them. The agreement check is a formatting cross-check, and the spec will describe it that way.

**What replaces two sequential passes?** C: run them in parallel. D: run verbatim, then re-transcribe the amount span. E: verbatim plus Harshdip's own grammar, keeping transcribe only if a measurement shows it earns its cost. Prisma returns no word timestamps, which kills D's design (Review 5). Concurrency is unmeasured and 429s have already been seen, which kills C's "one async change" (Reviews 1, 2, 5). **E wins.**

**Timbre or human voices for v2?** C wants Timbre only, B calls that circular, A wants recordings of friends, and D wants both. Ruling: use both and always report them separately. R9 locates the difficulty in extempore speech, so Harshdip's own extempore takes are the slice that counts.

**Scale.** D proposes 400–600 utterances, impulse noise, packet loss and a CC BY release. That breaks the 2,000-credit Lab cap and won't fit five solo weeks. Rejected.

## Blind Spots the Council Caught

1. **The correction turn is untested** (Review 1). Customers reply with short, number-only speech over AMR-NB. That codec caused R9's only real degradation and i109's silent empty, and R9 has no clip under 6 s.
2. **The original key is nearly empty** (Review 2). The estimate is 4,965–4,970 of 5,000 credits used, and the balance was never verified. So provenance gates every further call, including the demo.
3. **No live-call failure policy** (Review 2). The run hit two HTTP 504s in 2,002 requests, and the product has no policy for a 504, a 429 or an empty-200.
4. **Groq still decides intake and corrections** (Review 3), which conflicts with Rule 3. Nobody carried the Evon swap forward, and nobody plans to measure recovery after a re-ask.
5. **The bias list may never have run** (Review 5). An invalid `bias_list` is silently ignored and still returns 200, so "0 insertions" needs a positive control.
6. **Prisma has no confidence field** (Review 5), so abstention can only come from grammar completeness.
7. **Real Deal needs proof of usefulness** (Review 4), such as a real mechanic trying scripted estimates. Gnani's page lists Automobile as an industry.

## The Recommendation

- **(a) What changed.** Stronger: the grammar-and-abstain core, abstaining on incomplete numbers (failures are deletions, never insertions), and Real Deal. Weaker: two-pass agreement as verification, and both "hard problem" stories (Noise Canceller and Mixed Vibes). Wrong: 007's W3 (real audio now exists, though none is amount-labelled), and the assumption that credits are plentiful.
- **(b) Benchmark v2.** 200 amount-dense utterances (120 Timbre-voiced scripted estimates and 80 of Harshdip's own extempore takes), plus 40 short number-only corrections, all labelled in paise. Conditions: G.711 clean and AMR-NB 4.75 at 0 dB. The 65-word bias list goes on with a positive control. Budget ≤2,000 credits from a documented source. Human audio stays internal until organisers rule.
- **(c) Mandatory harness fixes.** Strip Latin glosses from references. Exclude i036 and the workshop slice. Score an empty-200 as a hard failure. Reproduce R9 from one command. Add the bias positive control and per-row paise labels. Fix the README "optional" claim, demo.md's unmeasured numbers and the "74/74 PASS".
- **(d) Award.** Real Deal.
- **(e) Pass design.** Verbatim plus the numeral grammar is the money path. The full transcribe pass stays as a cross-check through v2, then is dropped unless it catches a wrong amount the grammar alone would pass.
- **(f) Spec contents.** See "Decisions for the Updated Spec" below.

## The One Thing to Do First

Today, before writing any code, open the Gnani console. Record the configured key's real balance in effort 008, along with where the ten keys came from. Then send the 007 Discord message with one added question: "May these keys be used?"

## Factual Corrections to Carry Forward

1. No agreement check exists. Groq picked the verbatim evidence; nothing "caught" ₹450 (C).
2. Running the passes in parallel is not free. Concurrency is unmeasured, it doubles the burst rate, and effort 005 saw 429s (C).
3. "Spent a whole key" is a local estimate, and the provider balance was never checked (A, B, E). "Fits in one key" ignores that the key is nearly spent (C, E).
4. The amount-span re-transcribe can't be built, because REST and WS return no timestamps or confidence. The claimed "roughly in half" saving is unmeasured (D).
5. The code-mixed finding is not on R9's shareable list. No public report or organiser consent exists (D).
6. R9 rates grammar plus agreement "strengthened". B's and E's wrong-amount scenarios are untested.
7. The 0.2 credits/s figure comes from a single-call probe in `docs/gates.md`, not from published pricing.
8. The verbatim requests asked for bias score 1.0, but there is no evidence the boosting was applied.
9. Gnani's page lists BFSI, Automobile and Collections, so D's banking point stands; this supersedes 007's correction 6. D's adoption claim, "first open benchmark" and "engineers will share" remain unsupported.
10. Mixed Vibes rewards a code-mixed voice experience, not difficulty.
11. "Misleading demos" (Rule 7) and the deltas-only guard come from the full programme terms, not the landing page.

## Decisions for the Updated Spec

1. **Primary metric:** wrong-amount-confirmed rate on the amount-labelled set, which must be 0. Secondary metrics: abstain rate and recovery-after-re-ask. *Out:* CER as a headline or public metric.
2. **Money path:** verbatim pass → deterministic numeral grammar → paise. An incomplete number (a dangling "saade" or a missing multiplier) means abstain plus a targeted re-ask. *Out:* any LLM producing amounts.
3. **Transcribe pass:** runs sequentially as a value cross-check only, and disagreement means abstain. Always called a formatting cross-check, never independent verification. It stays past 27 Oct only if v2 earns it. *Out:* span re-transcribe, parallel calls, streaming.
4. **Empty-200, 504 and 429:** each means abstain plus re-ask, never "no items". *Out:* silent retries.
5. **Re-ask scope:** re-ask covers both intake and corrections. Correction-turn audio is short, number-only speech over AMR-NB.
6. **Read-back:** a Timbre read-back of every amount is mandatory before the job card is sealed.
7. **Extractor:** Evon replaces Groq for line items and part names, and Groq leaves the shipped path. The README calls the extractor required. *Out:* Evon touching amounts.
8. **Line Noise Lab:** harness fixes as listed in (c). *Out:* 10/5 dB steps, impulse noise, packet loss, the GPU run, multilingual.
9. **Benchmark v2:** as in (b), with the Timbre and human slices reported separately. *Out:* dataset release, 400+ utterances.
10. **Award:** Real Deal. *Out:* noise-robustness claims.
11. **Publication:** own-pipeline deltas only, after organiser consent. The code-mixed artefact finding stays for the interview. *Out:* absolute CER/WER, competitor comparisons, a BFSI pitch.
12. **Credits:** no call on the ten keys without written provenance.

## Dated Go/No-Go Gates

These gates supersede 007's gates where they conflict, including its 14 Oct gate and the 12-hour GPU allowance.

| Date | Gate | Pass | Kill/pivot |
|---|---|---|---|
| 2026-10-06 | Credits + integrity | Balance and provenance recorded in 008; Discord sent; README, demo.md, gates.md fixed | No written provenance → the ten keys are never used; budget = verified own balance |
| 2026-10-09 | Harness | R9 reproduces from one command; empty-200 fails; i036 excluded | Not reproducible → no R9 number is shown anywhere |
| 2026-10-13 | Zero-credit grammar run on captured numeral clips | Grammar values match transcribe digits except formatting cases; incomplete numbers abstain | Values always agree → apply 007's rule: no reconciler, abstention only |
| 2026-10-17 | v2 set built | 240 utterances labelled in paise; bias control ready; ≥2,000 clean credits | Fewer credits → human slice at AMR-NB 0 dB only |
| 2026-10-24 | Line Noise Lab v2 run | Wrong-amount-confirmed = 0; control shows boosting | A wrong amount gets confirmed → add an abstain rule and rerun that slice; control fails → drop bias claims |
| 2026-10-27 | Transcribe decision | Transcribe caught ≥1 wrong amount the grammar passed → keep it | Otherwise drop it from intake |
| 2026-10-31 | End-to-end loop on Evon | 10 scripted calls sealed; ≥8 recover after re-ask | Evon not running → part names from a 65-word lookup; Groq is removed anyway |
| 2026-11-04 | Usefulness proof | One mechanic tries scripted estimates (if organisers allow) | Not allowed → Harshdip's own extempore demo, labelled as such |
| 2026-11-07 | Freeze | Every demo.md number reproduces from one command | Unreproducible numbers are deleted |
| 2026-11-10 | Submit | Real Deal submission with measured numbers only | — |
