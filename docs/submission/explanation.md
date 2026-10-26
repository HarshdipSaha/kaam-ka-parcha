# Kaam ka Parcha: written explanation (draft for the submission form)

> Draft for the human to edit and submit. Every number links to [`docs/gates.md`](../gates.md). Replace the bracketed placeholders.

**Problem.** In two- and four-wheeler workshops the repair estimate is spoken, and at pick-up it is disputed: "₹400 bola tha, ₹750 ka bill kaise bana?" The mechanic has greasy hands in a noisy bay and cannot type; the customer has nothing in writing.

**Who uses it.** A workshop mechanic (dictates the estimate in Hinglish) and the vehicle owner (hears it read back and confirms by voice, "haan, theek hai").

**How it works.**
1. The mechanic speaks the estimate on `/workshop`. Prisma transcribes it twice (`transcribe` and `verbatim` with automotive bias words).
2. Rupee amounts are read by a deterministic numeral grammar (डेढ़, ढाई, साढ़े, सवा, पौने, "बारह सौ"), never by a language model. An amount is settled only when two separate recordings agree; look-alike numbers such as इक्कीस/इकतीस need a third. Anything doubtful stays flagged on the slip. Evidence: [Hinglish amounts note](../benchmarks/hinglish-amounts.md).
3. Timbre reads the estimate back to the customer over a simulated phone line (G.711 / AMR-NB, engine noise). The customer replies by voice; an unclear reply goes to review, retry or a fallback, never to confirmation.
4. On confirmation a sealed PDF (embedded audit manifest and hashes) and a WhatsApp-ready text are produced.

**Gnani models and endpoints used.**
- Gnani Prisma v2.5, speech-to-text REST (`/stt/v3`), `transcribe` and `verbatim` formats, automotive bias words, language `hi-IN`.
- Gnani Timbre v2.5, text-to-speech REST, voice Vikrant (chosen by a Timbre-to-Prisma echo test; see the Jugaad post).
- Field extraction (item labels, delivery) uses an external OpenAI-compatible LLM. **Gnani Evon is not used today** (no hosted Evon API is published); amounts never depend on the LLM. [Update this line only if task A8 is completed.]

**What is measured** (synthetic Timbre speech unless stated; see limitations).
- Single-amount re-ask recovery rose from 73.3% to 96.3% after normalising Prisma's formatted fractions (1,000 live rows; 96.8% on a fresh held-out set): [gates.md, section 11](../gates.md#11-money-path-safety-and-benchmark-v2-effort-009).
- A single recording's accepted amount was wrong 2.2-2.4% of the time, so it is never trusted alone. Two agreeing recordings settle 93-95% of amounts at the first pair with 0.2-0.4% wrong (all at 0 dB) and 0 wrong in the clean and control conditions (same section).
- Read-back echo: Vikrant with amounts in words was recognised 120/120 on a 4.75 kbit/s AMR-NB line at 0 dB (same section).
- Licensed real Hindi speech (AI4Bharat IndicContextEval, CC BY 4.0): relative error change versus a clean line, by noise level and codec, in the licensed-speech section of gates.md.

**Honest limitations.**
- Evidence is mostly synthetic speech. It supports the application logic, not general recognition accuracy.
- Owner-recorded real takes: [one speaker; add the result here once scored, or state that they are not yet scored].
- The `/stage` browser view simulates a phone line. A separate Twilio integration places real calls for read-back, spoken corrections and confirmation; the owner confirmed it working on 2026-10-26. WhatsApp is clipboard copy; the Twilio call path separately attempts a verification-link SMS after confirmation.
- Extraction is not on a Gnani model (see above).

**Who pays (hypothesis).** The workshop: a customer-confirmed estimate protects it against pick-up disputes. About ₹99 per workshop per month is an untested guess to check with garage owners; reach is through spare-parts dealers and garage associations; the next features are a GST invoice and a UPI advance from the same confirmed card. [Replace with what the garage visits show.]

**Data and consent.** Only synthetic data, a licensed corpus and self-recorded consented audio are used. No private call recordings, third-party voices, real phone numbers or IDs are committed. The real-call demo uses the owner's own consented participation and masks identifying details.

**Each member's contribution.** [Human to fill in.]

**Links.** Demo: https://kaam-ka-parcha.onrender.com/stage. Video: [URL]. Nominated posts: [URLs, with #GnaniAI #GreatIndianAIInternshipChallenge].
