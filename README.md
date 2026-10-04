# Kaam ka Parcha (काम का पर्चा) — Phone-Sealed

> **A job card your mechanic speaks over engine noise, and your customer confirms by phone in Hinglish, with the rupees right.**

Built for **Gnani AI's Great Indian AI Internship Challenge** (Oct 1 – Nov 10, 2026).

---

## The Problem
Two-wheeler and four-wheeler workshops in India run on verbal estimates. Mechanics work with grease on their hands in loud environments and do not type. Customer repair estimates are constantly disputed at vehicle pick-up (*"Aapne ₹400 bola tha, ₹750 ka bill kaise bana?"*), costing workshops 5–8% of gross margins.

## The Solution
**Kaam ka Parcha** turns spoken Hinglish workshop estimates into a legally confirmed, customer-sealed agreement:

1. **Leg 1 (Workshop Floor):** Mechanic dictates the repair over running engine roar: *"front brake pad badla, part saade chaar sau, labour do sau, Somvaar shaam tak."*
   - Powered by **Gnani Prisma v2.5** running dual-pass:
     - `format=transcribe` (Indic ITN: parses *"saade chaar sau"* $\to$ ₹450, dates).
     - `format=verbatim` with automotive `bias_list` (boosts part and brand names).
2. **Leg 2 (Customer Telephony Loop):** The system calls the vehicle owner:
   - Powered by **Gnani Timbre v2.5** rendering 8 kHz $\mu$-law audio over a simulated telephony line (FFmpeg G.711 / AMR-NB 4.75 kbps + street noise).
   - Speaks in clean Hindi: *"Aapki gaadi ka kul chhe sau pachaas rupaye hua, Somvaar shaam tak milegi. Agar theek hai toh kahiye 'Haan, theek hai'."*
   - Customer confirms or corrects on the call; response captured by Prisma at 8 kHz.
3. **The Artefact (Confirmed Parcha):** Generates a customer-sealed digital agreement (PDF + WhatsApp summary) containing the itemized ₹ total, promised delivery date, and timestamped audio proof logs.

---

## Technical Moat: Line Noise Lab
A dedicated evaluation harness measuring acoustic resilience across:
- Codecs: G.711 $\mu$-law, AMR-NB 4.75 kbps.
- SNR bands: Clean, 10 dB, 5 dB, 0 dB.
- Metrics: Character Error Rate (CER), Word Error Rate (WER), entity exact-match on ₹ amounts, and short-utterance confirmation drop rates.

---

## Project Structure
- [`docs/ideas/spec.md`](docs/ideas/spec.md): Locked product specification and implementation plan.
- [`docs/ideas/shortlist.md`](docs/ideas/shortlist.md): Evaluation of shortlisted candidate ideas.
- [`docs/ideas/council/`](docs/ideas/council/): 7-seat council reviews and fact-checking verdicts.
- [`docs/notes/`](docs/notes/): Deep dives on Gnani speech APIs, SDKs, Evon LLM, and hackathon rules.
- [`docs/research/`](docs/research/): Enterprise, grassroots, and virality research (R1–R6).
- [`CONTEXT.md`](CONTEXT.md): Project terminology glossary.

---

## Setup & Prerequisites
1. Clone the repository.
2. Copy `.env.example` to `.env` and add your Gnani AI API key:
   ```bash
   cp .env.example .env
   ```
3. Python 3.10+ / Node.js environment.

---

## Target Awards
- **Primary:** Noise Canceller (8 kHz telephonic audio performance)
- **Secondary:** Mixed Vibes (code-mixed Hinglish + ITN)
- **Standalone:** Solo Ninja, Demo Day Drop (60s viral video)
