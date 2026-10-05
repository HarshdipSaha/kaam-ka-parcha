# Council Verdict: Kaam ka Parcha, 3-day A100 window and multilingual-model ideas (2026-10-05)

> Method: `llm-council` skill (5 advisors → anonymised peer review by 5 reviewers, each fact-checking against one evidence file → chairman). Transcript: [`framed-question.md`](council-gpu-multilingual/framed-question.md), [`responses-anon.md`](council-gpu-multilingual/responses-anon.md), [`mapping-secret.md`](council-gpu-multilingual/mapping-secret.md), [`reviews.md`](council-gpu-multilingual/reviews.md). Inputs: [`R7`](../research/R7-a100-gpu-sprint.md), [`R8`](../research/R8-multilingual-models-arxiv.md). AIDLC effort [`007`](../../aidlc-docs/efforts/007-gpu-sprint-multilingual-council/effort-state.md). This verdict is a recommendation; nothing in it has been implemented.

## Where the Council Agrees

- **The plan doesn't fit the hours.** The Executor (B), the Outsider (C), the Contrarian (D) and the First Principles Thinker (E) each did the same sum and reached the same answer. R7 needs about 22 h before the GPU and about 40 attended hours during it, roughly 60 of the ~75 hours left. That leaves too little for real recordings, filming and posting. The Expansionist (A) missed this, and all five reviewers named A the biggest blind spot.
- **The money fix needs no GPU.** B, D and E agree that the real work is done by the numeral grammar on the verbatim pass plus one rule: accept an amount only when both passes agree, otherwise abstain and re-ask. That is CPU code. Evon is an upgrade, not a dependency, and the plan must win even if the GPU never arrives (B, C, D, E).
- **Real speech comes before GPU work.** B, C, D and E all treat W3 as the deciding unknown, because synthetic TTS sets score easier than real speech.
- **Stay on Hinglish only.** B, C, D and E drop QLoRA, Tanglish/Benglish and the regional read-back.
- **The research belongs in the interview, not the posts** (B, C, D, E).
- **Correct the false claims now.** All five agree. They differ only on how loudly.

## Where the Council Clashes

**What is Evon for?** A wants Evon at the centre and scaled up: a benchmark, a hosting recipe, 10× data. B keeps "Evon cross-examines Prisma" but makes Evon an upgrade. D asks the council's sharpest question: "What does Evon add over `a == b`?" D also warns that replacing Groq with a community quant on a free host is a worse dependency to have during a live interview. E's answer is a rule: no LLM decides money, whether it is Groq or Evon, and Evon only structures line items and part names. Reviewers 1 and 3 ranked B strongest because it is the easiest to act on. Reviewers 2, 4 and 5 ranked E strongest because its claim holds up under questioning. Both are right: take E's thesis and run it on B's schedule. Review 2 supplies the answer to D. Evon's value is in part names, where retrieve-then-select cut entity errors by 18–34% (R8 P2), not in amounts.

**How loud should the integrity fix be?** A wants W1/W4/W6 to be the headline. C says correct quietly, then pitch "I moved the money job to Gnani's model." D says disclose, because git history will show it anyway. E says skip the story and just make sure nothing is false. Confession-as-marketing reads well, but in an interview it invites "what else is wrong?"

**What a bad real-speech result means.** D says that below 70% exact the design collapses. E says it makes the case for abstain-and-re-ask stronger. Reviewers 2 and 3 backed E.

## Blind Spots the Council Caught

- **Abstaining has a cost.** If the system abstains on every disagreement, false confirmations drop to zero for free. Track two counter-metrics alongside it: review rate (kill if above 50% on clean cases) and recovery after re-ask (Review 1).
- **Answer (a) offline first.** Score at least 50 clips: when the transcribe pass is wrong, how often does the verbatim pass hold the right amount? If rarely, a reconciler has nothing to choose between. Also check that quantised Evon reliably follows a choose-or-UNRESOLVED schema (Review 2).
- **"Synthetic data only" may rule out real recordings.** The organisers still haven't said whether scripted roleplay by real people counts as synthetic, and that answer comes before W3 and before filming (Review 3). Noise Canceller also asks for "real telephonic audio". Recordings made beside a scooter and played over a simulated line don't meet that (Review 5).
- **The correction path also runs on Groq.** In demo.md's ₹450→₹350 beat, Groq parses the new amount. The storyboard has to be rewritten and re-filmed, and Evon has to be named, as Rule 3 requires (Review 4).
- **Does the community Q8_0 GGUF count as "Evon v3.3" under Rule 3?** Its card says quantisation loss was not measured against BF16 (Review 1).
- **A missed award:** Real Deal ("most useful real-world problem solved") fits a mechanic's estimate tool (Review 5).

## The Recommendation

The core promise is: **a wrong rupee amount never gets confirmed.** Money is decided by deterministic code, Evon structures everything else, and the GPU is a bonus measured run.

