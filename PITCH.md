# Kaam ka Parcha (काम का पर्चा): solution pitch

**A job card the mechanic speaks, and the customer confirms on a real phone call.**
Live: <https://kaam-ka-parcha.onrender.com> · Code: <https://github.com/HarshdipSaha/kaam-ka-parcha> · Demo video: [YouTube link]

## The problem

In a two-wheeler or four-wheeler garage, the estimate is spoken. The mechanic says "saade chaar sau lagega", the customer leaves, and at pick-up the bill says ₹900. Greasy hands and a loud bay make typing impossible, and the customer has nothing in writing. Thus every pick-up can turn into an argument where neither side has proof.

## What I built

1. The mechanic speaks the estimate in Hinglish. Gnani **Prisma** transcribes it, and the app fills an itemised slip (parts, labour, delivery day).
2. Rupee amounts are read by a fixed Hinglish number grammar (ढाई, साढ़े, सवा, "बारह सौ"), never by a language model. A price is locked only when **two separate recordings agree**; a doubtful one stays flagged.
3. One tap places a real phone call (Twilio). Gnani **Timbre** reads the estimate back in Hindi, the customer replies by voice, and only a clear "haan, theek hai" confirms. An unclear reply gets a retry, then a written fallback.
4. On confirmation the app seals a PDF with the transcripts and SHA-256 hashes inside, opens a public verify page, and texts the customer the link.

Besides this, every call starts with a DPDP consent notice, consent is time-stamped in the audit log, phone, Aadhaar and PAN numbers are masked before text reaches the external extractor, and money is stored as integer paise.

## Evidence (synthetic Timbre speech unless stated; all in [`docs/gates.md`](docs/gates.md))

- Single-amount re-ask recovery rose from **73.3% to 96.3%** after normalising Prisma's formatted fractions (1,000 live rows), and held at 96.8% on a fresh held-out set.
- One recording alone accepted a wrong amount 2.2-2.4% of the time, so it is never trusted alone. Two agreeing recordings settled 94.8% at the first pair with 0.2% wrong, and 0 wrong in 558 clean and control pairs.
- I picked the read-back voice with an echo test (Timbre speaks, Prisma listens): Vikrant was understood **120/120** on a 4.75 kbit/s AMR-NB line at 0 dB.
- A real Twilio call to my own phone reached a confirmed, sealed parcha on 2026-10-07. Also, Lighthouse mobile on the live site gives Accessibility 100 and Performance 83-91, and 826 offline tests pass.

## Honest limits

- Most evidence is synthetic speech plus my own calls, so it shows the logic works; a test across many speakers is still to do.
- Item names come from an external OpenAI-compatible model; Gnani Evon is not used yet. Amounts never depend on it.
- The `/stage` page simulates the phone line; the real call is the button on `/workshop` (Twilio trial, verified numbers only). WhatsApp is copy to clipboard. A correction spoken on a real call passes the offline tests but has not been tried live.

## Who pays

The workshop, because a customer-confirmed estimate protects it from pick-up disputes. About ₹99 per workshop per month is my untested guess, to check with garage owners. Reach is through spare-parts dealers and garage associations, and the next features are a GST invoice and a UPI advance from the same confirmed card.
