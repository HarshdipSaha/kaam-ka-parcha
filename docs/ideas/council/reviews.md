# Council round 2: peer reviews (each reviewer saw A–G anonymised + one evidence file)

## Review 1 (fact-checked against 02-speech-apis.md)

**1. Strongest: G**, with F's one modification grafted on. G is the only response that reasons as the interviewer who decides the offer: correct API facts (finals-only, far-field ≠ codec path), the exact EULA line (absolute WER-vs-SNR curves *are* a benchmark; publish deltas only), and six interview questions #2+#6 can answer from own data. F's "Timbre phones the customer, Prisma captures the haan/nahi correction over the 8 kHz leg" makes the telephony story true by construction and gives #2 the reacting human it lacks. A supplies the best execution schedule (Monday kill-tests, credit sizing).

**2. Biggest blind spot: D.** It prices #1's ceiling (400–1,000 reactions) off creator-account viral clips while C notes a ~700-follower student's baseline is 5–15; it proposes "Prisma v2.5 vs Whisper/Google with WER on screen, model names burned in", which is precisely the benchmark the EULA forbids; and it has zero engineering content for the interview that actually awards the ₹6 lakh. B shares the weakness ("three elderly testers is deployment data" collides with the synthetic-data-only rule).

**3. All seven missed:** Sun-Saathi's core scene is cross-lingual (Hindi caller → Bengali captions; E's Tamil-parent/Hindi-landlord). Prisma transcribes, it does not translate; translation is a dead row and no Gnani API does it. Without MT the product is same-language captions, i.e. Live Transcribe plus a Timbre reply. Also unexamined: WS has no flush/end-of-stream (notes line 129), so the last "haan" of any confirm loop can be lost.

**Factual flags:** A pairs `bias_list` with `format=transcribe`; notes line 68 require `verbatim`, and REST silently ignores invalid boosting (line 73), so his test would read "no gain". D rescored #2 at 14–15/21; shortlist says 16–17. B's "AMR-NB 5.9 kbps" vs G's "4.75" from the same paper: one is wrong, unverifiable here. C, F, G line citations check out.

## Review 2 (fact-checked against R5-virality.md)

**1. Strongest: F.** It is the only response that re-frames the decision correctly (two artefacts for two judges: a clip for the shortlist, numbers for the offer) and then designs for both at once: the mechanic's estimate becomes a Timbre call to the customer, so the 8 kHz leg is real by construction, the reacting human is "whoever picks up" (portable hero from #1), and the artefact is a confirmed agreement, not a Bolo-shaped form. It answers every sub-question and resists inventing a (g). G is the best complement (interview questions, EULA handling, non-speech hallucination budget).

**2. Biggest blind spot: B.** It treats #1's floor as "a working caption app" when the shortlist (risk d, G1 open) and R5 §7.1 say the reel is nothing without the elder; D at least adds an Oct 12 hard gate, B has none. It also transfers Instagram humour-reel numbers (creator accounts) to a 700-follower LinkedIn engineering post, and adds a second contest (Code for a Billion, not in shortlist/R5, unverified) to a 75-hour budget.

**3. What all seven missed: hours.** 15 h/wk × 5 wk = 75 h. R5 §6 alone (10–15 comments/day, 2–3 build-in-public posts/week from now, 90-min launch windows, 3 angle posts/week after) costs 20–30 h. Nobody subtracted that from build time; D's weekly grandparent series and B's dual-submit are unaffordable. Also, "first public post Oct 25" conflicts with R5 §6.1 pre-launch warming, which needs postable material from week 2.

**Factual flags:** D: "#2 = 14–15/21" matches R5 line 286 but shortlist §2 says 16–17; and Sophie has no engagement numbers in R5. G: "#1 answers none" overstates; shortlist §1 lists the same WER/latency/entity metrics via #6. E: Live Transcribe is mic-only, not calls (shortlist §1), so the judge objection is weaker than claimed.

## Review 3 (fact-checked against R4-technical-angles.md)

**1. Strongest: F**, with G as its executable twin. F alone dissolves the #1-vs-#2 split instead of picking a side: make the garage estimate a Timbre phone call to the customer at 8 kHz, so the telephony leg is real by construction, the reacting human (a parent/grandparent) is imported from #1, and the artefact is a confirmed agreement rather than a Bolo-shaped form. Its floor analysis (#1 floor = zero because WS is finals-only and the elder is unconfirmed) matches shortlist §1 risks (a)/(d). G supplies what F lacks: the interview question list, the correct EULA reading (absolute WER-vs-SNR curves are a benchmark; publish deltas), and non-speech hallucination (R4 S12), which nobody else budgets for. A gives the week-1 kill plan both need.

