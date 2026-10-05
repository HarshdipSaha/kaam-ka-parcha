# Council round 2: peer reviews (each reviewer saw A–E anonymised + one evidence file), 2026-10-05

Each reviewer read only [`framed-question.md`](framed-question.md), [`responses-anon.md`](responses-anon.md) and one evidence file. None saw [`mapping-secret.md`](mapping-secret.md).

| Reviewer | Evidence file | Strongest | Biggest blind spot |
|---|---|---|---|
| 1 | `docs/research/R9-real-audio-benchmark-analysis.md` | E | D |
| 2 | `aidlc-docs/efforts/006-real-api-real-audio-benchmark/construction.md` | E | D |
| 3 | `docs/ideas/council-gpu-multilingual-verdict.md` | E | D |
| 4 | `docs/abouthack.txt` | C | D |
| 5 | `docs/notes/02-speech-apis.md` | E | D |

## Review 1 (fact-checked against R9-real-audio-benchmark-analysis.md)

**1. Strongest: E.** It picks out the one real unknown, the rate at which wrong amounts get confirmed. It sees that agreement between two passes of the same decode can't catch a mishearing. It turns R9's deletion finding into a concrete guard: abstain when a number is incomplete, and treat an empty transcript as abstain. It also builds v2 on extempore speech, which is where R9 says the difficulty is. C has the best costed and sequenced plan, including a zero-credit grammar run on the 28 numeral clips. But C's Timbre-read v2 ignores R9 finding 3.

**2. Biggest blind spot: D.** It treats one-decode agreement as enough money safety. It wants to publicise a Prisma code-mixed-vs-Hindi comparison that R9 keeps private. It treats the keys as "if clean" rather than a hard stop. And it inflates scope (400–600 utterances, an open dataset, a banking pitch) for one person with five weeks.

**3. All missed:** the confirm/correct turn. The customer replies over the phone leg with short, number-only answers. That leg is AMR-NB, the codec behind R9's only real degradation and i109's silent empty. R9 has no clip under 6 s, so v2 needs a short-correction slice. The abstain rate should also be costed in re-ask credits and seconds. No one planned for 429 throttling either.

**Factual flags:** C: running the passes in parallel isn't a free "one async change"; R9 warns it doubles the burst rate (429s were seen in effort 005). C: no agreement check exists yet, so nothing "caught" the ₹450 failure. D: "roughly in half" is an unmeasured guess ([SPEC]) in R9. The code-mixed finding isn't on R9's list of shareable deltas. B/E: R9 rates grammar plus agreement "strengthened" and calls deletions "the safe failure direction". Their wrong-number scenarios are untested inference.

## Review 2 (fact-checked against effort 006 construction.md)

**1. Strongest: E.** E is the only response that turns findings 4 and 5 into a design. When both passes come from the same decode, their agreement can't catch a dropped "saade" or "sau". So safety has to come from three things: the grammar, abstaining when a number is incomplete, and the readback. E also treats an empty transcript as abstain. Its v2 targets extempore speech, which is where R9 locates the difficulty. C is the most actionable, with a zero-credit grammar run on numeral clips already captured. But C's v2 uses only Timbre, so it is read speech. C also says the cross-check "caught" ₹450, but no check existed yet.

**2. Biggest blind spot: D.** D calls the two passes a valid "agreement signal" and ignores deletions, the one error type agreement can't catch. It wants to publish Prisma CER by subset and never mentions the integrity items. It also widens scope (an open benchmark, 400–600 clips, impulse noise, packet loss, a pivot to finance) for one person with 5 weeks left.

**3. All missed:** The log puts the configured key at an estimated 4,965–4,970 of 5,000 credits used, about 30 left, with the balance unverified. No other key was loaded. So provenance gates every further Prisma or Timbre call, not just v2. That includes the demo and the submission, and they need a budget first. There were also two HTTP 504 errors in 2,002 requests, and the runner halts on any error. The product has no retry or abstain policy for a 504 during a live call.

**Factual flags:**
- A, B, E: "spent a whole key" is a local estimate. The provider balance was never checked.
- C, E: both size v2 "within one key" without noting that the original key is nearly spent.
- C: "one async change". The runs were serial with 1 s spacing and there is a 429 test, so concurrent calls are unmeasured.
- D: "fits the rules as a relative delta". The log says no public report was made: there was no organiser consent and no matched own-pipeline delta.

## Review 3 (fact-checked against council-gpu-multilingual-verdict.md)

**1. Strongest: E.** It follows R9 finding 4 through to its conclusion and still produces a design. Verbatim feeds Harshdip's own grammar. The system abstains on incomplete numbers (failures are deletions) and on empty transcripts. A transcribe of the amount span stays only if a measurement shows it earns its cost. V2 asks one question: how often is a wrong amount confirmed on extempore speech? This matches the verdict's line that "nothing recovers when both passes are wrong."

**2. Biggest blind spot: D.** It calls the one-decode agreement a "free number check" and misses that it can't catch a dropped "hazaar" (B and E both raise this). It plans 400–600 utterances, four conditions and a dataset release, all solo in five weeks. It also makes the research the shortlist post, against 007's ruling that the research belongs in the interview.

