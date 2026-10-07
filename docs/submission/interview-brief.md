# Interview brief (for the owner; practise out loud, without notes)

Every number links to [`docs/gates.md`](../gates.md). Know what each number measures and what it does not: most of it is synthetic speech.

## Architecture (text diagram)

```
mechanic mic -> /workshop (browser) -> POST intake -> Workflow.intake
   Prisma transcribe pass + Prisma verbatim pass (bias words)
   Extractor (external LLM): item labels + delivery only
   money.decide_amounts: numeral grammar reads amounts, transcribe pass = formatting cross-check
   settle_card_amounts: amounts flagged until two recordings agree (reask / confirm_estimate)
   SessionStore: revisions, states draft -> review -> awaiting_reply -> fallback_ready -> confirmed
customer page -> Timbre read-back (Vikrant, amounts in words) over simulated G.711/AMR-NB + noise
   customer reply -> Prisma -> classify_reply (yes / no / unclear) -> confirm only on a clear yes for the current revision
confirmed card -> sealed PDF (embedded transcripts.json, audit-manifest hash) + WhatsApp text (clipboard)
```

## Money-path decisions and their numbers

1. **Amounts come from a grammar, not an LLM.** Money must be reproducible and auditable. Integer paise; unknown stays `None`.
2. **Prisma writes fractions as clock strings** (`04:30 100` for साढ़े चार सौ). Normalising them lifted re-ask recovery 73.3% -> 96.3% (1,000 live rows), 96.8% held-out. Section 11 of gates.md.
3. **One recording is never trusted.** A single accepted amount was wrong 2.2-2.4% (all at 0 dB). Two agreeing recordings: 93-95% settle at the first pair, 0.2-0.4% wrong at 0 dB, 0 wrong in 1,158 clean/control pairs.
4. **Rejected: "accept when both Prisma passes on one recording agree."** Offline on saved runs: 475 of 1,344 accepted, 19 (4.0%; 10.2% at 0 dB) wrong. The two passes are correlated evidence about the same audio.
5. **Look-alike numbers** (इक्कीस/इकतीस etc.) can fool two recordings the same way at 0 dB, so they need a third. Offline replay of the 1,930 saved rows caught all 3 wrong settles; cost 17% of benchmark settles needing a third take.
6. **Whole-estimate repeat** so a demo needs two recordings per estimate however many amounts there are.

## How the benchmarks were built, and their limits

Synthetic Timbre speech (13 voices) rendered from generated estimates, degraded with G.711 / AMR-NB and recorded engine noise at clean/10/5/0 dB; live Prisma calls; scoring is the product's own decision code. Limits: synthetic voices flatter recognition; one noise recording; no labelled real workshop speech yet (owner takes are one speaker, if scored); licensed real Hindi speech (IndicContextEval) is broad professional speech, not mechanics, and is reported as relative change only.

## What I would do with more time

Score several real mechanics' speech with consent; replace the clipboard with the WhatsApp Business API; run extraction on self-hosted Gnani Evon and compare field accuracy; add regional-language read-back with native-speaker-reviewed templates; human listening labels for the echo failures.

## Likely questions (short answers)

1. **Why not let the LLM read the amounts?** It can hallucinate digits; the grammar is deterministic, testable, and abstains on doubt.
2. **Why two recordings?** One recording's mistakes are correlated across both Prisma passes; a separate recording is independent evidence. Measured: 2.2-2.4% wrong alone vs 0.2-0.4% (0 dB only) for two.
3. **Where does it still fail?** Look-alike numbers at 0 dB; now routed to a third recording. Residual: -ty twins such as पंद्रह/पचास are not flagged.
4. **Is the 96.3% a real-world accuracy?** No. Synthetic speech, one noise source, amounts only.
5. **Why Vikrant?** Echo test: amounts in words, 120/120 at AMR-NB 0 dB vs Roopesh/digits 119/120 and Chitra/words 113/120. Synthetic; human listening pending.
6. **Why is the phone line simulated?** The contest data rule bans real recorded calls and numbers; the simulation uses G.711/AMR-NB encoding and noise, and the app discloses it.
7. **Which Gnani models do you use?** Prisma v2.5 (REST) and Timbre v2.5. Extraction is an external LLM, not Evon, because no hosted Evon API exists.
8. **What happens if the customer says something unclear?** It stays in review/retry/fallback; only a clear yes for the current read-back revision confirms.
9. **What if the mechanic corrects after the read-back?** The earlier read-back is invalidated; confirmation must refer to the current revision.
10. **How do you protect credits on a public demo?** Per-IP rate limits, session and upload caps, optional access code, generic errors.
11. **How is the sealed PDF verified?** Visible hashes, the embedded `transcripts.json` and the verify endpoint all derive from one canonical audit-manifest helper.
12. **What does the consent flow do?** Explicit consent capture is logged with a hash before a read-back reply counts.
13. **How did you avoid overclaiming?** Every figure maps to a gates.md row; public reports are fail-closed (no absolute CER/WER, no competitor comparisons, consent reference required).
14. **What did you learn from the benchmarks that changed the product?** Fraction formatting, the single-recording unsafety, and the echo-driven prompt reword.
15. **What would you build next?** Real-speech labelled set with consent, regional-language read-back, Evon extraction comparison.