- **(a)** Not as framed. The core is the grammar, two-pass agreement, abstention and a targeted re-ask, applied to intake *and* to customer corrections. Evon replaces Groq for line items and part names, with constrained output. Evon may *suggest* which pass is right, but only deterministic agreement auto-accepts an amount.
- **(b)** Keep, in this order: R7 #2/P1 on CPU; a subset of P4 (confident-wrong rate, the "right in either pass" upper bound, review rate, the real anchor set, a frozen split); R7 #1; R7 #4, recorded during the window; R7 #5, cut down to one hosted quant plus a CPU fallback; P2 if hours remain; R7 #3, cut to about 40 cases; P8 as a one-hour check. Drop R7 #6 and #7, and P3, P5, P6 and P7.
- **(c)** Before the window: the integrity fixes, the money path, the eval runner, the offline verbatim check, an Evon-ready payload, and a GGUF smoke test on a CPU box. During it: one scripted batch that runs unattended, at most 12 attended hours, and export a Q4_K_M as well. After it: a hosted quant plus the deterministic fallback. If there are no dates by 18 Oct, plan for no GPU. If the window starts after 1 Nov, use it only for footage.
- **(d)** Hinglish only. Benglish would cost 8–14 h at medium-to-high risk, and it falls under Mixed Vibes, not Main Character.
- **(e)** Disclose it, but don't make it the headline. Put the fixes to the README, demo.md and gates.md in one dated corrections note. In the interview, say it in one sentence: "A non-Gnani model was deciding money, so money moved to code."
- **(f)** Public: the plain-language W2 moment, plus "keep numbers out of every text generator". Claim the re-ask only once it is built and filmed. Interview: choosing a hypothesis beats free correction, 1-best free correction made WER worse, nothing recovers when both passes are wrong, depth beat breadth, LLM judges inflate scores, synthetic sets flatter results.
- **Awards:** keep Noise Canceller as primary only if real phone-call audio is allowed. Otherwise make Real Deal primary and Mixed Vibes secondary.

## The One Thing to Do First

Today, post one message on the organisers' Discord that asks four things:
1. Does scripted roleplay by real people count as synthetic data?
2. May the recordings be real phone calls?
3. Does a community Q8_0 GGUF satisfy Rule 3?
4. Can own-pipeline deltas be published?

Every later gate depends on these answers.

## Factual Corrections to Carry Forward

1. W2 is a one-pass-right case. The verbatim pass held ₹450, and the transcribe pass returned `04:30 100`. No re-ask happened; Groq picked the verbatim evidence.
2. There is no re-ask, reconciler or rule-based line-item extractor yet. Amounts can leave Groq once the grammar ships; line items leave when Evon is wired. Groq cannot be out of the critical path "today".
3. Harshdip would not be first to make Evon easy to run. A community GGUF, a luminenio ZeroGPU Space and vLLM self-hosters already exist.
4. 10× data is unaffordable. At about 6.75 credits per audio case, 1,600 cases cost about 10,800 credits against 4,980 left, and gates.md caps the Lab at 2,000. Q8_0 also leaves only about 5–6 GiB for batching.
5. Kaggle fits only Q4_K_M or IQ4_XS, not the 31.45 GiB Q8_0.
6. The evidence does not support "Gnani sells into banking and collections".
7. The Oct 7 gate measures only the transcribe pass. Its fallback is "drop walk-up", not dropping the design.
8. `early_gates.py` halts on a 429 on purpose, as a budget safeguard. Add bounded backoff to the product path and keep the halt in the gate script.
9. demo.md also says "Measured by us, N=800", "96.0%… proving", "garages lose 8% of margins" and "legally sealed". It makes a Prisma ITN claim that W2 contradicts and says "139 tests" when there are 196. gates.md still shows "74/74 PASS" and stores a synthetic clip under `real_world_samples/`.
10. The landing page says LinkedIn **or** X, calls shortlisting "submission review", and states no interview length.
11. The landing page says Evon weights are available "by request"; Hugging Face reports `gated:false`. Both are true, so file the request anyway.

## Dated Go/No-Go Gates

| Date | Gate | Pass | Kill/pivot |
|---|---|---|---|
| 2026-10-06 | Integrity and asks | Discord message posted; GPU dates and Evon access requested; README, demo.md and gates.md corrected | Nothing public goes out until this is done |
| 2026-10-07 | Real anchor set | 10 real lines, ≥70% of amounts exact on the transcribe pass | Below 70%: drop walk-up and rely on abstain-and-re-ask. If the ruling is still pending, keep the audio internal |
| 2026-10-11 | Money path on CPU | Grammar, agreement and abstention work on intake and correction; W2 test passes; false confirmations below the Groq baseline | Review rate above 50% on clean cases: amounts default to the one-tap digital confirm |
| 2026-10-14 | Offline verbatim check | On ≥50 clips, the verbatim pass often holds the right amount when transcribe is wrong | Fails: no reconciler, abstention only |
| 2026-10-18 | Evon ready, GPU dates | `EXTRACTOR_PROVIDER` wired with a JSON schema and thinking-off; Q8_0 smoke-tested; Rule 3 answered; dates fixed | No dates: plan for no GPU (Q4_K_M on Kaggle or ZeroGPU). If Rule 3 says no: self-quantise during the window |
| GPU window, if dates are confirmed (19 Oct–1 Nov) | Measured run | ≤12 attended hours; Evon's line items match or beat Groq on the anchor set plus ~40 synthetic cases; schema followed; zero confident-wrong amounts; demo recorded; quants exported | Evon worse than Groq: ship Evon with more "needs review" fields and disclose it. Window after 1 Nov: footage only |
| 2026-11-01 | Demo without Groq | Three end-to-end runs in a row with Groq disabled | The live demo uses the deterministic fallback |
| 2026-11-04 | Film and post | New storyboard shows the system catching a disagreement; names Prisma, Timbre and Evon; every number reproducible with one command; nominated post is live | Cut any number that can't be reproduced or isn't consented |
| 2026-11-10 | Submit | Gnani models named per Rule 3; exports respect the consent guard; answer to "what does Evon add over `a == b`?" rehearsed | — |
