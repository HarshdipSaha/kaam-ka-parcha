# Notes index: Gnani Great Indian AI Internship Challenge

Research gathered 2026-10-04 (37 days before the Nov 10 deadline). Start with `01`, then whichever layer you need.

| File | What it answers | Read when |
|------|-----------------|-----------|
| [01-hackathon-overview.md](01-hackathon-overview.md) | Rules, eligibility, the 10 awards, selection pipeline (engagement → review → interview → offer), submission checklist, dates, official links, open questions | Always first |
| [02-speech-apis.md](02-speech-apis.md) | Prisma v2.5 STT (REST ≤60 s, realtime WebSocket, batch + diarization), Timbre v2.5 TTS (REST/SSE/WS, 42 voices, normalisation), voice cloning; limits, auth, message protocols, gotchas, doc contradictions | Designing or coding anything against `api.vachana.ai` |
| [03-sdks-and-integrations.md](03-sdks-and-integrations.md) | `gnani-vachana` Python SDK, LiveKit and Pipecat plugins, the three use-case tutorials, and the finding that **no Evon/LLM endpoint exists in the docs** | Picking the integration path |
| [04-agent-builder-and-platform-api.md](04-agent-builder-and-platform-api.md) | Gnani Agent Builder (no-code voice agents, `api.inya.ai`, "Pampa" LLMs, outbound test calls to whitelisted numbers); whether it's usable for the contest | Considering a phone-call front end |
| [05-models.md](05-models.md) | Evon v3.3 (Nemotron-based 30B-A3B, public weights, hosting options, benchmark strengths/weaknesses), Prisma and Timbre published benchmarks, Warp, Artha | Deciding how (and whether) to run Evon |
| [06-company-and-landscape.md](06-company-and-landscape.md) | Gnani's business, funding, hiring, this challenge's public footprint, current entrants, competitors (Sarvam, AI4Bharat, Bhashini), gaps Gnani itself names | Positioning the idea |

Raw sources: `../raw/llms.txt` (docs index), `../raw/llms-full.txt` (full docs dump, 17.8k lines), `../raw/sitemap.xml`.
Idea work: `../wayfinder/MAP.md` (decision map), `../research/` (R1–R6 findings), `../ideas/` (shortlist, council verdict, spec).

## Ten facts that shape the idea

1. **Shortlisting is engagement-driven** (reactions, comments, reshares on one nominated LinkedIn post + one X post). The interview decides the offer.
2. **Only Prisma (STT), Timbre (TTS) and voice cloning are behind the 5,000 credits.** Evon has no hosted API; it must be self-hosted (weights are public on HF, ~63 GB bf16, community GGUF 17–32 GB).
3. **No pricing is published anywhere.** Credit burn rate must be read off the dashboard before heavy testing.
4. **8 kHz telephony is first-class**: `x-sample-rate: 8000`, telephony VAD presets, µ-law/A-law TTS output, batch `with_denoise`. Prisma leads on noisy 8 kHz benchmarks (Gnani's numbers) but trails Sarvam/Microsoft on the public MUCS code-switch set.
5. **STT languages:** en, hi, bn, gu, kn, ml, mr, pa, ta, te (-IN). Batch lacks gu and pa. No Odia/Assamese/Bhojpuri STT. Hinglish has a single TTS voice (Poorvi).
6. **Realtime STT** = PCM16 mono, 1024-byte frames at real-time pace, 15-min cap, final transcripts only, config in upgrade headers (browser needs a backend proxy).
7. **Diarization** is batch-only and capped at two speakers.
8. **Synthetic data only** in demos (terms). No real numbers, Aadhaar, PAN, or recorded calls.
9. **Already taken by entrants:** voice form-filling, Hinglish support bot, voice puzzle games, Bhojpuri-via-Hindi; ~30 "audio notes summariser" repos look like a Gnani hiring assignment. Avoid those shapes.
10. **Gaps Gnani itself names:** three-way code-switching, real-time voice with Evon's reasoning off, rural/feature-phone/2G conditions. The EULA restricts publishing benchmarks of Gnani's product; measure our own system, not "Gnani vs X".
