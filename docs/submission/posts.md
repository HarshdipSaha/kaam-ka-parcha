# Post drafts (human edits, posts and nominates in the form)

Rules: use **#GnaniAI** and **#GreatIndianAIInternshipChallenge**, tag Gnani AI, no engagement-exchange requests, no claim beyond [`docs/gates.md`](../gates.md). Replace bracketed placeholders. Suggested dates: launch ~15 Oct, build story ~22 Oct, Jugaad ~29 Oct, final demo ~3 Nov.

## 1. Launch (problem + 20-second clip)

**LinkedIn.**
"₹450 bola tha, ₹900 likh diya?" Every workshop owner has heard it at vehicle pick-up. Estimates are spoken, never written.

I built Kaam ka Parcha for the #GreatIndianAIInternshipChallenge: the mechanic speaks the estimate in Hinglish, the customer hears it read back in Hindi and says "haan", and only then does a sealed job slip appear.

Built on Gnani Prisma (speech to text) and Timbre (read-back voice). The phone line in the demo is a simulation and the "WhatsApp" step is copy-to-clipboard, and the app says so.

20-second clip: [VIDEO LINK]
#GnaniAI #GreatIndianAIInternshipChallenge @GnaniAI

**X.** "₹450 bola tha, ₹900 likh diya?" Mechanic speaks, customer hears it read back and says "haan", then the job slip is sealed. Built on Gnani Prisma + Timbre. Simulated phone line, said openly. [VIDEO] #GnaniAI #GreatIndianAIInternshipChallenge

## 2. Behind the build: Hinglish rupee amounts

**LinkedIn.**
Gnani Prisma writes "साढ़े चार सौ" as `04:30 100`. A clock time. Here is why that mattered.

Rupee amounts in workshop talk are fractions: डेढ़, ढाई, साढ़े, सवा, पौने. Prisma's formatted output turns them into strings like `04:30 ₹100` or `साढ़े 4,000`. I use that formatted pass only as a cross-check of the spoken words, so those strings first have to be translated back. After doing that, recovery of a re-asked amount went from 73.3% to 96.3% on 1,000 live rows (96.8% on fresh amounts I had not tuned on).

It was still wrong 2.2-2.4% of the time at 0 dB, so a single recording is never trusted: an amount is settled only when two separate recordings agree. Numbers are synthetic speech, labelled as such. Write-up: [LINK to docs/benchmarks/hinglish-amounts.md]
#GnaniAI #GreatIndianAIInternshipChallenge

**X.** Gnani Prisma writes "साढ़े चार सौ" as `04:30 100`. Fixing that lifted amount recovery 73.3% -> 96.3% (1,000 live synthetic rows; 96.8% held-out). Still 2.2-2.4% wrong at 0 dB, so two recordings must agree. [LINK] #GnaniAI #GreatIndianAIInternshipChallenge

## 3. Jugaad: the echo loop that picked the read-back voice

**LinkedIn.**
How do you know the customer will actually hear "₹450" and not "₹450 and a phantom lakh"? I closed the loop: Timbre speaks the estimate over a simulated 4.75 kbit/s phone line with engine noise, and Prisma transcribes it. If Prisma cannot recover every amount, a person on a bad line probably cannot either.

Across voices and styles, Vikrant reading amounts in words was recognised 120/120 at the worst condition, ahead of digit style and other voices (Roopesh/digits 119/120, Chitra/words 113/120). The failures were recogniser insertions in the closing prompt, so I reworded it. Synthetic speech flatters results, and human listening is still on my list.
Numbers: [LINK to gates.md read-back section]
#GnaniAI #GreatIndianAIInternshipChallenge

**X.** I used Gnani Prisma to test Gnani Timbre: speak the estimate over a simulated AMR-NB line, transcribe it back, and pick the voice that survives. Vikrant + amounts in words: 120/120 at 0 dB. [LINK] #GnaniAI #GreatIndianAIInternshipChallenge

## 4. Real user (only if B5 happens; otherwise a self-recorded workshop clip)

**LinkedIn (template).**
[Name or "a mechanic in CITY", with their permission] tried Kaam ka Parcha for ten minutes. Their words: "[QUOTE]". What worked: [..]. What did not: [..]. [PHOTO/CLIP with permission, no faces or customer numbers.]
#GnaniAI #GreatIndianAIInternshipChallenge

**X (template).** A mechanic tried it for ten minutes: "[QUOTE]". [CLIP] #GnaniAI #GreatIndianAIInternshipChallenge

*(If B5 does not happen, replace with your own self-recorded workshop clip and say so.)*
