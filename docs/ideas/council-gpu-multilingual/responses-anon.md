# Council round 1: anonymised responses (A–E), 2026-10-05

Each advisor read only [`framed-question.md`](framed-question.md) (no other files, no web) and answered independently in 150–300 words. Letters were randomised; the key is in [`mapping-secret.md`](mapping-secret.md) and was not shown to reviewers.

## Response A

Yes, "Evon cross-examines Prisma" is the right bet. But you're treating it as a feature of a mechanic app, and it's worth more than that.

**1. The real product is a check on spoken rupee amounts for Prisma.** Gnani sells voice agents into banking, collections and insurance. On every one of those calls, rupee amounts travel over a bad 8 kHz line. W2 ("saade chaar sau" coming back as "04:30 100") isn't something to hide. It's a type of Prisma failure their enterprise customers hit every day. Pitch the cross-examiner as a component anyone can plug in: two Prisma passes, plus a deterministic grammar, plus Evon. When they disagree, it asks again instead of guessing. In the interview you stop being a student with a demo. You're the person who found a failure mode in their product and contained it.

**2. Release Parcha-Bench as a gift.** Publish the gold-first corpus on Hugging Face with a data card, as a test set for spoken numbers in Prisma and Evon. Ideally the engineers who interview you will already have run it.

**3. Be the first to make Evon easy to run.** There is no official quantised build. A public "Evon v3.3 on one A100, then on free ZeroGPU" recipe plus a live Space is the kind of thing Gnani's own developer-relations team reshares. That drives engagement on your LinkedIn and X posts and supports Jugaad Genius and Crowd Favourite. Other entrants need Evon too, which makes them your audience.

**4. Use all 72 hours.** Only 6 of Evon's 52 layers are attention layers, so the KV cache is tiny and batches can be huge. The ~30 hours you aren't at the machine should run overnight batch generation. Use several prompt styles and filter everything with the deterministic arbiter (items sum to the total, integer paise, valid date), Aya-style. Aim to leave with ten times the data R7 planned.

**5. Make W1, W4 and W6 the story.** "My first version let a non-Gnani LLM decide the money and showed numbers I never measured. Here's the measured, all-Gnani rebuild." Being that honest sets you apart from other entrants.

**6. The numeral grammar is just a lookup table.** Add one Benglish numeral leg to show it works for other languages, which opens Main Character at little cost.

## Response B

The plan doesn't fit the hours. R7 asks for 20–24 h of pre-GPU work plus 38–42 attended GPU hours. That is about 60 of the ~75 hours left, which leaves ~15 for real recordings, filming, posting and engagement. And 40 attended hours inside 72 is not realistic for someone who works 15 h a week. Cut until the plan fits.

"Evon cross-examines Prisma" is the right core bet. But the part that actually fixes the amounts needs no GPU: the numeral grammar and the rule "accept only when the two passes agree, otherwise abstain" are deterministic code. Build those first. Then Evon is an upgrade, not a dependency.

