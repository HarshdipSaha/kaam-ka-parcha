# Council Verdict: Gnani GIAIC idea (2026-10-04)

## Where the Council Agrees

- **The phone leg must be the primary path, not the hedge.** Executor (A), Contrarian (C), First Principles (F) and Gnani Insider (G) reached this independently: a walk-up garage recording is compressor noise, not "telephonic audio", and has no Noise Canceller claim. High confidence.
- **Speakerphone relay is not telephony evidence.** A, C, F, G: loudspeaker → air → tablet mic is far-field reverberant audio, a different degradation from codec + packet loss, and Prisma's documented edge (Gramvaani, Kathbath-noisy, GSM/VoIP) is not far-field.
- **Sun-Saathi's "live" promise is broken by the API.** A, C, F, G: WS emits finals only; end-of-turn ≈ `x-min-silence-ms` 500 + 300–500 ms. Captions arrive 1–2 s after each pause.
- **#1's floor is zero without a confirmed elder on camera.** Even its advocates, Growth Strategist (D) and Outsider (E), say so; D sets an Oct 12 gate.
- **#6 is a spine, not a product, and only deltas go public.** A, B, C, F, G. E dissents on publishing at all.
- **A reacting human is the shareable unit, and the hero is portable** (B, D, E, F). F is the only seat that unbundles "hero" from "product".
- **#4 and #5 tread on Gnani** (Aura365, Armour365, PIVC pitches): B, C, F, G.

## Where the Council Clashes

**#1 vs #2.** Expansionist (B), D and E pick Sun-Saathi for its ceiling (elder-reacting genre, the new B2C team, a Ganesh reshare). A and G pick Kaam ka Parcha for its floor and interview story. C says both are mis-scored. The real disagreement is which judge matters: engagement decides the shortlist, the interview decides the offer. Reviews 4 and 5 settle it: ~100 slots against ~5 entrants makes the interview binding. G's judge wins, but D/E are right that a clip with no face gets ignored. F's merge serves both judges; six of seven reviewers converged on it.

**Speakerphone honesty.** E: "that's how my grandmother uses a phone; only engineers would object." C/F/G: Noise Canceller is voted by exactly those engineers. Both right for their audience; the award is decided by G's.

**Should #6 be public?** E: interview-only, it bores everyone and smells of benchmark. B/C/G: a deltas-only carousel is the one thing an engineer reshares. F: public repo, never the nominated post. Verdict: F, with C/G's carousel as an angle post.

**Virality ceiling.** D prices #1 at 400–1,000 reactions off creator-account humour reels; C notes a ~700-follower student's baseline is 5–15. Reviews side with C. Plan for 60–150, which clears the field; a Ganesh reshare is a bonus, not a plan.

## Blind Spots the Council Caught

- **Translation gap.** Sun-Saathi's signature scene (Hindi caller → Bengali captions; E's Tamil parent/Hindi landlord) needs MT. Prisma transcribes; no Gnani API translates; translation is a dead row. Without it #1 is same-language Live Transcribe plus a Timbre reply.
- **No WS flush/end-of-stream** (notes line 129): the final "haan" of any confirm loop can be lost; zero-padding before close is inferred, untested.
- **Hours.** 75 h total; R5 §6's social playbook costs 20–30 h. Build budget ~45–55 h. D's weekly grandparent series and B's Code-for-a-Billion dual-submit are unaffordable.
- **Gramvaani** (OpenSLR 118) is the only real Indic telephone corpus; nobody named it, so "what real phone speech did you test on?" has no answer. Evaluation-only, never demo data.
- **Synthetic-data rule vs filming real people.** Rule 8 bans real PII and recorded calls; scripted lines with fake amounts are defensible but unconfirmed.
- **Rule 7 "misleading demos"**: a simulated line shown as a phone call needs on-screen disclosure. Bites the merge hardest.
- **D's 30-person first-hour list** sits near "no engagement exchanges". Organic comments only.
- **Award inflation for #2**; **EULA breach in every split-screen proof card** (absolute WER, "Prisma vs Whisper" burned in); **ASHA dismissed on casting alone** when a relative could play her from a script, exactly as #1's hero problem was solved. ASHA stays the Real Deal fallback.
- **Rule 9 scope**: a garage is a small enterprise; a consumer relay app needs reframing for telcos/banks.

## Factual Corrections to Carry Forward

1. **`bias_list` requires `format=verbatim`** (02-speech-apis lines 68, 87, 375) and **invalid boosting on REST is silently ignored** (line 73). A's W1 test pairs it with `transcribe` and would read "no gain". Run bias A/B in verbatim; score ITN separately in transcribe.
2. **ITN scope** is a documented CONFLICT (line 48); treat as hi-IN/en-IN only. Fine for Hinglish; it caps a Bengali/Tamil customer leg to Timbre read-back, not ITN capture.
3. **"Real by construction" is overstated** (Reviews 4, 6). No PSTN exists; the Timbre call is a simulated codec leg and needs the same disclosure F demanded of #1.
4. **Award re-score.** Real Deal names farmers/kirana/health workers; Noise Canceller says *telephonic*. #2 as written: Award 3 (total 33). #2 with phone leg primary: Noise Canceller + Mixed Vibes, Award 4 (total 34). #1: speakerphone fails Noise Canceller and a consumer app is not Real Deal's named users, Award 3 (total 31). D's "#2 = 14–15/21" is R5's number; shortlist's 16–17 stands, rising to ~17–18 with a reacting customer.
5. **AMR-NB 4.75 vs 5.9**: both appear in Gnani's paper (bitrate range 4.75–12.2; 5.9 kbps is the named open benchmark). No contradiction.
6. **EULA**: applicability to the contest is `[SPEC]` (06 line 67). R4's guard stands: deltas only, never "Gnani vs X", ask Discord before any absolute number.
7. **A's "elderly relative you don't have"**: G1 is open, not failed.

