# Council round 2: peer reviews (each reviewer saw A–E anonymised + one evidence file), 2026-10-05

Each reviewer read only [`framed-question.md`](framed-question.md), [`responses-anon.md`](responses-anon.md) and one evidence file. None saw [`mapping-secret.md`](mapping-secret.md). Each answered the `llm-council` skill's three questions plus a factual-flag line, following the 2026-10-04 council's convention.

| Reviewer | Evidence file | Strongest | Biggest blind spot |
|---|---|---|---|
| 1 | `docs/research/R7-a100-gpu-sprint.md` | B | A |
| 2 | `docs/research/R8-multilingual-models-arxiv.md` | E | A |
| 3 | `docs/gates.md` | B | A |
| 4 | `docs/demo.md` | E | A |
| 5 | `docs/abouthack.txt` | E | A |

## Review 1 (fact-checked against R7-a100-gpu-sprint.md)

**1. Strongest: B.** It turns the hours critique into a schedule with a cost on each step. Grammar plus abstention is the core and needs no GPU. Evon becomes an upgrade, W6/W4 get closed today, llama.cpp setup happens before the GPU arrives, and there is a plan if the GPU never comes. E's "abstain on money" is a sharper thesis, but it is harder to act on.

**2. Biggest blind spot: A.** It never mentions W3 (zero real recordings, the Oct 7 gate) or the hour budget. Yet it adds four builds: a public benchmark, a hosting recipe, Benglish and 10× data. Publishing a benchmark of Prisma failures also runs into the consent guard (W8).

**3. All five missed:**
- The counter-metric. Abstaining on every disagreement drives false confirmations to zero for free. R7 pairs that metric with review rate (kill if >50% on clean cases) and recovery after re-ask. Nobody counts the cost of all those re-asks.
- Whether a community Q8_0 GGUF counts as "Evon v3.3" under Rule 3. Its card says quantisation loss is "not measured against BF16". Ask on Discord before resting the W1 fix on it.

**Factual flags:**
- A "first to make Evon easy to run": a community GGUF, a luminenio ZeroGPU Space and vLLM self-hosters already exist.
- A "10× data": at ~6.75 credits per audio case, 1,600 cases ≈ 10,800 credits, against 4,980 left. Q8_0 also leaves only ~5–6 GiB of headroom for batching.
- A "Benglish at little cost": R7 says 8–14 h, Med–High risk.
- A's claim that Gnani sells into banking and collections: R7 doesn't support it.
- C "app caught it and asked again": no re-ask happened. Groq picked the verbatim evidence.
- D "31 GiB quant on Kaggle": Kaggle fits only Q4_K_M/IQ4_XS.
- E "Groq out today": no rules extractor exists for line items.

## Review 2 (fact-checked against R8-multilingual-models-arxiv.md)

**1. Strongest: E.** Its core rule is R8's strongest finding. LLMs invent plausible values and no paper recovers when both passes are wrong. So money comes from a grammar, pass agreement and abstention, with customer confirmation as the final check (§1.3, §1.6). It uses R8's confident-wrong rate as the gate. It also sees that bad real-speech results *strengthen* abstain-and-re-ask, which D gets backwards. B, the most executable plan, is a close second.

**2. Biggest blind spot: A.** It ignores the hours arithmetic that B–E flag, and it ignores W3. It wants 10× synthetic data, though R8 says TTS sets flatter results and should never stand alone. It treats one synthesised clip as an everyday Prisma failure. And it would publish a Prisma-failure benchmark despite the EULA guard and W8.

**3. All missed R8 Q1:** score offline whether the verbatim pass holds the right amount when the transcribe pass is wrong (o_cp > o_nb, ≥ 50 clips). If it rarely does, Evon's reconciler has nothing to choose and only abstention helps. That settles (a) before any GPU hour. All five also missed Q3: check that quantised Evon reliably follows a choose-or-UNRESOLVED schema (it was flagged as weak).

**Factual flags:** C's "the app caught it and asked again" is false: no re-ask exists (§9 "None is implemented"). D's "both passes wrong → design falls apart" is contradicted by §1.3, where read-back is the right design for exactly that case. D's "selection ≈ `a == b`" ignores P2's 18–34% entity gains. A's "10× data" and "cheap Benglish" go against §8 (gains peak at 2–3× real volume) and P6 (human-checked templates, round-trip check). R8 §1.3 itself mislabels W2 as "both wrong".

> Chair's note: the R8 §1.3 mislabel was corrected after this review. W2 is a one-pass-right case: the verbatim pass held ₹450.

## Review 3 (fact-checked against gates.md)

**1. Strongest: B.** It is the only response whose steps have hour costs and fit the ~75 hours left. It builds the numeral grammar and the agree-or-abstain rule first, so they work without a GPU. It also gets the GPU dates fixed, smoke-tests the Q8_0 GGUF before the window opens, and caps attended GPU time at about 12 h. It should adopt D's question ("what does Evon add over `a == b`?") and E's "abstain on money" framing.

