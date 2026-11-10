# Demo recording script: live site + real Twilio call (about 2:30)

The submission form asks for a **2–3 minute** video. This script runs about 2:30 with one real call to your own
phone, on the live site: <https://kaam-ka-parcha.onrender.com/workshop>.

It is built from what the code says on the call (`src/parcha/readback.py`, `_twilio_outcome_speech` in
`src/parcha/app.py`) and from the real calls placed on 2026-10-07 (`aidlc-docs/efforts/014-twilio-phone-leg/`).
Only the **"haan, theek hai" path has been proven live on a real call.** A spoken correction on the phone works in
the offline tests but has never been tried on a real call, so it is an optional beat: try it in the dry run first.

---

## 1. What the phone call does, second by second

Know this before recording, so nothing on the call surprises you on camera.

| # | What you hear on the phone | What you do |
|---|---|---|
| 1 | Phone rings from Twilio's US number (`+1 978…`). | Answer, put it on **speaker**. |
| 2 | **Twilio trial announcement** in English ("…trial account… press any key…"). | Open the **on-screen keypad** and tap **any digit**. A side button does nothing, and without a real key tap the call **ends after about 13 s** (this happened on 2026-10-07). Cut this part in editing, or caption it. |
| 3 | DPDP notice: *"DPDP Act 2023 ke antargat yeh call service estimate confirmation hetu record ki ja rahi hai."* | Stay silent. |
| 4 | Read-back in Hindi by Gnani Timbre (voice Vikrant): *"फ्रंट ब्रेक पैड: साढ़े चार सौ रुपये, लेबर: दो सौ रुपये. कुल छह सौ पचास रुपये. डिलीवरी सोमवार शाम."* (the labels are whatever the card shows) | Stay silent. Let the viewer hear it. |
| 5 | *"Agar aapko yeh manzoor hai, toh boliye: 'Haan, theek hai'. Kuch galat ho toh bataiye."* | Get ready. |
| 6 | **Beep.** Recording starts: up to 20 s, and it stops after **4 s of silence**. | Say **only** your reply, clearly, then stay **silent** for about 4 s. Anything else you say here (narration included) becomes part of the reply. |
| 7a | If you said yes: *"Dhanyavaad. Kul chhe sau pachaas rupaye. Aapka parcha confirm ho gaya. Likhit parcha aapko bhej diya jaayega."* Then the call hangs up. | Hang up when it does. |
| 7b | If it didn't catch you: *"Samajh nahi aaya. Kripya phir se boliye."* + beep | Say the yes again, slower, closer to the phone. |
| 8 | SMS from the Twilio number: Twilio's "Sent from a Twilio trial account" prefix, then *"Kaam ka Parcha #NNNNNN confirm ho gaya. Kul ₹650. Parcha: https://kaam-ka-parcha.onrender.com/verify/…"* | Show it on camera. |

At the same moment, the workshop page (polling every 2 s) switches to **Approved** (stamp, chime) by itself.

**Replies that confirm:** "Haan, theek hai" (best, because the call asks for exactly this), "Haan ji theek hai",
"Theek hai", "Manzoor hai", "Pakka", "OK". **Replies that don't:** "Hmm", "Achha", "Ji", or anything with "par" /
"lekin" / a number. An unclear reply gets a retry. After two retries the call moves to the written fallback, so say
the yes clearly the first time.

---

## 2. Before you record (do this 15 minutes before)

1. **Render, once:** Dashboard → kaam-ka-parcha → Environment → add `TWILIO_DEFAULT_TO` = your verified number
   (`+91XXXXXXXXXX`) → Save. The button then shows only `•••• last-4`, so no number is typed on camera.
   Skip it and the button shows a number box instead, which you'd have to blur.
2. **Twilio is still alive:** log in to the Twilio console and check the trial balance and that the trial
   number is still active (the trial started 2026-10-07). The dry run proves it anyway.
3. **Wake the server:** open <https://kaam-ka-parcha.onrender.com/health> and wait for `{"ok":true}`. The free plan
   sleeps after about 15 minutes and loses sessions, so keep the tab active between takes.
4. **Browser:** `/workshop` in a clean window, 125% zoom, EN toggle, bookmarks hidden, notifications off.
   Use `/workshop`, not `/stage`: the call button only appears on `/workshop`.
