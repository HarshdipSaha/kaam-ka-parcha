# Spec: Kaam ka Parcha, phone-sealed (working title)

**One line:** a job card your mechanic speaks over engine noise, and your customer confirms by phone, in Hinglish, with the rupees right.

Locked 2026-10-04 after research (R1–R6), a six-idea shortlist and a 7-seat council (`council-verdict.md`). Hand-off: `/writing-plans` in a fresh session. Deadline Nov 10 2026; first public post ≈ Oct 25.

## Problem and user
Two-wheeler and car workshops run on verbal estimates; "what was agreed" is disputed daily; mechanics do not type. Auto is a vertical Gnani sells into (Tata Motors, Horsepower) with no Gnani product for the workshop floor, so it treads on nothing and counts as a "practical need for enterprises" (terms, rule 9). Every utterance is dense in exactly what Prisma's ITN and Timbre's normalisation are for: part names, ₹ amounts, dates. The noisy workshop and the 8 kHz customer call are the Noise Canceller brief.

**Primary user:** the mechanic (dictates). **Second party:** the customer (confirms by phone). **Buyer, later:** multi-bay workshops / dealer service centres.

## What it does (two legs, one artefact)
1. **Leg 1, workshop.** Mechanic taps record and dictates in Hinglish over the running engine: "front brake pad badla, part saade chaar sau, labour do sau, Somvaar shaam tak." Prisma REST `hi-IN` runs twice: `format=transcribe` (ITN → ₹450, ₹200, date) and `format=verbatim` with `bias_list` of part/brand names. A schema-validated extractor (external LLM in development; Evon flag-switched for the final demo) fills the job card with per-field confidence; low-confidence fields are re-asked.
2. **Leg 2, the phone call.** The system "calls" the customer: Timbre `hi-IN` renders "kul chhe sau pachaas rupaye, Somvaar shaam tak, theek hai?" as 8 kHz µ-law, pushed through a simulated line (ffmpeg G.711 / AMR-NB 4.75 + street noise at a stated SNR). The customer answers "haan" or "nahi, saade chaar sau"; the reply comes back through the same chain into Prisma at `x-sample-rate 8000`, telephony VAD preset. A correction re-runs Leg 1's extractor on the corrected field only.
3. **Artefact.** A **confirmed parcha**: customer-sealed ₹ total and promised date, as PDF + WhatsApp text, with the two transcripts and timestamps attached. Not a form; a confirmed agreement.

**Gnani models, load-bearing:** Prisma v2.5 (noisy code-mixed speech, ITN, 8 kHz telephony leg); Timbre v2.5 (₹/date normalisation at µ-law). **Optional:** Evon v3.3 for extraction on demo day (rented GPU, ₹3–5k cap). **Spine:** Line Noise Lab, the harness that measures Leg 2 (SynthCall-IN via Timbre → codec × SNR × loss → Prisma → CER / entity exact-match / haan-nahi drop / hallucination on non-speech).

## Implementation options for the customer leg (decide in planning)
- **Simulated line (default):** server applies the ffmpeg chain to Timbre output and to the recorded reply; customer hears/answers on a second device or browser. Must carry the on-screen disclosure below.
- **WhatsApp voice-note leg (honest real channel):** Timbre audio sent as a voice note; customer replies with a voice note; Prisma transcribes. Opus, not 8 kHz; good for the "works with the phone they have" story.
- **Realtime WS vs REST for the reply:** WS has no documented flush/end-of-stream (zero-pad before close, untested); REST ≤60 s turn-based is the safe fallback for a one-word "haan".

## 60-second demo (storyboard)
| Time | Shot |
|---|---|
| 0–3 s | Customer (parent/grandparent, the hero) laughs "haan!" into her phone |
| 3–8 s | Garage, engine running: "Every repair in India is a verbal deal. This one gets confirmed." |
| 8–12 s | Mechanic dictates; raw transcript → job card fills, ₹ and date rendered |
| 12–40 s | Timbre "calls" the customer; she corrects one amount ("nahi, saade chaar sau"); the card updates; she confirms; parcha seals |
| 40–46 s | The unexpected beat: her reaction to being read the bill by a voice in Hindi |
| 46–53 s | Proof card: our own deltas only (see rules), "Prisma v2.5 + Timbre v2.5", "1 student, N days" |
| 53–60 s | She says one line to camera; end card with the two hashtags |

**On-screen disclosure during the call (rule 7, "misleading demos"):** *"Simulated phone line: audio passed through G.711 / AMR-NB 4.75 kbps + street noise at 5 dB. No call was placed. All names and amounts are synthetic."*

