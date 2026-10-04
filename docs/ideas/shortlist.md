# Idea shortlist: Gnani Great Indian AI Internship Challenge

Synthesised 2026-10-04 from `docs/research/R1`–`R6` (≈60 seeds) against the constraints in `docs/wayfinder/MAP.md`.
Ranked pre-council. The council (`council-verdict.md`) and the user make the final call.

## How the field was cut

**Hard filters applied to every seed**
1. A Gnani model must be **load-bearing**, and ideally the one with a real moat: Prisma on **noisy 8 kHz telephony audio with numbers/entities in it** (R4, R6: Prisma leads on noisy 8 kHz in 8/9 languages, trails on clean code-switch sets).
2. Not in a **dead or crowded** space (R3 §2): Hinglish support/sales bots, generic voice form-filling, audio-notes summarisers, farmer IVR, kirana khata, dubbing/live translation, scheme chatbots.
3. **Solo, 5 weeks, no GPU**: Evon optional or demo-only; no real PSTN; synthetic data only.
4. **Shareable in 60 s** (R5 rubric §7.3): a real person reacting, a hearable language moment, a visible before/after, one headline number.
5. **Defensible in an interview** (R4 §5): produces metrics Gnani's own benchmarking guide asks for (WER/CER by SNR band at 8 kHz, entity accuracy, switch-point error, p95 latency).

**Seeds eliminated by facts, not taste**
- *Bachat Baithak / Kendra Scribe* (SHG meeting → ledger): Prisma diarization is **batch-only and capped at 2 speakers**; an SHG meeting has 10–15. Infeasible as designed.
- *Suraksha Kavach* (elder scam-call shield): collides with Google's on-device Scam Detection and Truecaller's AI Call Scanner; depends on Evon/LLM classification; fear-framing risk. Kept as an optional module of #1, not a standalone.
- *Apni Awaaz Tracks / SwitchCap* (creator dubbing/captions): dubbing is a dead row (Sarvam Dub, ElevenLabs); captions are cosmetic and don't touch Gnani's telephony moat.
- *Vaada* (collections PTP ledger): excluded by the standing "no plain BFSI collections" decision; it is Gnani's own Collect365.
- *Mandi Bhav / Kisan Overflow / KCC*: farmer-IVR archetype, dead row.

## Scoring rubric (each 0–5)

| Criterion | What 5 means |
|---|---|
| **Share** | R5 rubric ≥17/21: real user reacting, hearable regional/code-mix, split-screen before/after, pasteable number |
| **Moat** | Demo collapses without Prisma on noisy 8 kHz; ITN/entities or Timbre normalisation do visible work |
| **Award** | Clean fit to one of Noise Canceller / Real Deal plus a second category |
| **Pain** | Primary-source evidence with numbers, 2024–26 |
| **Feasible** | Solo, 5 weeks, credits only; Evon optional; main risk has a known mitigation |
| **Open** | No entrant, no incumbent, not a known govt PS already built |
| **Interview** | Produces ≥3 defensible metrics from Gnani's own benchmark guide |
| **Filmable** | A real user can plausibly appear on camera in Delhi within 2 weeks |

## The shortlist

| # | Idea | Share | Moat | Award | Pain | Feasible | Open | Interview | Filmable | **Total /40** |
|---|------|------:|-----:|------:|-----:|---------:|-----:|----------:|---------:|------------:|
| 1 | **Sun-Saathi**: live regional-script captions of a phone call for hard-of-hearing/elderly users, with tap-to-reply spoken by Timbre | 5 | 4 | 5 | 3 | 3 | 5 | 4 | 4 | **33** |
| 2 | **Kaam ka Parcha** (Garage Job-Card): mechanic dictates the repair in Hinglish over workshop noise → itemised job card + bill, Timbre reads the total back for customer confirmation | 4 | 4 | 5 | 3 | 5 | 5 | 4 | 5 | **35** |
| 3 | **Claim-by-Call**: ASHA worker phones in her visits over a noisy 8 kHz line → NHM register + incentive claim with ₹ total, Timbre read-back | 4 | 5 | 5 | 5 | 4 | 3 | 4 | 2 | **32** |
| 4 | **Sahi Bikri**: regional-language pre-issuance verification call for insurance + "said vs sold" diff against the telesales recording | 3 | 4 | 3 | 5 | 3 | 5 | 5 | 3 | **31** |
| 5 | **Dhokha Desk**: multilingual fraud-complaint intake for bank fraud desks (UTRs, amounts, timestamps read back digit-by-digit) | 3 | 5 | 4 | 4 | 4 | 4 | 4 | 2 | **30** |
| 6 | **Line Noise Lab**: reproducible telephony-stress harness (codec × SNR × packet loss → WER/CER/entity/switch-point curves) built from Timbre-synthesised "SynthCall-IN" | 1 | 5 | 3 | 4 | 5 | 4 | 5 | 1 | **28** |