5. **Phone:** volume to max, Do Not Disturb on (calls allowed), keypad easy to reach. Film it with a second phone,
   or place it next to the laptop mic so the call audio lands in the recording.
6. **Quiet room** for the phone reply; save the background noise for the mechanic part.
7. **One full dry run** (this uses Gnani and Twilio credits). If you want the correction beat, try it here first
   (see section 4).
8. **Never on screen:** your full phone number, the Render or Twilio dashboards, `.env`, credit balances.

---

## 3. The script

Format: **SCREEN** = what is visible, **SAY** = your voice-over, **PHONE** = the call audio, **CAPTION** = on-screen
text added in editing.

### 0:00–0:15 · The problem
**SCREEN:** your face, or a crumpled handwritten bill.
**SAY:**
> "In Indian garages, the estimate is spoken. The mechanic says *'saade chaar sau lagega'*, and at pick-up the
> bill says nine hundred. Nothing is in writing, so there's no proof, only an argument.
> I built **Kaam ka Parcha**: the mechanic speaks the estimate, and the customer confirms it on a real phone call,
> using Gnani's voice AI."

### 0:15–0:22 · The live site
**SCREEN:** `kaam-ka-parcha.onrender.com/workshop`, the empty slip.
**SAY:**
> "This is the live website. I'm the mechanic. My hands are greasy and the bay is noisy, so I don't type. I speak."

### 0:22–0:38 · Dictate the estimate
**ACTION:** tap the yellow mic and speak:
> "**Front brake pad badla, part saade chaar sau, labour do sau, Somvaar shaam tak.**"

Tap stop. The slip fills in.
**SAY:**
> "Gnani **Prisma** turns my Hinglish into text, and the slip fills itself: brake pad, labour, ready Monday
> evening. The rupees don't come from a language model. A fixed Hinglish number grammar reads *'saade chaar sau'*
> as four hundred fifty."

**CAPTION:** `Speech-to-text: Gnani Prisma · amounts: rule-based, never an LLM`

### 0:38–0:55 · The money check (your strongest point)
**ACTION:** the flagged amounts ask for another recording. Use the per-row button (or "say it again"), repeat the
amounts, and show them settle: **₹450 + ₹200 = ₹650**.
**SAY:**
> "This is the part I care about most. A price is never locked from one recording. It's locked only when two
> recordings agree, and look-alikes like *ikkees* and *iktees* need a third. If a price is in doubt, it stays
> flagged. A wrong number never quietly ends up on a bill."

**CAPTION:** `Two recordings must agree before a price is locked`

### 0:55–1:05 · Place the call
**SCREEN:** the green **"Call the customer's phone (•••• 1234)"** button. Tap it. The page says
*"The customer's phone is ringing…"*
**SAY:**
> "Now the customer. They don't get a link they'll ignore. They get a real phone call. One tap."

### 1:05–1:12 · Phone rings, trial message
**SCREEN:** cut to the phone ringing. Answer on speaker.
**ACTION:** during the English trial message, open the keypad and tap a digit. Say nothing.
**EDIT:** trim this to 1–2 s, or keep it with **CAPTION:** `Twilio trial account: tap a key to continue`

### 1:12–1:35 · The read-back (let it play)
**PHONE:** DPDP notice → the read-back in Hindi → *"Agar aapko yeh manzoor hai, toh boliye: 'Haan, theek hai'…"*
**SAY:** nothing while it plays. The viewer should hear the real call.
**CAPTION** (line by line):
- `Real phone call via Twilio · voice: Gnani Timbre`
- `"Front brake pad ₹450, labour ₹200, total ₹650, delivery Monday evening"`
- `"If you agree, say: Haan, theek hai"`

### 1:35–1:45 · Say yes
**PHONE:** beep.
**YOU, to the phone, clearly, then silent:**
> "**Haan, theek hai.**"

**PHONE:** *"Dhanyavaad. Kul chhe sau pachaas rupaye. Aapka parcha confirm ho gaya…"* Then the call hangs up.
**CAPTION:** `"Thank you. Total ₹650. Your parcha is confirmed."`

> If the call says *"Samajh nahi aaya, kripya phir se boliye"*, say "Haan, theek hai" again after the beep. Keep
> it in the video: it shows the app won't confirm on a reply it isn't sure about.