**3. All five missed:** Evon and Groq. Groq still decides intake and corrections (the ₹450→₹350 beat in demo.md) and Rule 3 requires Gnani's models, yet nobody updates that part of 007. Nobody applies 007's 14 Oct gate either. The two passes agree on number values, so verbatim rarely rescues a wrong transcribe. 007's kill rule then says "no reconciler, abstention only". That makes recovery after re-ask the key metric, and none of the five plans to measure it.

**Factual flags:** D's "Gnani's banking and finance business" has no support in the evidence (correction 6). D's scale breaks the 2,000-credit Lab cap in gates.md (correction 4), and its "fits the rules" assumes the deltas ruling, which is still pending. C says the "two-pass cross-check... caught the ₹450 failure". No cross-check exists: Groq picked the verbatim evidence (correction 1). C's Timbre-only v2 ignores the verdict's warning that synthetic sets flatter results.

> Chair's note: the contest page footer in `docs/abouthack.txt` lists "BFSI" and "Automobile" under Industries and "Collections" under Solutions. So D's claim that Gnani serves banking and collections *is* supported by that page, even though the 007 verdict's correction 6 said the evidence then available didn't support it. What remains unsupported is the claim that this would make Gnani adopt the component.

## Review 4 (fact-checked against abouthack.txt)

**1. Strongest: C.** It is the only one with an ordered plan that starts at zero credits: harness fixes, then integrity items, then the numeral grammar over the numeral clips already captured. That last step is a free first test of the promise. Its v2 is costed (1,600 credits, arithmetic correct) and fits in one key. Flaw: v2 uses only Timbre read speech, but R9 says extempore speech is the hard part. C should adopt E's extempore set and E's substitution case ("saade teen" heard for "saade chaar").

**2. Biggest blind spot: D.** It calls one decode written twice "the agreement signal the 007 verdict asked for." That misses B's and E's point: deletions and substitutions get through both passes. It also plans 400–600 utterances plus impulse noise and packet loss for five solo weeks, on keys whose source is unclear. Then it drifts into BFSI.

**3. All five missed:**
- The page says Prisma "streams in under 200ms." Nobody considers streaming as the fix for the ~15 s p95 in (e).
- Gnani lists **Automobile** as an industry, which fits a mechanic product directly.
- Mixed Vibes rewards a code-mixed "voice experience," not difficulty. A, B, C and E dismiss it on the wrong criterion.
- A, C, D and E back Real Deal ("most useful"), but none proposes proof that it is useful, such as a real mechanic trying scripted estimates. Nobody mentions Solo Ninja.

**Factual flags:**
- D's "first open Hinglish spoken-amount benchmark" and "Gnani engineers will share that" are unsupported.
- The rules B and D cite (misleading demos, relative deltas) are not on the page.
- The page says keys are created in the console and draw on one registration's 5,000 credits. "Ten 5,000-credit keys" doesn't fit that, which supports the caution in A, B, C and E.

> Chair's note: "misleading demos" (Rule 7) and the deltas-only EULA guard come from the full programme terms as cited in `README.md` and the earlier councils, not from the landing page's six summary points.

## Review 5 (fact-checked against 02-speech-apis.md)

**1. Strongest: E.** It names the one real unknown: a wrong amount reaching the customer's "haan". From finding 4 it draws the right design. `transcribe` is ITN applied to the same decode (§2.1), so Harshdip's own grammar running on verbatim can replace that pass, abstaining on incomplete numbers and empties. The ₹450 failure fits ITN's documented 24-hour time rule. Merge in C's execution plan (harness fixes, zero-credit grammar run).

**2. Biggest blind spot: D.** It treats two-pass agreement as the safety net and misses the deletion case that B and E raise: if "hazaar" drops, both passes agree on the wrong value. Its amount-span re-transcribe can't be built as described, because Prisma REST and WS return no word timestamps or confidence (§2.1, §2.2). C is right on this. D also spends the unexplained keys and puts Harshdip's own voice into a CC BY release while the synthetic-only ruling is pending.

**3. All five missed:** REST silently ignores an invalid `bias_list` (still returns 200), `bias_score` defaults to off, and every entry must be a single letter-only word. So "0 bias insertions" (finding 6) may mean boosting never ran. One multi-word or digit entry could silently void the 65-word list. The harness needs a positive control. Also, Prisma has no confidence field, so abstention can only come from grammar completeness.

**Factual flags:** D's claim that the span design "cuts credits and latency roughly in half" is unsupported: there are no span timestamps, and the calls run one after the other. C's 0.2 credits/s and ~1,600-credit figures come from R9; the file says pricing is undocumented. C's halving from parallel passes assumes concurrency, but rate limits are undocumented (only 429).

> Chair's note: effort 006's bundle README states the verbatim requests sent the 12 bias words "at the client default bias score of 1.0", so boosting was requested. Without a positive control, though, there is still no evidence the provider applied it. R9 finding 7 has been amended to say so. The "0.2 credits/s" rate comes from the repo's single-call probe (`docs/gates.md`), not from a published price.