## The Recommendation

**Build Kaam ka Parcha, phone-sealed** (F's merge, G's "2G job card" framing), with Line Noise Lab as its spine.

1. **User**: a two-wheeler mechanic in a Delhi workshop (auto is a Gnani vertical with no Gnani product; Rule 9 satisfied as a small enterprise).
2. **Trigger**: mechanic taps record and dictates the job in Hinglish over engine noise.
3. **Leg 1**: Prisma REST `hi-IN` `format=transcribe` (ITN) with a parallel verbatim pass for `bias_list` part names → schema-validated extractor (external LLM, Evon flag-switched for demo day) → job card with per-field confidence.
4. **Leg 2**: the system "calls" the customer: Timbre `hi-IN` renders "kul chhe sau pachaas rupaye, Somvaar shaam tak, theek hai?" as 8 kHz µ-law, pushed through ffmpeg G.711 / AMR-NB 4.75 + street noise; the customer (parent or grandparent, the portable hero) answers "haan" or "nahi, saade chaar sau"; the reply passes back through the same chain into Prisma at `x-sample-rate 8000`, telephony preset.
5. **Gnani load-bearing**: Prisma on noisy code-mixed 8 kHz with ITN; Timbre number/date normalisation at µ-law; the harness measures exactly this leg.
6. **Artefact**: a *confirmed* parcha (customer-sealed ₹ total and date) as PDF/WhatsApp text, not a form.
7. **Demo scene (60 s)**: 0–3 s the customer laughs "haan" into her phone; garage + engine; job card fills; Timbre call; correction caught; parcha seals; proof card at 0:44–0:50; end on her line to camera. On-screen disclosure during the call: *"Simulated phone line: audio passed through G.711/AMR-NB 4.75 kbps + street noise at 5 dB. No call was placed. All names and amounts are synthetic."*
8. **Awards**: Noise Canceller primary, Mixed Vibes secondary. Do not claim Real Deal.
9. **Out**: live captions, speakerphone relay, Evon in the critical path, a Bengali/Tamil ITN leg (Timbre read-back in Bengali is a stretch only), any "Gnani vs X" comparison, Code for a Billion.

**Fallbacks.** haan/nahi gate fails: walk-up mode with in-person read-back (Mixed Vibes + Solo Ninja), proof card from harness deltas. Casting fails: a classmate answers the call. Both noise and phone gates fail: Claim-by-Call with a relative playing the ASHA from a script.

**Public vs interview-only.** Public: harness repo (SynthCall-IN generator, degradation chain, seeded manifest) and one deltas-only carousel as an angle post (denoise gain, `bias_list` gain in verbatim, entity accuracy with vs without read-back, preset A/B, latency decomposition), labelled "measured by us, N, settings, date". Interview-only: absolute WER/CER-vs-SNR curves, Gramvaani results, endpoint and hallucination rates. **Numbers on screen**: only our own pipeline's deltas or our own end-to-end outcome, labelled as such, no other vendor named beside it; no absolute Prisma WER unless Discord consents by Oct 10.

## Go/No-Go Gates (week 1, dated)

| Date | Gate | Pass | Kill/pivot |
|---|---|---|---|
| Oct 6 | Credit burn: one 6-s STT + one TTS call, read dashboard | Grid of 100 utts × 3 codecs × 3 SNRs ≤ 40% of 5,000 | Shrink to 2 codecs × 3 SNRs × 60 utts |
| Oct 7 | ₹/part/date exact-match on 10 scripted Hinglish lines beside a running scooter, REST `transcribe` | ≥ 70% amounts exact | Drop walk-up arm; phone leg only, noise added synthetically |
| Oct 8 | Timbre `hi-IN` total in `container: mulaw` 8 kHz, round-tripped through Prisma | Amount recovered ≥ 9/10; intelligible to 3 listeners | Sweep voices (R4 voice × channel); normalise text ourselves |
| Oct 10 | haan/nahi drop rate at AMR-NB 4.75 + 5 dB, telephony preset, 50 clips; hallucination on 20 engine-only clips | Drop ≤ 10%; hallucinated words ≤ 1/clip | Prompt for a longer phrase ("haan theek hai"); if still > 25%, revert to walk-up fallback |
| Oct 10 | Discord answers: scripted real-person filming = synthetic? Own-system deltas/end-to-end numbers OK under EULA? | Both yes in writing | No: Timbre voices both parties, hero reacts silently; no numbers in public post |
| Oct 12 | Casting: customer-hero (consent, filming date ≤ Oct 22) + one garage/mechanic | Both confirmed | Classmate as customer; own scooter + friend as scripted mechanic, disclosed |
| Oct 15 | `bias_list` A/B in verbatim, 30 part/brand names, score 1.0 and 1.5 | Measurable part-name gain | Drop bias from pipeline and proof card |
| Oct 19 | Line Noise Lab v0: 100 SynthCall utts × {G.711, AMR 4.75} × {clean, 10, 5, 0 dB} → manifest + CER/entity curves + one delta figure; WS zero-pad flush recovers last "haan" ≥ 95% | All produced | WS unreliable → customer leg on REST ≤ 60 s (turn-based) |

## The One Thing to Do First

Monday Oct 6, before any UI: record the ten scripted Hinglish garage lines (₹ amount, part name, date) on your phone beside a running scooter, read the credit dashboard, push them through `POST /stt/v3` `hi-IN` twice (`format=transcribe` for ₹ exact-match; `format=verbatim` with and without `bias_list`), read the dashboard again, and post the two Discord questions (synthetic-data scope, EULA numbers). Everything else is sized by those three numbers.