### 1:45–1:55 · Both sides at once
**SCREEN:** split, or cut quickly: the workshop page switched to **Approved** by itself (stamp + chime), and the SMS
arriving on the phone with the parcha number, ₹650 and a `/verify/` link.
**SAY:**
> "The moment the customer says yes, the mechanic's screen shows it's approved, and the customer gets an SMS with
> the record. Only a clear yes counts. A 'hmm' or a half-answer never confirms anything."

### 1:55–2:15 · The sealed parcha
**ACTION:** click **Open the verified record** (`/verify/…`), then **Download sealed PDF** and show it.
**SAY:**
> "Mechanic and customer now hold the same parcha: a sealed PDF with the transcripts and SHA-256 hashes inside it,
> a public verification page, and a WhatsApp-ready summary. If anyone edits the record, the hash stops matching."

**CAPTION:** `Sealed PDF · audit hashes · public verify page`

### 2:15–2:30 · Close
**SCREEN:** end card: live URL, GitHub link, "Gnani Prisma + Timbre · Twilio".
**SAY:**
> "Gnani Prisma for Hinglish speech-to-text, Gnani Timbre for the read-back, and a real Twilio call. Money is kept
> in paise, and nothing is final until the customer says yes in their own voice.
> **Kaam ka Parcha: mechanic bolta hai, customer phone par haan bolta hai, aur dono ke paas ek hi parcha.**
> Thank you, Gnani."

**END CARD fine print:** `Synthetic names and numbers · Twilio trial account · WhatsApp = copy to clipboard · #GnaniAI #GreatIndianAIInternshipChallenge`

---

## 4. Optional beat: correct a price on the call (only if the dry run works)

Insert between 1:35 and 1:45, so you say the correction **instead of** the first yes. It adds about 30 s.

**At the first beep, say:**
> "**Nahi, brake pad saade teen sau bola tha.**"

The reply must contain **"nahi"** (that's what marks it as a correction) and name the item.

**If it works**, the call says *"Theek hai, badal diya. Naya parcha suniye."* and reads the new estimate
(brake pad ₹350, **total ₹550**). The workshop page updates its total while the call is still going. At the next
beep say "**Haan, theek hai.**"
**SAY afterwards:**
> "As the customer I changed one price by voice. Only that line changed; labour and the delivery day stayed the
> same, and the old total can't be approved any more."
**CAPTION:** `One price corrected by voice: ₹650 → ₹550. Everything else kept.`

**If the call asks** *"Kaunsa item badalna hai? Kripya naam leke boliye"*, it didn't match the item name in what
it heard. This happens when the slip's label and Prisma's spelling differ. Drop this beat from the final take and
use the plain yes path. Don't try to rescue it live: after a correction attempt only one more unclear reply is
allowed before the call moves to the written fallback.

---

## 5. If something goes wrong

| Symptom | Cause | Fix |
|---|---|---|
| No call button | The card still has flagged amounts, or you're on `/stage` | Settle the flags; use `/workshop`. |
| Button shows an error | Twilio settings missing or trial expired; or the server restarted | Check the Twilio console; reload `/workshop` and start a new estimate. |
| Phone never rings | Number not verified in Twilio, or trial credit is used up | Twilio console → Verified Caller IDs / balance. |
| Call ends after about 13 s | No real key tap during the trial message | Tap a digit on the **on-screen keypad**. |
| *"Maaf kijiye, is waqt estimate nahi sunaya ja saka"* | The read-back couldn't be built (Gnani credits or keys) | Check the Gnani balance; start a new estimate. |
| *"…link bhejenge jahan aap likh kar confirm kar sakte hain"* | Two unclear replies, or very low confidence | Start a new estimate and reply clearly in a quiet room. |
| Workshop page doesn't switch to Approved | The page stopped following the call after 5 minutes | Press F5: the session id is in the URL. |
| Twilio fails completely | — | Record the same flow on `/stage` and caption it **"browser simulation of the phone line"**. Never present the simulation as a real call. |

---

## 6. Editing checklist

- Cut dead air and the trial message; **never** fake a result or splice in a confirmation that didn't happen.
- English captions for every Hindi or Hinglish line, one short line at a time.
- Blur your phone number anywhere it shows (call screen, SMS app header).
- Final length: **2:00–3:00**. Export at 1080p and upload to YouTube as **Unlisted**. That link goes in form field 6.
- Re-check any number you say aloud against `docs/gates.md`.