**2. Biggest blind spot: B.** It prices #1's ceiling off creator-account humour clips (C rightly notes a ~700-follower student is not that genre), never mentions finals-only caption latency, adds a second contest (Code for a Billion) to a 15 h/week solo budget, and claims speakerphone is a "harsher" Noise Canceller case. R4 §3.1 says the channel is codec round-trip + packet loss; far-field room audio is a different degradation, not a harder version of the same one.

**3. All seven missed:** (a) Every seat treats Timbre-synthesised SynthCall-IN as the harness's data. R4 §3.6 warns TTS speech is cleaner than humans and says "always pair with Gramvaani"; nobody names the one real Indic telephone corpus, so the interview question "what real phone speech did you test on?" has no answer. (b) Nobody checked D's "30-person first-hour list" playbook against the no-engagement-exchanges rule.

**Factual flags:** D's criterion-7 "Prisma vs Whisper/Google split-screen with WER on screen, model names burned in" directly violates R4 §1.6 ("never a Gnani vs X table"). C is right that shortlist's Award=5 for #2 contradicts the framed Real Deal/Noise Canceller text. A's credit math is labelled speculation; R4 §7 confirms cost is undocumented.

## Review 5 (fact-checked against 06-company-and-landscape.md)

**1. Strongest: F.** It reframes the decision correctly (one clip for the shortlist, one number set for the interview) and resolves (c) and (d) with a single structural move: the mechanic's estimate becomes a Timbre call to the customer at 8 kHz, so telephony is real by construction, the reacting human is imported, and the artefact is a confirmed agreement rather than a form. This matches notes §2.2 ("agentic voice that closes the loop"). G is the essential complement: its interview-question list and "2G job card" framing are what make F's build defensible.

**2. Biggest blind spot: B.** It never engages the two facts that cap Sun-Saathi: WS emits finals only (captions lag each pause) and the far-field speakerphone path has no codec/loss stage, so "harsher Noise Canceller case" is wrong on the award's own terms. It rests on an unconfirmed grandmother (G1 open) and asserts #1 "treads on nothing" while notes §1.1 list Assist365 as real-time transcription. "Code for a Billion" is unverifiable from the permitted files.

**3. All seven missed:** the arithmetic. Up to 100 internships, ~483 Discord members, five explicit entries at 5–26 reactions. The shortlist is a low bar; the ₹6 lakh is decided at the interview and (secondarily) one award. B/D/E spend the whole budget on virality nobody needs. Also unaddressed: if extraction runs on an external LLM, Prisma is a swappable STT and "genuine Gnani use" rests on ITN + Timbre alone.

**Factual flags:** D: #2 rubric "14–15/21"; shortlist says 16–17. D: split-screen Prisma vs Whisper with WER and model names burned in contradicts the EULA guard. E(g): Tamil captions of a Hindi caller needs MT Gnani's API lacks; "live translation" is a dead row. A: "ITN hi/en-only" overstates "documented mainly for hi/en".

## Review 6 (fact-checked against 01-hackathon-overview.md; asked to test F's merge)

**1. Strongest: G**, with A's week-1 plan as its execution layer. G is the only seat arguing from the judge who decides the offer: it cites the finals-only WS, distinguishes far-field room audio from codec-path audio (Prisma's actual moat), names the auto vertical Gnani sells into, gets the EULA right, and lists interview questions #2+#6 can answer and #1 cannot. A, C and F independently converge on the same pivot (phone leg primary), which corroborates it. A alone prices credit burn.

**2. Biggest blind spot: B.** It asserts #1's floor is "a working caption app", contradicting the shortlist's own risk (d) and the open G1 gate; it assumes a Ganesh reshare; it imports an unverified external contest and calls three testers "deployment data". E shares the flaw: "strangers think speakerphone is honest" ignores that Noise Canceller is voted by telephony engineers.

**3. All seven missed:**
- **Rule 9 scope**: "practical need for enterprises, developers or creators". Sun-Saathi is a consumer app; nobody framed it for telcos/banks.
- **Rule 7 "misleading demos"**: a simulated call presented as a phone call needs an on-screen disclosure. This bites F's merge hardest.
- **Mixed Vibes** fits Hinglish #2 better than Real Deal (C correctly notes a mechanic is not farmer/kirana/health; shortlist's Award=5 is inflated). D's "#2 14–15/21" also contradicts the shortlist's 16–17.

