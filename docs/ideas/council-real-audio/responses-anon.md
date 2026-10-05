# Council round 1: anonymised responses (A–E), 2026-10-05

Each advisor read only [`framed-question.md`](framed-question.md) (no other files, no web) and answered independently in 150–300 words. Letters were randomised; the key is in [`mapping-secret.md`](mapping-secret.md) and was not shown to reviewers.

## Response A

In plain terms: Harshdip spent a whole credit key testing whether Prisma can transcribe professionals from 23 fields, mostly reading aloud, over an idling engine. The product makes one promise: "a wrong rupee amount never gets confirmed." Not one of the 2,000 rows checks a rupee amount. The benchmark measured everything except the promise.

Three things the insiders seem to be stepping past:

1. **"Ten additional 5,000-credit keys, provenance not recorded."** Each registration gets 5,000 credits. From outside, ten spare keys looks like ten registrations. If a Gnani engineer asks "where did those credits come from?", there needs to be a clean, written answer. Get that answer before spending a single credit.

2. **The two-pass "agreement check" compares two copies of the same decode.** R9 says the passes tie 88–91% of the time. When two witnesses are really the same person, their agreement proves very little. It does catch formatting slips like `04:30 100`, and that is worth having. Just don't describe it as independent verification in the interview, because they will see through it.

3. **The open integrity items.** The README calls a mandatory component "optional", `demo.md` has numbers nobody measured, and the "74/74 PASS" can't be reproduced. A reviewer clicks these first. They take an afternoon to fix. Fix them before running any new benchmark.

**Award:** engine noise turned out easy, and code-mixing turned out easy once the scoring was fixed. So neither "we beat a hard problem" story holds up. What remains is a mechanic, a job card and a price that can't be wrong. That's Real Deal.

**Next measurement:** record 100–200 short clips of people (Harshdip and friends first) dictating made-up estimates. Label each clip with the correct rupee amount. Score one thing: did the right number reach the card, or did the system ask again? And count an empty transcript returned with HTTP success as a failure every time.

## Response B

Finding 4 undercuts the 007 verdict, and nobody is saying it. If transcribe and verbatim are one decode with different number formatting, "two-pass agreement" is not two witnesses. It is one witness repeating itself. It catches formatting slips like `04:30 100` and nothing else. R9 also says the main failure is deletion. If "hazaar" drops out of "dhai hazaar", both passes agree on the wrong value, the grammar parses it cleanly, and the system confirms it. So "a wrong rupee amount never gets confirmed" is unproven. The only real evidence points to the one error type agreement can't catch. The real safety net is the customer readback, and no human has ever tested it.

Second: 2,000 rows used up a whole key and produced zero amount labels. The run measured CER on professional-domain Hindi, not the product's promise. Don't let a big row count pass for evidence.

Third, and the most dangerous: "ten additional 5,000-credit keys, provenance unrecorded." Credits come at 5,000 per registration. If those keys belong to other registrations, spending them breaks the rules, and a Gnani interviewer will spot it with one question. Harshdip should confirm in writing where the keys came from before spending one credit. Losing a ₹6 lakh offer over a credit shortcut is the worst outcome on the table.

Fourth: Noise Canceller is now the weakest award to claim. Engine-idle noise didn't hurt, G.711 barely moved, and there was no impulse noise, no packet loss and no real call. Claiming it would be a misleading demo. And the code-mixed clips only looked hard because of a scoring artefact.

Fifth: an amount set made with Timbre is Gnani speech feeding Gnani recognition. It is clean, read aloud and circular, so it will look good exactly where real extempore dictation is hard.

Also: the 65-word bias list is untested, and p95 means about 15 seconds of silence on a call. Fix the integrity items before showing any new number: the README calling the extractor "optional", and the unreproducible "74/74 PASS".

## Response C

Today is Monday, and Harshdip has 2,000 rows that say nothing about money. They measured transcription, but the product promises rupees. Here's the order of work.

**Today (zero credits):**
1. Fix the harness. Strip the Latin glosses from the references and drop i036. Score an HTTP-200 with an empty transcript as a hard failure, not just a high-CER row. Commit the R9 script so every number comes back from one command.
2. Fix the integrity items. Take "optional" out of the README, strip the unmeasured numbers from demo.md, and either rerun the 74/74 or delete it. That's about an hour, and an interviewer will find these first.
3. Write the numeral grammar. Run it over the numeral clips already captured in both passes. The value-agreement rate costs nothing, and it's the first number that actually tests the core promise.