**Pre-council recommendation:** build **#2 Kaam ka Parcha** or **#1 Sun-Saathi** as the product, with **#6 Line Noise Lab** as its measurement spine (not a separate entry; one award per entrant). #2 edges #1 on total because it is lower-risk and filmable today; #1 has the higher ceiling on engagement. The council should decide which ceiling is worth which risk.

---

## 1. Sun-Saathi (working title) — "Live Relay for Indian phone lines"

**Real situation.** India has ~63 million people with significant hearing loss (WHO/NPPCD figures; verify) and a fast-growing elderly population for whom phone calls are the default channel for banks, hospitals, deliveries and family. Google demoed "Live Relay" (live call captions + typed replies spoken aloud) at I/O 2019 and never shipped it; Live Transcribe works from the mic only, not for phone calls, and speaks nothing back. India has no telephone relay service. Accessibility is an unserved segment in Indic voice AI (R3 §2 "Open"), and the RPwD Act 2016 obliges service providers to be accessible, which gives banks and telcos (Gnani's customers) a reason to care.

**What it does.** The user's phone is on speaker (or a VoIP leg in the stretch version). A companion app on a tablet/second phone streams the caller's audio to Prisma realtime at 8 kHz telephony preset, shows large captions in the user's script (Hindi, Bengali, Tamil, Kannada…), and offers tap-to-reply chips or a keyboard; the reply is spoken into the call by Timbre in the caller's language. Mishear → "phir se boliye" chip makes Timbre ask the caller to repeat (the failure-handled beat). A post-call card lists what was agreed (amounts, dates via ITN). Optional module: scam-grammar warning in the user's language.

**Load-bearing Gnani.** Prisma realtime WS (8 kHz, telephony VAD preset, ITN) is the whole product; Timbre is the user's voice; Evon optional for the post-call card and reply suggestions.

**Awards.** Real Deal (primary), Noise Canceller (telephony audio by construction), Crowd Favourite / Demo Day (emotional reel). R5 rubric estimate 19–20/21.

**60-second scene.** 0–3 s: a grandparent reads large Bengali captions as a grandchild says "Dida, ami Shonibar ashchi" from a noisy market line. 3–8 s: "6 crore Indians can't hear the phone; nobody built relay for Indian languages." 8–12 s: split screen, generic ASR garbles the same clip. 12–40 s: the call continues; a delivery agent calls in Hindi, she taps "Darwaza khula hai, upar aaiye", Timbre speaks it; a mishear is repaired. 40–46 s: she laughs at the caller's reaction. 46–53 s: proof card (caption latency p95, WER at 5 dB on the synthetic call set, "Prisma v2.5 + Timbre v2.5"). 53–60 s: who it's for; end card.

**Headline numbers.** Caption latency p95 (speech end → caption), WER/CER by SNR band on SynthCall-IN at 8 kHz, reply round-trip latency, entity accuracy for amounts/dates in the post-call card.

**Biggest risks.** (a) Prisma realtime emits **final transcripts only** (no partials) so captions arrive per utterance, ~0.5–1.5 s after the speaker pauses; acceptable for relay but must be measured in week 1. (b) Speakerphone capture is far-field; honest framing: "second-device relay", like a hearing-aid companion. (c) One language per WS session; language switch requires reconnect (or two sessions). (d) Filmability depends on access to an elderly relative (G1 open).

## 2. Kaam ka Parcha (Garage Job-Card)

**Real situation.** Two-wheeler and car workshops (Gnani's auto vertical: Tata Motors, Horsepower are customers) run on verbal estimates; disputes over "what was agreed" are universal; mechanics will not type. Workshop noise (compressors, engines) is the Noise Canceller brief in a non-phone setting, and every utterance has part names + ₹ amounts + a date, Prisma ITN's exact job. SIH 2026 has an analogous "voice time agent for site supervisors". No entrant and no startup in this slot (R3 §2 "Open").

**What it does.** Mechanic taps record, speaks the job in Hinglish over the noise ("front brake pad badla, part saade chaar sau, labour do sau, Somvaar tak"); Prisma (REST ≤60 s or WS) transcribes; an extractor (Evon or external LLM, schema-validated) fills a job card: items, part/labour ₹, promised date; Timbre reads the total back in the customer's language; the customer says "haan" or corrects one line; a PDF/WhatsApp message goes out. Per-field confidence shown; low-confidence fields re-asked.

**Load-bearing Gnani.** Prisma on noisy code-mixed speech with ITN; Timbre normalisation (₹650 → "chhe sau pachaas rupaye", dates). Evon optional.

**Awards.** Noise Canceller + Real Deal; Solo Ninja; Demo Day. R5 rubric estimate 16–17/21 (mechanic reacting lifts it).

**60-second scene.** Phone propped on a workbench in a real Delhi garage, engine running; mechanic speaks; raw transcript → job card fills; split-screen generic ASR fails on "saade chaar sau"; Timbre reads "kul chhe sau pachaas, Somvaar shaam tak"; customer nods; proof card.

**Headline numbers.** Entity (₹/part/date) exact-match at measured workshop SNR vs clean; WER by SNR band; read-back correction rate; end-to-end seconds per job card vs handwriting.

**Biggest risks.** (a) "Voice form-filling" adjacency (Bolo): mitigate with the noisy vertical, the confirm-by-readback loop, and the bill as the artefact. (b) It is not telephony audio unless we also route it through the 8 kHz chain for the "mechanic calls the customer" variant; do both and measure both. (c) Mechanic slang and brand names: `bias_list`.

## 3. Claim-by-Call (ASHA incentive claim by phone)

**Real situation.** ASHAs double-enter diaries into 7+ apps until midnight; incentives are paid only on data entry; 42,000 Karnataka ASHAs struck in Jan 2025 over a glitching portal; UP's 150k ASHAs still file paper vouchers on a 15-day cycle (R2 §2). ASHABot's voice path died on 38% transcription errors; FormBharo lost ~41 points of completion to real ASR transcripts and recovered it with deterministic validation.

**What it does.** The ASHA calls a number (demo: simulated 8 kHz AMR-NB line) and speaks her visits; Prisma + ITN capture counts, dates, phone numbers; a validator + extractor maps to NHM activity codes; Timbre reads back "teen ANC, ek institutional delivery, kul ₹1,350. Sahi hai?"; CSV/PDF for the block manager.

**Load-bearing Gnani.** Prisma realtime 8 kHz + ITN; Timbre read-back; Evon for code mapping (optional).

**Awards.** Real Deal (strongest evidence in the whole research set), Noise Canceller, Main Character (Marathi/Kannada).

**Biggest risks.** Bolo/form-filling adjacency; no real NHM integration; health optics; **filmability**: finding an ASHA to appear on camera within two weeks from Delhi is unlikely, and without her the reel loses its human (R5 says that is most of the reach).

## 4. Sahi Bikri (insurance PIVC + said-vs-sold)

**Real situation.** 26,667 mis-selling complaints in FY25 (+14%), IRDAI panels Dec 2025 and clawback proposals, PIVC done by humans on a sample in Hindi/English while victims are elderly regional-language buyers (R1 §4).

**What it does.** Timbre calls (demo: browser leg resampled to 8 kHz) the buyer in Tamil/Bengali and reads the real policy facts; Prisma + ITN capture yes/no and amounts; Prisma batch diarization on the 2-speaker telesales recording; Evon diffs what the agent said vs the policy schedule vs the buyer's answers and flags mismatches with timestamps.

**Why it ranks 4th.** Best "enterprise" story and best interview story (uses every API incl. batch diarization at exactly 2 speakers), news hook, zero collisions; but the 60 s needs two scenes to explain, it is B2B insurance (LinkedIn-friendly, X-hostile), and the human reacting is an actor. Strongest alternative if the council prefers enterprise credibility over virality.

## 5. Dhokha Desk (fraud-complaint intake)

**Real situation.** 1930 unreachable in the golden hour (victims report 20 failed dials); intake needs UTRs, amounts, timestamps, bank names from a panicking caller in their language (R1 P7). Must not impersonate 1930/I4C; position for bank fraud desks.

**Why it ranks 5th.** Long digit strings on 8 kHz are the hardest ASR case and the most impressive if nailed (gate: ≥90% exact 12-digit UTR capture on 30 clips); but the demo is a form filling itself from a stressed caller, which is close to the crowded row, and the human in frame is an actor.

## 6. Line Noise Lab (measurement spine)

Reproducible harness: Timbre synthesises entity-dense two-voice dialogues ("SynthCall-IN", exact ground truth), ffmpeg/phonesim degrades them (G.711, AMR-NB 4.75–12.2, packet loss, MUSAN/Vaani-Noise at 0–20 dB), Prisma transcribes (REST/WS/batch, presets, `with_denoise`, `bias_list` on/off), jiwer-based report of WER/CER by SNR band, entity accuracy, switch-point MER, hallucinated words on non-speech. Publishes **only our own system's deltas** (EULA). Jugaad Genius candidate alone; as the spine of #1 or #2 it produces every proof-card number and the interview story. Recommendation: build it in week 1 regardless of the product chosen.

## Questions for the council

1. Ceiling vs floor: #1 (higher engagement ceiling, latency/capture risk) or #2 (lower risk, filmable now, slightly weaker emotional hook)?
2. Is "second-device relay via speakerphone" an honest enough telephony story for the Noise Canceller award, or does it read as a hack?
3. Does #2 escape the "voice form-filling is crowded" verdict convincingly?
4. Should #6 be a visible part of the submission (repo + curves) or stay internal evidence for the interview?
5. Anything here a Gnani hiring manager would see as a toy, or as treading on a Gnani product?