**F's merge**: feasible only as Timbre → ffmpeg G.711/AMR → speaker/WhatsApp note → customer → recorded reply → chain → Prisma REST. "Real by construction" overstates it: still simulated codec, same as #2's hedge. It resolves C/G (telephonic path primary, confirmed-₹ artefact) but not E (still speak-then-bill), and inherits G's haan/nahi short-utterance drop and one-language-per-session risks.

## Review 7 (fact-checked against R2-grassroots.md; asked for a resolution)

**1. Strongest: F.** It is the only response that reframes the decision correctly (two artefacts for two judges) and then derives the product from that. Its merged design simultaneously answers (c), (d) and (f), and it is the only seat that notes "the hero is portable". G is the best interview-side companion (concrete sweep questions, non-speech hallucination, 2G framing); A is the best week-1 plan (credit-burn sizing is a real catch nobody else makes).

**2. Biggest blind spot: B.** It prices the ceiling off creator-account virality while ignoring C/F/G's floor-killers for #1: finals-only WS, speakerphone is far-field not a codec path, the elder is an unconfirmed cast. "Speakerphone is a harsher Noise Canceller case" is wrong in kind. D shares the blind spot but at least sets an Oct 12 hard gate. E's "#6 interview-only" undersells the only resharable thing engineers have.

**3. What all seven missed:**
- **Claim-by-Call/ASHA dismissed on filmability only.** R2 calls it the strongest-documented, money-linked voice pain in India. Nobody tested whether the hero problem is solvable the same way they solved #1's (a relative plays the ASHA with scripted synthetic visits, which the rules already require). It is the only seed that natively hits Real Deal + Noise Canceller + Main Character and treads on nothing Gnani sells.
- **Nobody measured the confirm loop's weakest link:** short-utterance "haan/nahi" drop rate at 8 kHz (G asks it, no one budgets week 1 for it). Every merged design depends on it.
- **Casting is a week-1 task with a deadline in every design**, not just #1. F/G's phone-leg demo also needs a reacting person answering the call.

**Resolution: F states it; G/A half-state it.** The hero answers the phone. The garage (or ASHA) worker speaks on the noisy leg; the system then *calls the elder* (parent/grandparent as the customer) over the simulated G.711/AMR-NB chain; Timbre reads "kul chhe sau pachaas, Somvaar tak, theek hai?"; she corrects or laughs "haan"; Prisma catches it at 8 kHz; the parcha seals. Telephony honest by construction (F, G), reacting elder in frame and ends the clip (D), artefact a confirmed agreement not a form (F, G), and #6 measures that exact leg. Apply D's Oct 12 casting gate to the *customer* role. If the elder is a Bengali/Tamil speaker, Main Character comes free (E). Publish #6 as deltas-only carousel (C, G).

## Review 4 (fact-checked against R3-hackathons-and-field.md)

**1. Strongest: G.** It answers every sub-question from the hiring manager's seat, and its claims check out: auto vertical confirmed (R3 line 43), Bolo's "clean English records" positioning (R3 line 55), EULA bites on absolute WER-vs-SNR curves. Its interview-question list is the only concrete test of whether the harness earns the offer. Lift A's credit-burn probe (one call, read the dashboard) into G's week 1; nobody else sized the 5,000 credits.

**2. Biggest blind spot: B.** It prices #1 off creator-account humour reels while ignoring that a ~700-follower student's floor is zero if G1 (elder on camera) fails and finals-only latency shows on screen. It recommends "comparative-number threads" despite the EULA, and its Code for a Billion dual-submit (R3 line 86 confirms the contest exists) collides with GIAIC's synthetic-only rule and CfB's "real deployment data" criterion simultaneously.

**3. All seven missed:**
- Whether filming a real mechanic/grandmother's speech satisfies "synthetic data only". A asserts "scripted = synthetic" without evidence; six ignore it. Verify with Gnani on Discord before week 2.
- D's "30-person first-hour list" seeding playbook sits close to "no engagement exchanges"; nobody flagged the disqualification risk.
- Up to 100 internships against a field of ~5 entrants means the interview, not the shortlist, is likely the binding constraint; only G implicitly weights this.

**Factual flags:**
- D scores #2 at 14–15/21; shortlist says 16–17.
- D's split-screen "Prisma vs Whisper/Google with WER burned in" is a published Gnani benchmark, EULA-violating (shortlist scenes carry the same defect; C's absolute-WER flag is correct).
- F: "telephony leg real by construction" is false; no PSTN exists, so the Timbre call is a simulated leg needing the same disclaimer F demands of #1.
- C's Award critique is sound against the framed question, but contradicts R3 S1 and shortlist Award=5; the shortlist should re-score.
- A: "elderly relative you don't have"; shortlist says G1 open, not absent.