## Awards and positioning
- **Primary: Noise Canceller** (the phone leg is telephonic by construction, measured). **Secondary: Mixed Vibes** (Hinglish with ITN-dense content). Solo Ninja and Demo Day by default. **Do not claim Real Deal** (its named users are farmers, kirana, health workers).
- Public framing: "the 2G job card" (Gnani's own rural-ASR paper names AMR-NB 4.75, AGC and jitter as the unsolved end-user problem).

## Rules for numbers in public (EULA-safe)
Publish only **our own pipeline's deltas or end-to-end outcomes**, labelled "measured by us, N utterances, settings, date": denoise on/off, `bias_list` on/off (verbatim), entity accuracy with vs without read-back, preset A/B, latency decomposition. **Never** a "Prisma vs Whisper/Google" split-screen or an absolute Prisma WER unless Gnani confirms on Discord. Absolute WER/CER-vs-SNR curves and Gramvaani results are **interview-only**.

## Go/No-Go gates (week 1–2)
| Date | Gate | Pass | Kill / pivot |
|---|---|---|---|
| Oct 6 | Credit burn: one 6-s STT + one TTS call, read the dashboard | Planned grid (100 utts × 3 codecs × 3 SNRs) ≤ 40% of 5,000 credits | Shrink to 2 codecs × 3 SNRs × 60 utts |
| Oct 7 | ₹/part/date exact-match on 10 scripted Hinglish lines beside a running scooter, REST `transcribe` | ≥ 70% amounts exact | Drop walk-up arm; phone leg only, noise added synthetically |
| Oct 8 | Timbre `hi-IN` total as `mulaw` 8 kHz, round-tripped through Prisma | Amount recovered ≥ 9/10; intelligible to 3 listeners | Sweep voices (R4 voice × channel); pre-normalise text ourselves |
| Oct 10 | haan/nahi drop rate at AMR-NB 4.75 + 5 dB, telephony preset, 50 clips; hallucination on 20 engine-only clips | Drop ≤ 10%; ≤ 1 hallucinated word/clip | Prompt for a longer phrase ("haan theek hai"); if still > 25%, walk-up fallback |
| Oct 10 | Discord answers in writing: scripted real-person filming counts as synthetic? Own-system deltas OK under the EULA? | Both yes | Timbre voices both parties and the hero reacts silently; no numbers in the public post |
| Oct 12 | Casting: customer-hero (consent, filming ≤ Oct 22) + one garage/mechanic | Both confirmed | Classmate as customer; own scooter + friend as scripted mechanic, disclosed |
| Oct 15 | `bias_list` A/B in **verbatim**, 30 part/brand names, scores 1.0 and 1.5 | Measurable part-name gain | Drop bias from pipeline and proof card |
| Oct 19 | Line Noise Lab v0: 100 SynthCall utts × {G.711, AMR 4.75} × {clean, 10, 5, 0 dB} → manifest + CER/entity curves + one delta figure; WS zero-pad flush recovers the last "haan" ≥ 95% | All produced | WS unreliable → customer leg on REST, turn-based |

## Fallbacks
- haan/nahi gate fails → **walk-up mode** with in-person Timbre read-back (Mixed Vibes + Solo Ninja), proof card from harness deltas.
- Casting fails → a classmate answers the call.
- Both noise and phone gates fail → **Claim-by-Call** (ASHA incentive claim) with a relative playing the ASHA from a script (Real Deal).

## Explicitly out of scope
Live call captions / speakerphone relay (Sun-Saathi); Evon in the critical path; Bengali/Tamil ITN leg (Timbre read-back in Bengali is a stretch only); any "Gnani vs X" comparison; Code for a Billion dual-submission; real PSTN/Twilio/Exotel integration (stretch note only); any BFSI/insurance/fraud framing (treads on Gnani products).

## Budget
75 h total (15 h/wk × 5). Reserve 20–30 h for the social plan (pre-launch commenting from week 2, 90-min launch windows Oct 25 and later, 2–3 angle posts/week to Nov 9, replies). Build budget ≈ 45–55 h. Compute ≤ ₹5k (Evon demo day only). Credits: ≤ 40% on the harness grid.

## Facts to verify live in the first API session
`bias_list` requires `format=verbatim` and REST silently ignores invalid boosting; ITN scope beyond hi/en is a documented conflict; `multi_lang_codes` format; WS behaviour without flush; voice-clone not used; credit cost per STT second and TTS character.

## Interview story (what the build must let you say)
Dataset-level CER by SNR band at 8 kHz, never upsampled; entity exact-match for ₹/dates/part names with and without read-back; premature-endpoint rate when sweeping `x-min-silence-ms` at 5 dB; short-utterance drop for haan/nahi; hallucinated words on engine-only segments; what `bias_list` did at 1.0 vs 1.5; ITN behaviour on "saade" vs "pachaas", lakh/crore; Gramvaani as the real-telephony sanity check.

Sources: `../research/R1–R6`, `../notes/02`, `05`, `06`, `shortlist.md`, `council-verdict.md`.
