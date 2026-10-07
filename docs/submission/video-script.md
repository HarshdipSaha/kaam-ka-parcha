# 60-second demo video: storyboard

Exactly 60 seconds, captions on (Hindi and English), recorded on the deployed `/stage` page (keep a local-run take as a fallback). Use only the synthetic demo identifiers (`KA-01-AB-1234 (Synthetic Demo)`, a fake phone number) and your own consented voice. The simulated-line disclosure must be visible on screen. Numbers quoted must match [`docs/gates.md`](../gates.md).

| Time | Shot | On-screen caption (HI / EN) | Voice-over |
|---|---|---|---|
| 0-5 s | Close-up: a hand points at a paper bill, text overlay "₹450?" then "₹900?" | "₹450 बोला था, ₹900 लिख दिया?" / "Said ₹450, billed ₹900?" | "₹450 bola tha, ₹900 likh diya?" |
| 5-15 s | `/stage`: mechanic taps the mic and speaks: "Front brake pad saade chaar sau, labour do sau, Somvaar shaam tak." Slip fills in. | "मिस्त्री बोलता है" / "The mechanic speaks" | "The mechanic just speaks the estimate. No typing." |
| 15-25 s | Flagged amount rows appear in yellow; tap the whole-estimate mic and repeat once; both settle. | "दो बार सुनकर ही रकम पक्की" / "An amount counts only after two recordings agree" | "An amount is only accepted when two recordings agree. Doubtful ones stay yellow." |
| 25-40 s | Customer pane: play the read-back; say "haan, theek hai"; slip gets the APPROVED stamp; PDF and WhatsApp text buttons appear. | "ग्राहक सुनकर 'हाँ' बोलता है" / "The customer hears it and says yes" | "The customer hears the estimate in Hindi over a phone line and confirms by voice." |
| 40-55 s | One honest failure: speak a look-alike amount over heavy noise ("इकतीस हज़ार"); the slip refuses to settle and asks for one more clear recording; then it settles. | "शक हो तो पूछता है, अंदाज़ा नहीं लगाता" / "When unsure it asks, it never guesses" | "When the line is noisy and two numbers sound alike, it asks again instead of guessing." |
| 55-60 s | End card: logos/names of models, disclosure line, hashtags. | "Gnani Prisma + Timbre · simulated phone line · WhatsApp = copy · #GnaniAI #GreatIndianAIInternshipChallenge" | "Built on Gnani Prisma and Timbre." |

**Checklist before recording.** Disclosure line (simulated line, clipboard WhatsApp) visible in the end card and in the customer pane. Synthetic data only. No Gnani Evon claim (extraction runs on an external LLM unless task A8 is done). Do not show `.env`, keys or the credit balance. Record a take of the failure-and-recovery beat several times; use a real one, not an edit.
