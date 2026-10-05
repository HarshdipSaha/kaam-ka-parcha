# Money-Path Safety & Amount-Labelled Benchmark v2 Specification

> Written with the `to-spec` skill (mattpocock/skills) on 2026-10-05, then updated the same day with three owner decisions: **Gramvaani real phone calls are included**, **Timbre is tested too**, and **cost is not a constraint**. The owner still needs to run `/to-spec` personally for a full skill-driven rewrite; the skill can only be started by the user. This spec synthesises decisions already made; it introduces none. Sources: [council verdict 008](../ideas/council-real-audio-verdict.md) (its "Decisions for the Updated Spec" list), the surviving parts of the [007 verdict](../ideas/council-gpu-multilingual-verdict.md), [R9](../research/R9-real-audio-benchmark-analysis.md), and the current code. Triage label: `ready-for-agent`. Publication to GitHub Issues is pending (see Further Notes). AIDLC effort [`008`](../../aidlc-docs/efforts/008-real-audio-analysis-council-spec/effort-state.md). Vocabulary follows [`CONTEXT.md`](../../CONTEXT.md) and `AGENTS.md`.

## Read This First: The Simple Version

### What happened

Your other laptop sent 125 audio clips to Prisma, under 16 different conditions each (two Prisma modes, two phone-line types, four noise levels). That is 2,000 transcriptions, costing about 4,965 credits (≈ ₹99). The results were merged as PR #17. We then checked those results carefully (R9) and asked the council what they mean.

### What was wrong with the 2,000-audio run

1. **It never tested money.** No clip had a rupee amount with a known correct answer. The product's one promise ("a wrong amount never gets confirmed") was not measured at all.
2. **The scoring was unfair to Prisma.** In the dataset's answer key, every English word is written twice, once in Hindi script and once in English ("मॉडल model"). Prisma writes it once, so it got marked wrong for words it heard correctly. Fixing the answer key drops the error from about 16% to about 7%.
3. **The noise was too easy.** We only used a recording of an idling engine. A steady hum like that barely affects a phone line, so 10 dB, 5 dB and clean all scored the same. Only the cheap 2G codec (AMR-NB) at the loudest level hurt. No wrench bangs, horns, packet loss or real phone calls were tested.
4. **The two Prisma passes are basically one.** `transcribe` and `verbatim` gave the same words 90% of the time. The only real difference: `transcribe` writes "50", `verbatim` writes "पचास". So comparing them only catches formatting slips like `04:30 100`. It does **not** catch Prisma mishearing a number or dropping "hazaar".
5. **Wrong audio, not mechanics.** The clips were professionals from 23 fields (medicine, film, engineering), mostly reading sentences aloud. A mechanic speaks freely, and freely spoken clips were about twice as hard.
6. **Small data problems.** One clip (i036) has the wrong answer text. One clip (i109) came back empty while the API still said "success". The five workshop clips were scored against YouTube auto-captions and their text was redacted, so they prove nothing.

### How to fix it, simply

| Problem | Fix |
|---|---|
| Money never tested | Build ~240 clips where we know the exact amount in paise: Timbre-voiced scripted estimates, your own freely spoken takes, and short "nahi, saade teen sau" corrections. Score one thing: did a wrong amount ever reach the card unchallenged? |
| Unfair answer key | Clean the reference before scoring (remove the duplicate English word and tags like `<stammers>`). The script already does this. |
| Easy noise, no real calls | Stop running engine-idle steps. Test clean audio and 2G at the loudest level, **and add Gramvaani's real Indian phone calls** (decided; see below). |
| Read-back never checked | **Test Timbre too**: every amount the customer will hear goes Timbre → phone line → Prisma → our number reader, and must come back as the same paise value (decided; see below). |
| Two passes are one witness | Read amounts with our own number-reading code on the `verbatim` text. If anything looks incomplete, empty or contradictory, **ask again** instead of guessing. The customer's read-back is the final check. |
| Empty "success" results | Treat an empty transcript, a 504 or a 429 as "please repeat", never as "no items". |
| Bad clips | Exclude i036 and the auto-caption clips from scores. |

### Was this run based on the benchmark plan in R4?

**No.** [`R4`](../research/R4-technical-angles.md) recommended a different plan, and the run did not follow it:

| R4 recommended | What the 2,000-audio run used |
|---|---|
| **Gramvaani** (OpenSLR 118): the only public corpus of *real* Indian phone calls, which Gnani itself calls one of the datasets that matter most | Not used |
| **Kathbath-noisy**, **MUCS** (code-switched Hindi-English), via **Vistaar** (the same test sets Gnani benchmarks on) | Not used |
| Real noise banks: **MUSAN**, **DEMAND**, **Vaani-Noise** (154 h of Indian street and household noise) | One engine-idle recording |
| **SynthCall-IN**: Timbre-voiced scripted calls with exact amounts, phones and dates (template T2, entity accuracy) | Not built |
| Codecs G.711, AMR-NB 12.2 and 4.75, GSM, Opus with packet loss; SNR down to −5 dB; 200+ clips per condition | G.711 and AMR-NB 4.75 only; clean to 0 dB; no packet loss |
| Dataset | **IndicContextEval** (AI4Bharat, CC BY 4.0): broad professional Hindi. Not in R4's table |

IndicContextEval was a reasonable choice for "can Prisma handle varied Hindi" with a clean licence, but it answers a different question from the one R4 set up.

**Owner decision (2026-10-05): we must use Gramvaani as well.** Gramvaani's real phone-call recordings are a required part of benchmark v2, not an option. We use the Vistaar Gramvaani test slice from R4 in full. Verified on 2026-10-05: 1,032 utterances, 2.80 h, stored at 16 kHz by the Hugging Face mirror and downsampled to 8 kHz by us. 291 clips already contain clipping from the real phone line, and those are reported as their own group. This gives a believable answer to "how does it do on real Indian phone calls?", which R4 called the question every Gnani interviewer will ask. It also brings Noise Canceller back into play. The rules that come with it:
- Gramvaani is "free for academic purposes; commercial use by permission". Use it for evaluation only, never as demo audio. Never commit or redistribute its audio. Email contact@gramvaani.org before showing any Gramvaani result publicly or in the submission.
- Adding it reopens the council's award choice. Real Deal stays the working target until the Gramvaani and Timbre results are in, then the award is decided again.

### Cost: don't worry about it

**We have a lot of credits.** The owner reports about ₹4,700 left at roughly 50 credits per ₹1, so about **235,000 credits**. For scale:

| Run | Rough cost |
|---|---|
| The whole 2,000-audio run (PR #17) | ≈ ₹99 |
| Gramvaani slice, both Prisma passes (2.80 h of audio, measured from the real files) | ≈ ₹81 (≈ 4,025 credits) |
| Amount-labelled v2 set: Timbre rendering plus Prisma, both passes, both conditions | ≈ ₹28 (≈ 1,400 credits, estimate) |
| Timbre echo test, screen stage (13 voices × 2 formats × 37 stress amounts) | ≈ ₹272 (≈ 13,600 credits) |
| Timbre echo test, confirm stage (top 3 voice/format pairs × 120 estimate cards) | ≈ ₹140 (≈ 7,000 credits) |
| **Everything in this spec** | **≈ ₹520 (≈ 26,000 credits), about 11% of the balance** |

So **nothing in this spec is trimmed to save credits.** The limit is the owner's time, not money. Every run still records what it spent, so the numbers stay auditable.

### Why was only Prisma benchmarked?

1. **Prisma is Gnani's only speech-to-text model**, and the contest requires Gnani models. There was nothing else from Gnani to test for that job.
2. **Comparing against Whisper, Google and the like is off-limits for public material.** The EULA guard allows only our own pipeline's before/after deltas. An internal comparison would teach us little about *our* product anyway.
3. **But the run should not have stopped at Prisma.** The money risk sits in three places, and two were never measured:
   - **Prisma** hearing the number: measured, but without amount labels.
   - **Timbre** saying the number correctly in the read-back: not measured. R4's "Echo Test" (Timbre → phone line → Prisma, check the amount comes back the same) does this cheaply.
   - **Evon/the extractor** structuring the card: not measured. Under this spec, Evon no longer touches amounts, but its line items still need a check.

### Why wasn't Timbre tested, and what we do now

**Why it was missed:** effort 006 was set up as a speech-to-*text* benchmark. It asked "how well does Prisma hear Hindi?" and never looked at the other direction, Timbre *speaking* to the customer. But the customer's "haan" only protects the money if they heard the right number. If Timbre says "saade teen sau" when the card says ₹450, or the 2G line garbles "dedh hazaar", the customer could confirm a number nobody said. That is the same failure the whole product exists to prevent.

**Owner decision (2026-10-05): Timbre is tested too.** In simple terms:
1. Take every amount the customer would hear (the v2 estimates, the corrections, plus a list of tricky ones like saade/sava/paune/dedh/dhai, ₹1,050 vs ₹1,500, lakh).
2. Build the read-back exactly as the product does, and have Timbre speak it.
3. Push the audio through the same fake phone line (clean, and 2G at the loudest level).
4. Let Prisma transcribe it, and run our number reader on the result.
5. The amount must come back as the **same paise value**. Anything else is a failure.

We try **all 13 Timbre voices that speak Hindi** and **two ways of writing amounts**: ₹ digits, which is what the product sends today (Timbre normalises them itself), and Hindi number words written by our own code. A cheap **screen** stage runs every voice and format on 37 tricky amounts. A **confirm** stage then runs the best 3 on all 120 estimate cards. We keep the voice and format that survive the phone line best. The owner listens to every failure, because this round trip mixes Timbre's errors with Prisma's and only a human can tell which one slipped.

## Problem Statement

A mechanic dictates an estimate, the customer hears it read back and says "haan", and the job card is sealed. That sealed rupee amount is the whole product. Today nothing guarantees it is right:

- **A non-Gnani LLM decides the money.** Intake and every re-ask send Prisma's text to an external Groq model, which picks the amounts. Intake cannot run without it, and the README wrongly calls it optional.
- **The correction path is the weakest path.** A re-ask transcribes the customer's or mechanic's reply with the transcribe pass only, then lets the same external model parse the new amount. There is no verbatim evidence and no rule-based check.
- **Known failures are invisible.** Prisma's inverse text normalisation turned "saade chaar sau" into `04:30 100` (effort 005). On AMR-NB audio it once returned HTTP success with an empty transcript (effort 006, clip i109). Two HTTP 504s and earlier 429s have been seen. The product has no policy for any of these, so an empty or failed result could become "no items" or a stale amount.
- **The evaluation can't see the promise.** The 2,000-condition real-audio benchmark contains no amount labels, and its scores mix recognition error with reference artefacts: duplicated Latin glosses inflate CER by about 2.3×, and one clip has a mismatched label. Public-facing documents still carry unmeasured numbers and an unreproducible "74/74 PASS".
- **No real phone calls were tested.** Every degraded clip was clean speech pushed through a simulated line with engine-idle noise. That is too easy, and it isn't what Noise Canceller asks for.
- **The read-back is unverified.** Nobody has checked that Timbre says each amount correctly, or that it survives the phone line. The customer's confirmation is only a safety check if what they hear matches the card.

From the customer's side, a confident wrong amount at read-back is worse than being asked again.

## Solution

**A wrong rupee amount never gets confirmed.**

- **Amounts.** They come only from a deterministic numeral grammar applied to Prisma's verbatim pass, never from an LLM.
- **The transcribe pass.** It is kept as a formatting cross-check of the same decode, not as independent evidence.
- **Abstaining.** Whenever the grammar finds an incomplete number, the cross-check disagrees, or Prisma returns an empty result, 504 or 429, the system abstains on that field. It then asks a targeted re-ask through Timbre ("Brake pad kitne ka? Sirf rakam boliye"), and the customer's read-back confirmation remains the final check.
- **Corrections.** These get the same treatment as intake.
- **Line items and part names.** Evon, Gnani's own LLM, structures them and is never allowed to touch amounts. Groq leaves the shipped path.
- **Evaluation.** The Line Noise Lab gains three things. An amount-labelled benchmark (v2) whose headline metric is the wrong-amount-confirmed rate, which must be zero, with abstain rate and recovery-after-re-ask reported as its costs. A Gramvaani real-telephone slice. A Timbre echo test that proves the read-back says the right number. The harness is fixed so every number is fair and reproducible from one command. Cost is not a constraint.

## User Stories

1. As a mechanic, I want the amount I speak in Hinglish ("saade chaar sau", "dedh hazaar", "paune do hazaar") to land on the job card as the exact paise value, so that I never have to correct the bill by hand.
2. As a mechanic, I want the app to ask me again for one specific amount when it isn't sure, instead of guessing, so that the customer never hears a wrong number from my workshop.
3. As a mechanic, I want a re-ask to name the item it is asking about, so that I can answer with just the amount while my hands are busy.
4. As a mechanic, I want the rest of the job card to stay unchanged when one amount is re-asked, so that a single unclear number doesn't make me repeat the whole estimate.
5. As a mechanic, I want an empty or failed transcription to be treated as "please repeat", not "no items", so that a network glitch never wipes my estimate.
6. As a mechanic, I want the card to tell me which amounts are still awaiting confirmation, so that I know what the customer will be asked.
7. As a mechanic, I want part names I say in Hinglish ("clutch plate", "brake pad") to be recognised and named correctly on the card, so that the customer understands what was repaired.
8. As a customer, I want every amount read back to me before anything is sealed, so that I agree to the real total.
9. As a customer, I want to correct one amount by saying only the number, so that fixing a mistake takes one short reply.
10. As a customer, I want a correction I speak over a poor phone line to be checked as strictly as the mechanic's original estimate, so that my correction can't introduce a new wrong number.
11. As a customer, I want the system to ask me again if it didn't catch my correction, rather than keep the old amount silently, so that what I said is what gets sealed.
12. As a customer, I want the read-back to repeat an amount that was re-asked, so that I can hear the final figure before I say "haan".
13. As a customer, I want a short, clear prompt when the system needs a number again, so that I'm not confused by a long repeat of the whole estimate.
14. As a customer, I want the one-tap digital confirmation to remain available when voice keeps failing, so that a bad line doesn't block me.
15. As a workshop owner, I want sealed job cards whose amounts never differ from what was spoken and confirmed, so that verbal disputes at pick-up stop.
16. As a workshop owner, I want the sealed PDF to keep both Prisma transcripts as evidence, so that any dispute can be checked against what was actually said.
17. As a workshop owner, I want the system to keep working when the external network hiccups, by asking again instead of failing, so that drop-off isn't delayed.
18. As the builder, I want the money path to depend only on Gnani models and my own deterministic code, so that the project meets the contest's genuine-use rule.
19. As the builder, I want the extractor endpoint to be selectable by configuration, with Evon as the shipped provider, so that I can run Evon locally, on a rented GPU or on a hosted quant without code changes.
20. As the builder, I want the system to keep running when the Evon endpoint is down, by holding line items for review while the grammar still produces amounts, so that a demo never silently falls back to a non-Gnani model.
21. As the builder, I want the transcribe pass described everywhere as a formatting cross-check, never as independent verification, so that I don't overclaim in the interview.
22. As the builder, I want each abstention to record its reason (incomplete number, cross-check disagreement, empty transcript, 504, 429), so that I can measure which rule is doing the work.
23. As the builder, I want the Line Noise Lab to score an empty transcript returned with HTTP success as a hard failure, so that silent empties never look like clean idle output.
24. As the builder, I want benchmark references canonicalised (disfluency tags stripped, duplicated Latin glosses removed), with the original kept alongside, so that scores reflect recognition and not reference formatting.
25. As the builder, I want clips with a known label mismatch (i036) and the auto-caption workshop slice excluded from scored results, so that bad references don't distort the numbers.
26. As the builder, I want every benchmark row to carry a paise label where an amount exists, so that the Lab can compute the wrong-amount-confirmed rate directly.
27. As the builder, I want the Lab's headline output to be the wrong-amount-confirmed rate, with abstain rate and recovery-after-re-ask beside it, so that the evaluation measures the product's promise and its cost.
28. As the builder, I want a positive control for the bias list, meaning audio where a biased word should change the output, so that I can tell "no bias insertions" apart from "bias was silently ignored".
29. As the builder, I want benchmark v2 to report every slice separately (Timbre-voiced estimates, my extempore takes, short corrections, Gramvaani, and the Timbre echo test), so that synthetic speech can't hide where real speech is hard.
30. As the builder, I want the amount-labelled slices to run G.711 clean and AMR-NB 4.75 at 0 dB, so that the runs target the only simulated condition R9 showed to be harmful.
31. As the builder, I want each live run to record its estimated spend and the key it used, so that spending stays auditable even though cost is not a constraint.
32. As the builder, I want the R9 analysis reproducible from one command, so that any number I show can be regenerated in front of an interviewer.
33. As the builder, I want a measured decision point on whether the transcribe pass stays, based on whether it caught any wrong amount the grammar alone would have passed, so that the second pass earns its latency.
34. As the builder, I want public material limited to own-pipeline relative deltas after organiser consent, so that I respect the EULA guard and the misleading-demo rule.
35. As the builder, I want the benchmark to include Gramvaani's real Indian phone calls, so that "how does it do on real phone calls?" has a measured answer.
36. As the builder, I want Gramvaani audio scored at its own telephone quality (downsampled to 8 kHz mono, never upsampled, no extra noise or codec added), so that the slice measures real phone audio and not my simulation.
37. As the builder, I want every number spoken in a Gramvaani utterance read by the same numeral grammar and compared with the reference value, so that I can count confident wrong numbers on real phone speech even though Gramvaani has no rupee labels.
38. As the builder, I want Gramvaani audio kept out of the repository and its results kept private until Gram Vaani grants permission, so that I respect its academic-use licence.
39. As the builder, I want Gramvaani results to decide whether a Noise Canceller claim is supportable, so that the award choice rests on real telephonic audio and not on engine-idle simulation.
40. As a customer, I want the read-back voice to say every amount clearly enough to survive a bad phone line, so that the number I confirm is the number on the card.
41. As the builder, I want every amount the customer will hear sent through Timbre, the phone-line chain, Prisma and the numeral grammar, and required to come back as the same paise value, so that the read-back is proven, not assumed.
42. As the builder, I want the echo test to include tricky amounts (saade, sava, paune, dedh, dhai, ₹1,050 vs ₹1,500, lakh), so that the hardest spoken forms are covered.
43. As the builder, I want to compare all 13 Hindi Timbre voices and two amount formats (today's ₹ digits vs Hindi words rendered by our code) on that round trip, so that the product uses the voice and wording customers hear most reliably.
44. As the builder, I want a clean, no-phone-line control in the echo test, so that I can tell Timbre problems from phone-line damage.
45. As the builder, I want to listen to every echo-test failure and a sample of passes, and label each failure as Timbre, phone line or Prisma, so that the round trip's mixed errors are separated by a human.
46. As the builder, I want Timbre's time to first audio recorded for each read-back, so that I know how long the customer waits on the line.
47. As a Gnani interviewer, I want to see the wrong-amount-confirmed rate with its sample size, conditions, date and cost metrics, so that I can judge the safety claim on evidence.
48. As a Gnani interviewer, I want to see that the project abstains on deletions and empty outputs, so that I can trust its failure behaviour on noisy calls.
49. As a Gnani interviewer, I want evidence that all three Gnani models (Prisma, Timbre and Evon) were measured on the job they do, so that I can see genuine, load-bearing use of the stack.
50. As a contest judge for Real Deal, I want to see the loop working end to end for a real trade, so that I can judge real-world usefulness.
51. As a contest judge for Noise Canceller, I want results on real telephonic audio rather than simulated noise, so that the claim matches the award's criteria.

## Implementation Decisions

- **Primary metric.** The wrong-amount-confirmed rate on the amount-labelled set is the headline evaluation outcome, with a target of zero. Abstain rate and recovery-after-re-ask are mandatory companion metrics. CER/WER stay internal diagnostics.
- **Numeral grammar module (new, deterministic, no network).**
  - Input: verbatim-pass text, Devanagari or romanised.
  - Output: amount mentions with their transcript span and a value in paise, or an explicit *incomplete* result.
  - Scope: units (ek … ninyanve); multipliers (sau, hazaar, lakh); fractional prefixes (saade +½, sava +¼, paune −¼, dedh 1½, dhai 2½); digits.
  - Distractors not treated as money: time expressions, years, vehicle numbers.
  - A dangling fraction word or a missing multiplier is *incomplete*, never a guessed value.
- **Money path at intake.** The intake operation runs the verbatim pass and gives its text to the numeral grammar. It runs the transcribe pass sequentially as a value cross-check. Each line item's amount is set only when the grammar yields a complete value and the transcribe pass does not contradict it. Otherwise the amount stays unset, and the field is marked for re-ask with an abstention reason.
- **Amounts attach to items deterministically.** Grammar amounts are attached to line items by deterministic rules over transcript spans. When attachment is ambiguous, the amount stays unset and the field goes to review. No LLM participates in attaching or producing amounts. *(This follows from "amounts from the grammar; Evon never touches amounts". See Further Notes.)*
- **Money path at re-ask and correction.** The re-ask operation uses the same verbatim + grammar + cross-check path as intake, scoped to the one requested field. A successful re-ask updates only that field; unrelated items and evidence are preserved. An unresolved re-ask leaves the field unset and re-asks again within the existing retry limit, after which the existing digital fallback applies.
- **Provider failure policy.** An empty transcript with HTTP success, an HTTP 504, or an HTTP 429 from Prisma during intake or re-ask leads to abstention with a recorded reason and a targeted re-ask. None of them may be interpreted as "no items" or reuse a previous value. No silent automatic retries in the product path. The Lab's existing stop-on-provider-error budget behaviour is unchanged.
- **Abstention reasons** are recorded per field on the session and in the transcript log: `incomplete_number`, `crosscheck_disagreement`, `empty_transcript`, `provider_504`, `provider_429`, `ambiguous_attachment`, `out_of_range`. The last one is derived from the existing `LineItem` limit of ₹1,00,000. They become part of the canonical audit manifest so the sealed evidence shows why a field was re-asked. A spoken total ("kul …") is checked against the sum of the items rather than counted as an item; a mismatch abstains every amount.
- **Read-back invariant.** Every amount is spoken in the Timbre read-back before the session can reach `confirmed`. A re-asked amount is read back again. The current rules about expected revisions and immutable confirmed sessions are unchanged.
- **Extractor provider.**
  - The extractor provider setting is honoured, and Evon (an OpenAI-compatible endpoint) is the shipped provider.
  - The extractor's responsibility shrinks to line items, part names and delivery date, each tied to transcript evidence. It sends thinking-off and a JSON schema.
  - The Groq default is removed from the shipped configuration. The README describes the extractor as required.
  - If Evon is unavailable, line items are held for review while the grammar still sets amounts. There is no fallback to a non-Gnani model.
- **Line Noise Lab fixes.** The runner and report gain:
  - reference canonicalisation (strip tags; drop a Latin gloss directly following a Devanagari token), keeping the original reference;
  - an `empty_transcript` outcome distinct from success;
  - an exclusion list for known label mismatches, starting with i036;
  - exclusion of auto-caption slices from scored aggregates;
  - per-row paise labels and the three amount metrics;
  - a bias positive-control condition.
- **The R9 analysis** remains reproducible from one standalone command over the benchmark bundle.
- **Benchmark v2: amount-labelled slices.**
  - About 240 utterances, all labelled in paise:
    - 120 Timbre-voiced scripted estimates;
    - 80 extempore takes by the builder, kept internal until the organisers rule on real-person audio;
    - 40 short number-only corrections.
  - Conditions: G.711 clean and AMR-NB 4.75 at 0 dB.
  - The product's 65-word bias list is used, with the positive control.
  - Slices are always reported separately.
- **Benchmark v2: Gramvaani real-telephone slice (owner decision, mandatory).**
  - Source: the Vistaar Gramvaani test slice from R4, 1,032 utterances of spontaneous Hindi over a real IVR phone line, run in full.
  - Audio: downsampled to 8 kHz mono and never upsampled. No added noise or codec, because it is already real telephone audio. Both Prisma passes run on it.
  - References go through the same canonicaliser as every other slice.
  - Metrics (private):
    - canonicalised CER/WER;
    - silent-empty and deletion-heavy rates;
    - latency;
    - **numeral-value accuracy** on utterances whose reference contains a number. The grammar runs on the verbatim pass and is compared with the reference value and with the transcribe pass's digits.
  - A grammar value that differs from the reference and is not flagged incomplete counts as a *confident wrong number*. This is the Gramvaani analogue of the primary metric.
  - Licence handling: evaluation only, never demo audio. Audio stays under the ignored private directory; only clip IDs, hashes and metrics are committed. The Gram Vaani source is cited. No Gramvaani-derived number appears in public material or the submission until Gram Vaani's permission (contact@gramvaani.org) and the organisers' consent are recorded.
- **Timbre echo test (owner decision, mandatory).**
  - Inputs: every amount in the v2 scripted estimates and corrections, plus a stress list of hard spoken forms (saade, sava, paune, dedh, dhai, near-collisions like ₹1,050 vs ₹1,500, and lakh amounts).
  - Pipeline: the read-back text is built exactly as the product builds it → Timbre speaks it → the product's phone-line chain → Prisma verbatim pass → numeral grammar. The result must equal the card's paise value.
  - Arms:
    - every Timbre voice that supports `hi-IN` (the count is read from Timbre's voice list at run time);
    - two amount formats: ₹ digits as the product sends them today (`format_rupees`, normalised by Timbre), and Hindi number words rendered by our own deterministic code;
    - two stages: **screen** (all 13 voices × both formats on 37 stress amounts), then **confirm** (the top 3 voice/format pairs, ranked on AMR-NB 4.75 at 0 dB, on all 120 estimate cards);
    - the read-back is synthesised without the DPDP consent sentence, because "DPDP Act 2023" would parse as a number;
    - conditions: clean with no phone line (control), G.711 clean, and AMR-NB 4.75 at 0 dB.
  - Metrics: read-back round-trip exact-match rate per voice × format × condition, and Timbre time-to-first-audio p50/p95.
  - Human check: the builder listens to every round-trip failure and a 10% random sample of passes. Each failure is labelled *Timbre said it wrong*, *phone line damaged it*, or *Prisma misheard it*, because the round trip mixes errors from two models.
  - Outcome: the product's read-back voice and amount format become the combination with the best round-trip result on AMR-NB 4.75 at 0 dB; on a tie, keep the current voice. Every amount pattern that still fails on the chosen combination is recorded as a known read-back risk.
  - The Timbre-voiced v2 slice (Prisma hearing Timbre speech) and the echo test (Timbre's read-back being correct) measure different things and are reported separately.
- **Transcribe-pass decision.** After the v2 run, the transcribe pass stays in intake and re-ask only if it caught at least one wrong amount that the grammar alone would have passed. Otherwise it is removed from the product path.
- **Credits: cost is not a constraint (owner decision).**
  - The owner reports about ₹4,700 left at roughly 50 credits per ₹1, so about 235,000 credits.
  - No benchmark, slice or arm in this spec is reduced to save credits. The binding constraint is the builder's time.
  - Each live run records its estimated spend and the key used. The Lab forecast stays as a runaway guard against the configured key's balance.
  - The council's rule that the ten additional keys from effort 006 need recorded provenance before use still applies to those specific keys.
- **Integrity corrections, delivered alongside this work:**
  - the README no longer calls the extractor optional;
  - the demo storyboard drops every unmeasured number;
  - the gates ledger stops claiming "74/74 PASS" unless it is reproduced by a runnable command.
- **Award target: reopened (owner decision to add Gramvaani).**
  - Real Deal stays the working target.
  - The award is chosen again once the Gramvaani slice and the Timbre echo test have run.
  - Noise Canceller may be claimed only if the Gramvaani results support it on real telephonic audio, never from engine-idle or synthetic audio alone.

## Testing Decisions

- **A good test checks observable behaviour at the highest available seam.** Given the audio-bytes stand-in and what the fake Prisma returns, assert what the session, job card, transcript log and read-back contain. Don't test the grammar's internal tokenisation or the order of internal calls. Ordinary tests must use no API credits.
- **Seam 1, product (existing).** The workflow's public operations (intake, re-ask, start read-back, reply) are driven through the HTTP app with the existing offline fake services. The fake Prisma returns scripted transcribe and verbatim text per call, and the fake extractor and fake Timbre are used. Covered here:
  - grammar outcomes, table-driven: complete values, fractional prefixes, incomplete numbers, distractors;
  - cross-check disagreement, including the effort-005 `04:30 100` vs "saade chaar sau" case;
  - empty-transcript, 504 and 429 abstention;
  - re-ask on corrections, preservation of unrelated fields, and the read-back of re-asked amounts;
  - abstention reasons in the audit manifest;
  - Evon-unavailable behaviour.
- **Seam 2, evaluation (existing).** The Line Noise Lab runner and report run over a small manifest with the existing fake Prisma client. Covered here:
  - reference canonicalisation;
  - the `empty_transcript` outcome;
  - exclusion lists;
  - the wrong-amount-confirmed, abstain and recovery-after-re-ask metrics;
  - the bias positive control;
  - forecast refusal above the configured key's balance;
  - Gramvaani preparation: downsampling only (an upsampling attempt is rejected), no added degradation, clip IDs and hashes recorded, no audio written outside the private directory;
  - numeral-value scoring on a Gramvaani-style row: a correct value, a confident wrong number, and an incomplete number;
  - an echo-test mode driven by the existing fake Timbre and fake Prisma. A read-back whose fake transcription returns a different amount must count as a round-trip failure; voice, format and condition must be recorded per row; the clean control row must be present.
- **No new seams are proposed.** The numeral grammar is exercised through Seam 1. A direct grammar-level table test would be a third seam, added only if Seam 1 table tests become too slow.
- **Prior art:**
  - the workflow, session, fallback and reply test suites, which use the shared fake services;
  - the lab runner tests, including the fake-client 429 stop and chunking regressions;
  - the lab metrics tests;
  - the real-audio dataset selection tests, which are the model for Gramvaani manifest preparation;
  - the existing fake Timbre client in the shared fixtures, which is the model for the echo-test fakes.

  Mirror their style: one observable failure per regression, written before the fix.
- **Live checks** (benchmark v2, the Gramvaani slice, the echo test, end-to-end calls) are recorded runs with their spend logged and outputs under the ignored private directory. They are evidence, not tests.

## Out of Scope

- Any LLM (Groq, Evon or other) producing, attaching or correcting amounts.
- Re-transcribing only the amount span. Prisma REST/WS return no word timestamps or confidence.
- Parallel Prisma calls and streaming transcription for intake. Concurrency limits are unmeasured, and 429s have been observed.
- Silent automatic retries in the product path.
- Treating two-pass agreement as independent verification, in code, docs or the pitch.
- 10 dB and 5 dB SNR steps, impulse-noise profiles, packet loss, the A100/GPU sprint, QLoRA, multilingual or regional read-back legs. These are excluded for focus and time, not cost.
- Using Gramvaani audio in the demo, committing it, or publishing Gramvaani-derived numbers before Gram Vaani's permission and the organisers' consent.
- Timbre speed and prosody tuning beyond the voice and amount-format arms.
- A run-time echo check inside the product (Prisma re-checking each read-back before it plays). See Further Notes.
- A public dataset release, growing the amount-labelled set beyond ~240 utterances before the v2 results are in, and any BFSI or collections pitch.
- Publishing absolute CER/WER, competitor comparisons, or the code-mixed scoring-artefact finding. The last stays for the interview.
- Noise Canceller claims based on engine-idle or synthetic audio, and Mixed Vibes claims based on the scoring-artefact finding.
- Spending credits from the ten additional keys before their provenance is recorded.

## Further Notes

- **Publication.** The repository's tracker is GitHub Issues, but `gh` is not installed on the machine that wrote this spec. To publish it, sign in as the HarshdipSaha account and run: `gh issue create --title "Spec: Money-path safety and benchmark v2" --label ready-for-agent --body-file docs/specs/money-path-safety-spec.md`. As the to-spec guidance warns, exclude this parent spec from any AFK agent that polls `ready-for-agent`, or remove the label after tickets are cut.
- **Owner decisions recorded 2026-10-05, after the council:**
  1. The Gramvaani real-telephone slice is mandatory.
  2. The Timbre model is tested with an echo test of every read-back amount.
  3. Cost is not a constraint (about ₹4,700 ≈ 235,000 credits).

  Decisions 1 and 3 change two council-008 items: the ≤ 2,000-credit v2 budget is lifted, and the award choice is reopened. The concrete echo-test arms (all Hindi voices; words vs digits; clean, G.711 and AMR-NB 0 dB; listening check on failures) were drafted to implement decision 2. Confirm them.
- **Implementation plan:** [`docs/superpowers/plans/2026-10-05-money-path-safety.md`](../superpowers/plans/2026-10-05-money-path-safety.md), written with the writing-plans skill. It has 17 tasks with tests and code snippets, verified data facts, and credit forecasts.
- **Full `/to-spec` rewrite.** The `to-spec` skill can only be started by the owner. Run `/to-spec` in Claude Code to regenerate this document from the conversation, which now includes these decisions.
- **Candidate follow-up (not decided):** a run-time echo check in which Prisma re-transcribes each read-back before it plays and blocks a mismatched amount. The echo test's results will show whether it is worth the extra ~2 s per read-back. R4 also lists the echo test as a Jugaad Genius-style use of the stack.
- **Organiser question to add:** whether public real-speech corpora such as Gramvaani and IndicContextEval may be used for evaluation under the synthetic-data rule.
- **Seams for owner review.** The to-spec process asks the owner to confirm the seams. Proposed: Seam 1 (workflow through the HTTP app with fake services) and Seam 2 (Line Noise Lab runner/report with the fake Prisma and fake Timbre clients, now including Gramvaani preparation and the echo-test mode), both existing, with no new seams.
- **One derived decision to confirm.** Deterministic attachment of amounts to items follows from the council's rule that no LLM touches amounts, but the council did not specify the attachment rule itself.
- **Dated gates** live in the [008 verdict](../ideas/council-real-audio-verdict.md#dated-gono-go-gates) and supersede the 007 gates where they conflict. First action before any code: record the configured key's real balance and the provenance of the ten keys, then send the organiser Discord questions.
- **Previous spec.** [`closed-loop-voice-sealing-spec.md`](closed-loop-voice-sealing-spec.md) remains the record of the phrasal prompting, fallback, QR verification, DPDP consent and impulse-lab work. This spec changes how amounts are produced and evaluated. Where the two conflict, this spec wins on anything that relies on an external extractor deciding amounts.