**Today (it's Monday):**
1. Remove the W6 numbers from the storyboard and relabel the W4 gate "unverified." 30 minutes, and the integrity problem is closed.
2. Add 429 retry with backoff. 1 h.
3. Get the GPU dates fixed. A GPU with no dates is no GPU.

**This week:**
4. Write the numeral grammar for the verbatim pass and add the W2 "saade chaar sau" → 450 case as a test. ~5 h.
5. Clear the Oct 7 gate: 10 real lines recorded beside a scooter, by you and two friends. Without real audio, every number is synthetic.
6. Build an eval runner that counts false confirmations: Groq vs grammar-only. ~4 h.
7. Wire up `EXTRACTOR_PROVIDER`, add the JSON schema and the thinking-off flag, and smoke-test the Q8_0 GGUF in llama.cpp on a rented high-RAM CPU box. Then the first GPU hour runs the batch instead of debugging setup.

**GPU window:** one scripted batch that runs unattended. Evon acts as extractor and as a constrained reconciler over the real clips plus ~40 synthetic ones. Record the live three-model demo on day 2. Cap attended time at about 12 hours.

**If the GPU never comes:** the grammar handles the amounts, slow quantised Evon on CPU or ZeroGPU covers the demo, and Groq leaves the critical path either way.

**Drop:** QLoRA, Tanglish/Benglish, the regional read-back, Parcha-Bench, the enhancement A/B and the bias_list A/B. Cut corpus v2 from 160 cases to 40.

**Multilingual research:** one sentence for the interview ("choosing between hypotheses beats free correction"). Zero build hours.

## Response C

Reading this cold, the most striking thing is that no human being has ever spoken into this product. There are 196 passing tests and 45 papers behind it, but zero real mechanics. Everything you're optimising sits on synthetic speech, and your own research says synthetic speech flatters results and can rank variants in the wrong order. Fix that before anything touches a GPU.

Second, look at the hours. Pre-GPU work is about 22 hours and the attended window is about 40, so roughly 62 of your 75 hours go there. That leaves around 13 hours for filming, posting and engagement. But the shortlist is decided by LinkedIn and X engagement. The plan spends most of the budget on what the interview tests and almost nothing on what gets you into the interview. On top of that, the GPU dates aren't even fixed.

Third, your best story is already written, and it's W2. The mechanic said "saade chaar sau", the machine heard "04:30", and the app caught it and asked again. Anyone can follow that in five seconds. "Evon cross-examines Prisma" means nothing to an outsider. Neither does the vocabulary: ITN, bias_list, verbatim pass, paise, CoefVar, Parcha-Bench, SynthCall, Line Noise Lab. Pick one name and one moment.

On integrity: the README says "optional" when the step is required, and the proof card shows numbers nobody measured. To an outsider those are simply false statements. Correct them now, without ceremony. Then the honest version becomes your pitch: "a non-Gnani model was deciding the money, so I moved that job to Gnani's own model."

Drop the regional read-back, Tanglish, QLoRA and the benchmark branding. Stay deep on Hinglish. Aya, Swallow and the arXiv citations belong in the interview. Nobody scrolling LinkedIn cares.

If the GPU never arrives, nothing important is lost: Evon runs as a quantised build on rented hardware, and real recordings plus one clear video still win.

## Response D

The fatal flaw is the arithmetic. R7's plan takes 20–24 h before the GPU and 38–42 attended hours during it. That is 58–66 of the ~75 hours left. The remaining ~10 h has to cover the Oct 7 real-recording gate, the Lab grid, the W6 cleanup, filming, two posts that need days to gather engagement, and interview prep. The plan is built on hours Harshdip doesn't have. It also assumes a 72-hour window at fixed dates nobody has confirmed, worked by a student who averages about 2 hours a day.

Second flaw: Evon doesn't add much to the "cross-examination." The numeral grammar and the agreement check do the real work, and neither needs a GPU. R8 says frozen mid-size LLMs make transcripts worse, and that only constrained selection is safe. A constrained selection between two values is basically a string compare. A Gnani engineer will ask, "What does Evon add over `a == b`?" There's no good answer to that yet.

Third: swapping Groq for Evon swaps one dependency for a worse one. After the GPU goes back, the critical path runs on a 31 GiB community quant on ZeroGPU or Kaggle, with cold starts, during a live interview demo. Groq at least stays up.

Fourth, and the one being avoided: there is not one real human recording. The Noise Canceller pitch rests on synthetic speech mixed with an engine sound. If real lines come in under 70% exact, both Prisma passes are wrong together. R8 says nobody recovers from that, and the cross-examiner design falls apart. Run the Oct 7 gate first and let its result decide whether the GPU plan is worth doing.

What to do:
- **Now:** Remove the W6 numbers, correct the README's "optional" claim, and label the 74/74 gate unreproducible. These are Rule 7 risks sitting in public material. Disclose them, don't fix them quietly, because git history will show it.
- **Before any GPU work:** Build the grammar plus abstention and re-ask on CPU. That stays the core even if the GPU never comes.
- **If the GPU comes:** Use it for one measured run of Evon as extractor, plus recorded demo footage. Nothing more.
- **Drop:** QLoRA, the Tanglish/Benglish/regional legs, and Parcha-Bench. Keep the literature for the interview, not the posts.

## Response E

You're asking how to spend a GPU. The real question is what Harshdip can defend when a Gnani engineer interrogates them for 30 minutes. The offer gets decided in that interview, and the GPU isn't what decides it. Feeling that "3 days that won't recur" must be used is scarcity bias. Look at the math: R7's plan takes 20–24 h before the GPU and 38–42 h during it. That's about 60 of their 75 hours, which leaves almost nothing for real recordings, filming, posting and engagement. And engagement is the first filter.

Strip it down. The product makes one promise: **a wrong rupee amount never gets confirmed.** W1, W2, W4 and W6 all break that promise. The literature says LLMs make up plausible numbers and that nothing recovers when both passes are wrong. So no LLM should decide money at all, whether it's Groq or Evon. Amounts should come from a deterministic numeral grammar plus agreement between the two passes. When they disagree, the system abstains and asks again, and the customer's confirmation is the final check. None of that needs a GPU, and it takes Groq out of the critical path today. Once that's done, Evon only structures line items and part names. That's a small constrained job, and a GGUF build can cover it after the window.

So for (a), the core bet is "abstain on money", not "Evon cross-examines Prisma". Use the GPU, if it comes, for three things only: run Evon on the real anchor set, record the live demo, and export the quantised build for hosting. The plan has to win without the GPU arriving at all.

The real gate is W3. Ten real speakers beside a scooter, measured by one metric: the rate of wrong amounts confirmed with confidence. If Prisma misses amounts on real speech, the abstain-and-re-ask design is the story.

(e) Delete the W6 numbers today. Correct the README. Make every claim reproducible with one command. Don't build a story around it. Just make sure nothing in it is false.

(d) Stay on Hinglish only. Aya 23 itself showed depth beats breadth.

(f) The public post gets one lesson: "Keep numbers out of every text generator." Everything else stays for the interview.