**Tuesday:** fire both Prisma passes at the same time instead of one after the other. That takes p50 from about 4 s to about 2 s with one async change. Keep both passes. Re-transcribing only the amount span needs word timestamps and alignment code they don't have. The two-pass cross-check is the only thing that caught the ₹450 failure.

**Wednesday to Friday, benchmark v2:** about 200 scripted mechanic estimates with known paise amounts, voiced by Timbre. That's unblocked today, so don't wait on Discord. Use two conditions only: G.711 clean and AMR-NB 4.75 at 0 dB. R9 showed the 10/5 dB steps add almost nothing, so drop them. Prisma cost is roughly 200 × 10 s × 0.2 × 2 passes × 2 conditions ≈ 1,600 credits, plus Timbre. Put the 65-word bias list on that same audio. Two metrics: wrong amounts confirmed (must be zero) and abstain rate.

Don't touch the ten extra keys until someone writes down where they came from. Fit v2 inside one key.

**Award: Real Deal.** Engine-idle noise is too easy to carry Noise Canceller, and the Mixed Vibes case rests on a scoring fix. Real Deal only needs the loop working end to end, which is the work anyway.

**The spec leaves out** the GPU run, multilingual and further SNR sweeps.

## Response D

The council is reading R9 as a list of harness bugs. Harshdip is actually sitting on three assets they could publish.

1. **The scoring-artefact finding is the post that gets them shortlisted.** The story: a public Hindi benchmark writes every English word twice, and once that is fixed, Prisma scores slightly better on code-mixed speech than on pure Hindi. Gnani engineers will share that. It flatters the model, it is an own-pipeline result and it fits the rules as a relative delta. Ship the reference normaliser as a small open tool. It costs zero credits and gives them both post engagement and interview credibility.

2. **The two passes aren't redundant. They give a free number check.** It is one decode written two ways, digits and words. That is the agreement signal the 007 verdict asked for, and Prisma provides it already. Make the design verbatim-first, then re-transcribe only the amount span. That cuts credits and latency roughly in half and keeps the cross-check where the money is. Add a re-ask trigger for silent empties (HTTP success with a blank transcript), and send Gnani a reproducible bug report.

3. **Build the first open Hinglish spoken-amount benchmark.** If the keys are clean, spend the new credits on 400–600 amount utterances like "saade chaar sau", "paune do hazaar" and "dedh hazaar". Use Timbre voices plus Harshdip's own spontaneous takes. Label every rupee value. Test clean audio and AMR-NB at 0 dB, plus impulse noise and packet loss, and drop the middle SNR levels. Release it under CC BY so it lasts beyond the contest.

The biggest reframe: "a wrong rupee amount never gets confirmed" isn't a mechanic feature. It's a money-safety layer for any voice agent that hears amounts: loan collections, EMI reminders, kirana orders, insurance. That is Gnani's banking and finance business. Go for Real Deal, and walk into the interview with a component Gnani could deploy next quarter, not a student demo.

## Response E

Strip it back. The product makes one promise: a wrong rupee amount never gets confirmed. PR #17 spent a whole key on 2,000 conditions, and not one row tests that promise. CER across 23 professional domains is a proxy for a proxy. There are six questions here but only one real unknown: how often does a wrong amount reach the customer's "haan"?

R9 finding 4 quietly breaks the 007 verdict. If transcribe and verbatim are one decode with different number formatting, their "agreement" is not two witnesses. It is one witness asked twice. It catches formatting errors (the `04:30 100` case) and nothing acoustic. If Prisma hears "saade teen" instead of "saade chaar", both passes agree on the wrong ₹350. So the real safety comes from three things: Harshdip's own grammar run on the verbatim words, abstaining when a number is incomplete (failures are deletions, so the threat is a dropped "saade" or "sau"), and the Timbre readback. The transcribe pass mostly *adds* the one money failure seen so far. Run verbatim, parse it with their own grammar, and keep transcribe of the amount span only if a measurement shows it earns its cost. An empty transcript means abstain, never "no items".

Benchmark v2 should answer one question: on about 200 extempore mechanic utterances packed with amounts, what is the exact-match rate for amounts and the wrong-amount-confirmed rate? Test clean audio and AMR-NB at 0 dB only. That costs well under one key. Don't touch the "ten extra keys" until their provenance is written down. The rule is 5,000 credits per registration, and an unexplained pile of credits is the fastest way to lose credibility in the interview.

Award: the noise result is Prisma's win, not theirs, and code-mixing turns out fine once it is scored correctly. What they actually built is a confirmation loop for a real trade. That is Real Deal.
