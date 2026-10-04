# Framed question (as given to all seven council seats, 2026-10-04)

DECISION: Which project should Harshdip (solo student, NSUT Delhi, laptop without GPU, ~15 h/week for 5 weeks until Nov 10 2026) build for Gnani AI's "Great Indian AI Internship Challenge", and with what changes?

CONTEXT
- Contest: build on Gnani's models: Prisma v2.5 STT (strongest on noisy 8 kHz telephony and Indic numerals/ITN; trails Sarvam/Microsoft on clean code-switch sets), Timbre v2.5 TTS (42 voices, 10 Indic langs, 8 kHz µ-law out), voice cloning, Evon v3.3 (30B-A3B LLM, self-host only, NOT covered by credits, weak at instruction-following/summarisation). 5,000 credits, no public pricing. Up to 100 internships (up to ₹1 lakh/month, individual); ten ₹50k awards (Noise Canceller = noisy telephonic audio, Real Deal = real-world impact for farmers/kirana/health workers, Main Character = regional language, Mixed Vibes = code-mixed, Jugaad Genius = creative use, Solo Ninja, Demo Day = best 60-s video, Crowd Favourite = public votes; Duo and Small Town not applicable).
- Selection: shortlist is driven by VERIFIED ENGAGEMENT (reactions, comments, reshares) on ONE nominated LinkedIn post and ONE X post (#GnaniAI #GreatIndianAIInternshipChallenge, tag Gnani); the offer is decided by an individual interview. Gnani is LinkedIn-native (company 124K followers, CEO 27K and reshares community content); field is tiny so far (first entrant posts: 5 and 26 reactions; Gnani's launch post 115). Rules: synthetic data only; genuine use of Gnani tech; no engagement exchanges/bots; EULA restricts publishing benchmarks of Gnani's product (publish only our own system's deltas).
- Standing decisions: solo; optimise for the shortlist with ONE award as secondary target (Noise Canceller or Real Deal favoured); first public post ~Oct 25 then iterate; no real PSTN line (8 kHz telephony simulation + speakerphone/WhatsApp voice notes); Evon only as a demo-time bonus on a rented GPU (₹3–5k cap); exclude plain BFSI collections bots.
- Gnani hires for: LLM inference (vLLM/SGLang), speech data engineering, full-stack + AI, and a new consumer-products team (mobile app, growth, reels).
- Hard API facts: Prisma realtime WebSocket emits FINAL transcripts only (no partials), one language per session, 15-min cap, config in upgrade headers so a browser needs a backend proxy; batch diarization is capped at 2 speakers; ITN documented mainly for hi/en; no Hinglish STT code (an undocumented multi_lang_codes exists); REST clips ≤60 s.
- Dead/crowded idea spaces: Hinglish support/sales bots, generic voice form-filling (entrant "Bolo"), audio-notes summarisers, farmer IVR, kirana khata (entrant "Voice Khata"), dubbing/translation, scheme chatbots.

THE SHORTLIST (full detail in docs/ideas/shortlist.md):
1. Sun-Saathi: live regional-script captions of a phone call for hard-of-hearing/elderly users + tap-to-reply spoken into the call by Timbre; "second-device relay" via speakerphone. 33/40.
2. Kaam ka Parcha (Garage Job-Card): mechanic dictates the repair in Hinglish over workshop noise → itemised job card + bill; Timbre reads the total back. 35/40.
3. Claim-by-Call: ASHA health worker phones in her visits over an 8 kHz line → NHM register + incentive claim with ₹ total, Timbre read-back. 32/40.
4. Sahi Bikri: regional-language insurance pre-issuance verification call + "said vs sold" diff against the 2-speaker telesales recording. 31/40.
5. Dhokha Desk: bank fraud-desk complaint intake with UTR/amount digit-by-digit read-back. 30/40.
6. Line Noise Lab: telephony-stress harness (Timbre-synthesised "SynthCall-IN" → codec × SNR × packet loss → Prisma → WER/CER/entity/switch-point curves). 28/40 standalone; proposed as the measurement spine of whichever product wins.
Pre-council recommendation: build #2 or #1 as the product with #6 as its spine.

AT STAKE: a ~₹6 lakh internship offer and five weeks of a student's time.

QUESTIONS: (a) Which idea, with what modifications (merging allowed)? (b) Ceiling vs floor between #1 and #2? (c) Is "second-device relay via speakerphone" an honest telephony story for Noise Canceller, or a hack? (d) Does #2 escape the "form-filling is crowded" verdict? (e) Should #6 be a public part of the submission or interview-only evidence? (f) What would a Gnani hiring manager see as a toy, or as treading on a Gnani product? (g) Is there anything NOT on the list that the research clearly supports and the shortlist missed?