**2. Biggest blind spot: A.** It never does the hours arithmetic. It adds a public benchmark, a ZeroGPU recipe, a Benglish leg and round-the-clock batching on top of a plan that already uses ~60 h. It ignores W3: there is still no real audio. "Ten times the data" can't be run through Timbre and Prisma with ~4,980 credits, and gates.md caps the Lab at 2,000. Publishing Parcha-Bench and pitching W2 publicly as a Prisma failure would also clash with the fail-closed consent policy.

**3. What all five missed:** B, C, D and E all make real human recordings the top gate. But the contest rule is "synthetic data only," and gates.md lists organiser question 1 ("does scripted real-person roleplay count as synthetic?") as still pending. That Discord answer comes before W3 and before any filming. None of the five budgets the gates already scheduled for Oct 6–19 either.

**Factual flags:**
- C, "the app caught it and asked again": the 2026-10-05 end-to-end row in gates.md logs ₹450 + ₹200 exact, GO, with no re-ask.
- D, "under 70% means both passes are wrong": the Oct 7 gate measures only the `transcribe` pass. Its fallback is "drop walk-up," not dropping the design.
- B, "add 429 retry": `early_gates.py` halts on a 429 on purpose, as a budget safeguard.
- A: a public benchmark breaks the consent guard. Nothing in the evidence supports "Gnani sells into banking and collections."
- gates.md itself still shows "74/74 PASS" and stores a synthetic clip under `real_world_samples/`.

## Review 4 (fact-checked against demo.md)

**1. Strongest: E.** It swaps "Evon cross-examines Prisma" for a promise a Gnani engineer can't puncture: no LLM, Groq or Evon, decides money. Amounts come from a numeral grammar plus agreement between the two passes, and the system abstains when they disagree. E plans to win without the GPU. It makes W3 the gate and measures it with the right metric (wrong amounts confirmed with confidence). Its "every claim reproducible with one command" is the only integrity standard that would catch all of demo.md's problems, not just W6. D comes close: "what does Evon add over `a == b`?" is the sharpest line in the council. But D tells Harshdip less about what to do.

**2. Biggest blind spot: A.** It adds scope (Parcha-Bench, an Evon hosting recipe, 10× synthetic data, a Benglish leg) without doing the hours arithmetic. It ignores that no human has ever spoken into the product, and that R8 says synthetic data flatters results. It wants to pitch "a failure mode in your product" on the strength of one synthesised clip. And its "here's the measured rebuild" line rests on measurements that don't exist yet.

**3. All five missed:** In demo.md's correction beat (₹450→₹350, "saade teen sau"), the extractor parses the new amount, and the extractor is Groq. So the grammar and abstention must also cover the customer-correction and re-ask path. The storyboard also needs rewriting so the system catches a disagreement itself, and nobody budgeted hours to re-film it. And demo.md never names Evon, which Rule 3 requires if Evon is used.

**Factual flags:** C says "the app caught it and asked again." demo.md doesn't support this: it has no re-ask started by the system, and S04 claims Prisma parsed ₹450 correctly. B says the integrity problem is closed in 30 minutes. That understates it, because demo.md also contains "Measured by us, N=800" (§6), "96.0%… proving" (§4), "garages lose 8% of margins", "legally sealed", a Prisma ITN claim that W2 contradicts, and "139 tests" where the product has 196.

## Review 5 (fact-checked against abouthack.txt)

**1. Strongest: E.** It turns R8 into one rule anyone can check: no LLM decides money, whether it is Groq or Evon. Amounts need the numeral grammar plus agreement between the two passes, or the system abstains. That takes Groq out today without a GPU. It answers (a)–(f) and still works if the GPU never comes. B's order of steps should be added on top: fix the GPU dates, smoke-test the GGUF first, cap attended time at about 12 h. D's question, "what does Evon add over `a == b`?", is the best interview prep.

**2. Biggest blind spot: A.** It adds scope (Parcha-Bench, an Evon recipe, 10× synthetic data, a Benglish leg) and ignores the hours arithmetic that B–E all point out. It also ignores W3 (no real recordings yet) and R8's warning that synthetic speech flatters results. And it assumes the GPU will arrive.

**3. All five missed:**
- The **Real Deal Award** ("most useful real-world problem solved… kirana stores") fits a mechanic's estimate tool. The framed question left it out.
- Noise Canceller asks for **"real telephonic audio."** Recordings beside a scooter, played over a *simulated* phone line, don't meet that. Record a few real mobile phone calls.
- The page says Evon weights are **"available by request,"** which contradicts R7's "ungated." Request access now.
- **Warp**, a fourth Gnani model on the page, was never looked at.

**Factual flags:**
- A says Benglish "opens Main Character," but the page lists Benglish under Mixed Vibes.
- C says the shortlist is "decided by LinkedIn and X engagement," but the page calls shortlisting "submission review."
- C/D say "LinkedIn and X" / "two posts," but the page says "LinkedIn **or** X."
- D cites "Rule 7," but the page shows only six rules.
- E's "30-minute" interview length isn't on the page.

> Chair's note on Review 5: "Rule 7 (Misleading Demos)" and "synthetic data only" come from the full programme terms as cited in `README.md` and the 2026-10-04 council, not from the six summary points on the landing page. Evon weights: the landing page says "by request", and the Hugging Face API reported `gated:false` on 2026-10-05 (R7 §1.3). Both are true; R7 already recommends filing the request anyway.
