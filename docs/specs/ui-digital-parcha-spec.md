# UI Redesign: "Digital Parcha" Specification

> Written with the `to-spec` skill (mattpocock/skills) on 2026-10-05. It synthesises the session's research and makes no new interview. Sources:
> - [R10 Sarvam and Indic hackathon winners](../research/R10-ui-sarvam-indic-hackathon-winners.md)
> - [R11 CampusEvac and Beacon repos](../research/R11-ui-campus-beacon-repos.md)
> - [R12 voice-AI hackathon winners and 60-second demos](../research/R12-ui-voice-ai-hackathon-winners.md)
> - [R13 target audience](../research/R13-ui-target-audience.md)
> - [R14 Indian visual language](../research/R14-ui-indian-visual-language.md)
> - the current templates and browser script
>
> Triage label: `ready-for-agent`. Publication to GitHub Issues is pending because `gh` is not installed on this machine (see Further Notes). AIDLC effort [`010`](../../aidlc-docs/efforts/010-ui-digital-parcha-plan/effort-state.md). **Runs after the money-path plan** ([`2026-10-05-money-path-safety.md`](../superpowers/plans/2026-10-05-money-path-safety.md), effort 009); see "Dependency on the money-path plan" below. Vocabulary follows [`CONTEXT.md`](../../CONTEXT.md) and `AGENTS.md`; state names are the code's (`draft`, `review`, `awaiting_reply`, `fallback_ready`, `confirmed`). Implementation plan: [`2026-10-05-ui-digital-parcha.md`](../superpowers/plans/2026-10-05-ui-digital-parcha.md).

## Testing seams

1. **Browser seam (new, the highest available).** Playwright drives the real `/workshop`, `/customer/{id}`, `/verify/{id}` and `/stage` pages. They run against an in-process server built from the existing offline fakes (scripted Prisma transcripts, fake extractor, silent Timbre) with Chromium's fake microphone. One fixture owns the seam. No credits are spent.
2. **HTTP seam (existing).** The FastAPI `TestClient` asserts on rendered HTML strings and JSON payloads. This is the same approach as today's page and verify tests.

The owner has not yet confirmed these seams; they asked for no check-ins this session. The confirmation is recorded as an open item.

## Problem Statement

**The mechanic** stands in a ~80–90 dB bay with greasy fingers and a budget 360 px-wide Android phone. They most likely studied to middle school and read Hindi more comfortably than English (R13 §1). The workshop page they open:
- is a dark developer dashboard in English;
- puts a small red "Stop" button away from "Record";
- shows a table with an `ID` column (`part-1`) and a `Kind` column;
- lists problems as raw paths such as "Needs review: items.part-1.amount_paise";
- prints amounts without Indian digit grouping.

After pressing "Read estimate to customer" the mechanic is left with a bare link. The page never tells them when the customer said "haan". Nothing shows what the system *heard*, so a mechanic can't tell a mishearing from a typo.

**The vehicle owner** opens a link from WhatsApp and gets:
- a yellow wall of English disclosure text;
- a native audio bar;
- a pre-ticked legal paragraph citing two Acts;
- a button labelled "Record Reply (Say 'हाँ' or correct amount)";
- a table of badges.

Nothing looks like the WhatsApp, UPI-receipt or bill-book screens they already trust (R14 §1). When they correct an amount, the old value silently disappears. The "Estimate Confirmed" state is a plain green box. "WhatsApp Text" downloads a `.txt` file, although the README promises a one-tap copy.

**The verification page** shows "✓ Verified Electronic Record" even when the session is not confirmed. Its "consent not logged" badge uses an undefined colour.

**For the contest:**
- Judges of the 60-second "Demo Day Drop" and LinkedIn/X "Crowd Favourite" awards decide in the first seconds of a muted, phone-sized video (R12 §3).
- The current screens look like every generic hackathon dashboard. Several Indic winners won *despite* that look (R10, anti-patterns), so a UI that resembles its users is an open differentiator.

The read-back endpoint also returns invalid JSON (`Infinity`) whenever no telephony noise is mixed in. The browser then shows "Error starting read-back".

## Solution

The screens become a **digital parcha**: the same bill-book slip mechanics already write (white original, pink duplicate, red serial number, ruled rows, rubber stamp). It is framed by the call, WhatsApp and UPI-receipt patterns vehicle owners trust. Hindi comes first, in Devanagari, with a smaller English line under every label. Amounts are large, use Latin digits and are grouped the Indian way (₹1,23,456).

**Workshop page.** One very large yellow mic button sits in the thumb zone. It turns into an equally large stop button with pulse rings, a live voice-level meter and a "सुन रहा हूँ 0:07" timer. A five-step tracker shows where the job is: बोलो → पर्चा → सुनाओ → हाँ → मंज़ूर.

The parcha slip shows:
- each line with an icon, a part/labour label and the exact words heard (“saade chaar sau”);
- a big total, and "गाड़ी कब मिलेगी" with the promised day.

A field that needs review is highlighted **on its own row**, with a plain question ("फ्रंट ब्रेक पैड का दाम?") and a "दोबारा बोलें" mic chip. Once the card is complete, the dock offers "ग्राहक को सुनाएँ". After that, a share sheet offers to copy the customer link or open WhatsApp with a prefilled Hindi message; both disclose that sending is the mechanic's own action. While the owner decides, the page waits. When the owner says "haan", a violet मंज़ूर stamp lands on the mechanic's slip with a chime and a vibration (the "soundbox" moment, R13 req. 3, R14 §3).

**Customer page.** It opens as a call from the workshop: avatar, "गैराज से कॉल", a ringing/talking status, a large play button and a running caption of exactly what Timbre says. The white-original slip sits below it.

Consent is one Hindi sentence with an explicit tick box; the full legal text sits behind "पूरा नोटिस".

A sticky bottom dock holds one big mic labelled "बोलकर जवाब दें". It sits under two hint chips showing what to say: green “हाँ, ठीक है” and amber “नहीं, ब्रेक पैड 500 था”. The chips are hints, not buttons, because a tap is never voice consent.

- **After a correction:** the old amount appears struck through next to the new one, the row flashes, and a fresh call is ready.
- **Sealed:** the result is a UPI-receipt-style screen with:
  - a green tick, the big total, "पर्चा मंज़ूर हुआ · Estimate confirmed";
  - the owner's own words ("आपने कहा: “हाँ ठीक है”"), the time and the parcha number;
  - a violet stamp on the slip;
  - three actions: download PDF, copy WhatsApp text, and "असली है? जाँचें" (verify).
- **When voice fails:** the existing digital fallback appears as two big buttons.

**Verify page.** Modelled on a DigiLocker/Aadhaar-QR result:
- a large verdict that depends on the real state ("✓ असली पर्चा · Verified" only when confirmed);
- the sealed slip;
- the mechanic's and the owner's recordings as WhatsApp-style voice-note bubbles with transcripts;
- hashes and consent details folded under "तकनीकी सबूत".

**Stage view.** A new page creates a session and shows the mechanic's and owner's pages side by side in two phone frames, for the 60-second film and live judging.

## User Stories

### Mechanic: recording the estimate
1. As a mechanic, I want one mic button large enough to hit with a greasy thumb without looking, so that I can start dictating while holding a part.
2. As a mechanic, I want the mic button at the bottom of the screen in thumb reach, so that I can use the phone one-handed.
3. As a mechanic, I want the stop control to appear exactly where the mic button was, so that I don't hunt for a small separate button.
4. As a mechanic, I want a pulsing ring and a live level meter while recording, so that I can see my voice is being picked up over the engine noise.
5. As a mechanic, I want a running timer ("सुन रहा हूँ 0:07"), so that I know the phone is still listening.
6. As a mechanic, I want a clear "समझ रहे हैं…" processing state after I stop, so that I don't tap again and send a duplicate.
7. As a mechanic, I want Hindi instructions in Devanagari with a small English line, so that I can read them faster than English-only text.
8. As a mechanic, I want to be told in Hindi how to allow the microphone when the browser blocks it, so that I'm not stuck on a silent failure.
9. As a mechanic, I want a friendly Hindi error with a "फिर से बोलें" action when speech processing fails, so that I can retry instead of reading an HTTP error.
10. As a mechanic, I want to see the words the system heard ("आपने कहा: …") above the slip, so that I can tell whether a wrong line is a mishearing.

### Mechanic: reviewing the parcha
11. As a mechanic, I want the estimate shown as a parcha slip like my bill book (serial number, date, ruled rows), so that it feels like my own paperwork.
12. As a mechanic, I want each line to show a part or labour icon and a Hindi kind label (पार्ट / लेबर), so that I can scan it without reading English.
13. As a mechanic, I want each amount in large digits with Indian grouping, so that ₹1,250 never reads as ₹12,50.
14. As a mechanic, I want the exact words behind each line in small italic (“saade chaar sau”), so that I can trust the amount came from what I said.
15. As a mechanic, I want the total as the largest number on the slip, so that I can quote it at a glance.
16. As a mechanic, I want "गाड़ी कब मिलेगी" shown as a weekday, date and part of day in Hindi, so that I can confirm the promise I made.
17. As a mechanic, I want a field that needs checking highlighted on its own row with a plain question ("फ्रंट ब्रेक पैड का दाम?"), so that I know exactly what to say again.
18. As a mechanic, I want a "दोबारा बोलें" mic chip on the flagged row, so that I can correct that one field without re-dictating everything.
19. As a mechanic, I want a counter of how many fields still need checking, so that I know when the parcha is ready.
20. As a mechanic, I want a missing amount shown as "₹ —" and the total as "अधूरा", so that an incomplete parcha is never mistaken for a final one.
21. As a mechanic, I want the read-to-customer action to stay unavailable until nothing needs checking, so that an incomplete estimate never reaches the customer.
22. As a mechanic, I want my other lines and their evidence untouched after a correction, so that fixing one field never breaks another.

### Mechanic: sending and waiting
23. As a mechanic, I want one big "ग्राहक को सुनाएँ" button once the parcha is complete, so that the next step is obvious.
24. As a mechanic, I want a share sheet that copies the customer link, so that I can paste it into WhatsApp myself.
25. As a mechanic, I want an "open WhatsApp" option with a prefilled Hindi message giving the total and the link, so that sending takes one more tap.
26. As a mechanic, I want a notice that nothing is sent automatically, so that I know the message only goes when I send it.
27. As a mechanic, I want the step tracker to show "ग्राहक का जवाब बाकी" while the customer decides, so that I know the parcha is with them.
28. As a mechanic, I want my phone to show a violet मंज़ूर stamp, play a chime and vibrate when the customer says "haan", so that I can hand over the vehicle without checking anything else.
29. As a mechanic, I want my page to show when the customer asked for changes, so that I can call them or correct the parcha.
30. As a mechanic, I want to reopen the page from its link and resume the same parcha, so that a reload doesn't lose my work.

### Vehicle owner: hearing the estimate
31. As a vehicle owner, I want the page to open like a call from the workshop, so that I understand someone is reading me an estimate.
32. As a vehicle owner, I want one large play button labelled "सुनें", so that I can start the read-back without finding a tiny audio bar.
33. As a vehicle owner, I want a running caption of exactly what the voice says, so that I can follow it in a noisy street or with the sound off.
34. As a vehicle owner, I want an honest notice in Hindi and English that this is a simulated phone line with demo data, so that I'm not misled about a real call.
35. As a vehicle owner, I want the page to wait and update by itself if the workshop hasn't finished the read-back, so that I don't have to keep reloading.
36. As a vehicle owner, I want to read the slip even if the audio fails to play, so that I can still respond.

### Vehicle owner: consent and answering
37. As a vehicle owner, I want consent explained in one Hindi sentence with the full notice one tap away, so that I understand what I agree to without a legal wall.
38. As a vehicle owner, I want to tick consent myself (never pre-ticked), so that my agreement is real.
39. As a vehicle owner, I want the reply mic to stay off until I have given consent, so that nothing is recorded without it.
40. As a vehicle owner, I want one big mic with two hint chips showing what to say, so that I know "हाँ, ठीक है" seals the parcha and "नहीं, …" changes it.
41. As a vehicle owner, I want the same large pulse, meter and timer as the mechanic while I speak, so that I can see I'm being heard.
42. As a vehicle owner, I want to be told kindly in Hindi when my answer wasn't understood, so that I can try again.
43. As a vehicle owner, I want a precise question when my correction was ambiguous, so that I name the right item.
44. As a vehicle owner, I want the corrected amount shown next to the old one struck through, so that I can see my correction took effect.
45. As a vehicle owner, I want a fresh read-back ready after a correction, so that I confirm the new total, not the old one.
46. As a vehicle owner, I want two big buttons ("मंज़ूर करें" / "बदलाव चाहिए") when the line is too bad for voice, so that a poor network never blocks me.
47. As a vehicle owner, I want a clear Hindi message when the workshop changed the parcha while I was replying, with a reload action, so that I never confirm a stale estimate.

### Vehicle owner: the sealed parcha
48. As a vehicle owner, I want a UPI-success-style screen (big tick, big total, time, parcha number), so that the confirmation feels as final as a payment.
49. As a vehicle owner, I want to see my own words quoted ("आपने कहा: “हाँ ठीक है”"), so that I know what was recorded as my approval.
50. As a vehicle owner, I want a violet "मंज़ूर" rubber stamp on the slip, so that it looks like an approved paper parcha.
51. As a vehicle owner, I want to download the sealed PDF with one tap, so that I keep proof.
52. As a vehicle owner, I want to copy the WhatsApp text with one tap and a "कॉपी हुआ" confirmation, so that I can forward it myself.
53. As a vehicle owner, I want an "असली है? जाँचें" link, so that I can check the parcha is genuine.

### Anyone verifying
54. As anyone holding the PDF, I want the verify page to show a big verdict that depends on the real state, so that an unconfirmed parcha never looks verified.
55. As a verifier, I want the recordings shown as voice-note bubbles with play buttons and transcripts, so that I can hear who said what.
56. As a verifier, I want hashes, consent records and the legal basis folded under "तकनीकी सबूत", so that ordinary users see the verdict first and auditors can still see everything.

### Demo, judges and quality
57. As the builder recording the 60-second video, I want a stage view with the mechanic's and owner's phones side by side, so that one screen capture shows the whole loop.
58. As a judge watching muted on a phone, I want the heard words, amounts and stamp large enough to read in a video, so that I understand it without audio.
59. As a judge, I want every Gnani model's role visible in the flow (Prisma heard, Timbre spoke), so that genuine use is obvious.
60. As a user on a 360 px Android phone, I want no sideways scrolling and every control at least 48 px, so that the page is usable with one thumb.
61. As a user in sunlight, I want a light, high-contrast paper theme, so that the screen stays readable outdoors.
62. As a user who prefers reduced motion, I want pulses, stamps and flashes reduced to instant changes, so that the page doesn't strain me.
63. As a user on a slow phone, I want the pages to load without a framework or build step, so that they open quickly on patchy 4G.
64. As a screen-reader user, I want every icon-only control labelled and status changes announced, so that I can follow along.
65. As the owner of the project, I want labels and transcripts rendered strictly as text, so that a hostile extracted label can't inject markup.

## Implementation Decisions

### Visual direction: "Digital Parcha" (R14 Direction A, with R11's state-colour rule and R13's sizes)
- **Palette.** Contrast figures are against paper as computed in R14.

  | Token | Hex | Use |
  |---|---|---|
  | counter | `#F3EEE3` | page background |
  | paper | `#FFFDF6` | slip / card |
  | paper-pink | `#FCE4EC` | mechanic's duplicate-copy tint |
  | paper-yellow | `#FFF3C4` | flagged row |
  | ink | `#1B2433` | body text, 15.3:1 |
  | ink-muted | `#5B6472` | secondary text, 5.9:1 |
  | neela | `#1F3A8A` | primary action, white on it 10.3:1 |
  | haldi | `#F2B705` | mic fill only, never text |
  | hara | `#0E7A41` | confirmed / "haan" |
  | amber | `#B45309` | "change" (a change is not a rejection) |
  | sindoor | `#B3261E` | errors only |
  | serial | `#C0262D` | serial number |
  | jamuni | `#5B2E91` | violet seal stamp |
  | rule | `#D9CFBC` | ruled lines |
  | wa | `#008069` | WhatsApp text |

- **Colour means state, never decoration** (R11 Beacon). Every state is shown as icon + word + colour, never colour alone.
- **Type:**
  - Mukta (400/600/800) for all UI text and amounts, with tabular figures;
  - Baloo 2 (800) only for the brand and stamp text;
  - system Devanagari fallbacks (Nirmala UI, Noto Sans Devanagari).
  - Body 18 px, line-height 1.6; slip rows 20 px; total 44 px; no letter-spacing on Devanagari; no thin weights.
- **Sizes:**
  - mic button 96 px;
  - primary actions 64 px tall and full width in the dock;
  - every other control at least 48 px, with 8 px gaps;
  - nothing requires swipe or long-press.
- **Layout:** mobile-first, single column, a maximum of 480 px centred on larger screens (the pages are phone pages; the stage view is the desktop experience). Primary actions live in a sticky bottom dock that respects safe-area insets.
- **Motion:**
  - items rise in 80 ms apart;
  - recording pulse rings;
  - the stamp drops from scale 2.4/-24° to 1/-12°;
  - correction rows flash for 1.4 s.

  All of it is disabled under `prefers-reduced-motion`.
- **Theme:** light only. No dark mode (sunlight readability, R13 req. 7).

### Copy rules
- Hindi in Devanagari is primary. A smaller English sub-line sits under every label and button. Use everyday loanwords (पार्ट, लेबर, टोटल is acceptable, but कुल is preferred for the total).
- Digits are always Latin 0–9, with en-IN grouping. Paise appear only when non-zero (₹45.50). An unknown amount is "₹ —".
- The sealed state is called **मंज़ूर** ("approved"), never "पक्का बिल", because it is not a GST invoice (R13 req. 11).
- **Fixed strings.** Exact copy, fixed by this spec:

  | Where | Hindi | English sub-line |
  |---|---|---|
  | Mic idle | बोलिए | Tap to speak |
  | Recording | सुन रहा हूँ | Listening — tap to stop |
  | Processing | समझ रहे हैं… | Understanding… |
  | Heard | आपने कहा | You said |
  | Flag counter | {n} चीज़ जाँचनी है / {n} चीज़ें जाँचनी हैं | {n} to check |
  | Re-ask chip | दोबारा बोलें | Say again |
  | Amount question | {label} का दाम? | Price of {label}? |
  | Label question | यह {kind} क्या है? | Which {kind} is this? |
  | Delivery question | गाड़ी कब मिलेगी? | When will the vehicle be ready? |
  | Total | कुल | Total |
  | Total incomplete | अधूरा | Incomplete |
  | Read-back | ग्राहक को सुनाएँ | Read to customer |
  | Copy link | लिंक कॉपी करें | Copy link |
  | Open WhatsApp | WhatsApp खोलें | Open WhatsApp |
  | Send disclosure | अपने आप कुछ नहीं भेजा जाता — भेजना आपके हाथ में है। | Nothing is sent automatically. |
  | Copied toast | कॉपी हुआ | Copied |
  | Waiting | ग्राहक का जवाब बाकी | Waiting for customer |
  | Workshop sealed | ग्राहक ने मंज़ूर किया | Customer approved |
  | Call title | गैराज से कॉल | Call from workshop |
  | Listen | सुनें | Listen |
  | Consent line | मेरी आवाज़ रिकॉर्ड होकर इस पर्चे के सबूत के तौर पर रखी जाए — मैं सहमत हूँ। | I agree my voice is recorded as proof for this parcha. |
  | Full notice | पूरा नोटिस | Full notice (DPDP Act 2023) |
  | Customer mic | बोलकर जवाब दें | Speak your answer |
  | Hint chips | “हाँ, ठीक है” / “नहीं, ब्रेक पैड 500 था” | Say yes / or say what to change |
  | Fallback | मंज़ूर करें / बदलाव चाहिए | Approve / Request changes |
  | Sealed | पर्चा मंज़ूर हुआ | Estimate confirmed |
  | Own words | आपने कहा | You said |
  | Verify link | असली है? जाँचें | Verify |
  | Stamp | मंज़ूर | APPROVED |
  | Mic blocked | माइक की इजाज़त दें — ऊपर ताले 🔒 पर टैप करके "Allow" चुनें। | Allow the microphone in your browser. |
  | Stale | पर्चा बदल गया है — पेज ताज़ा करें। | The parcha changed — reload. |

- **Kept verbatim.** The existing English simulation disclosure sentence stays word for word, preceded by its Hindi translation ("यह नकली फ़ोन लाइन है — कोई कॉल नहीं हुई। सभी नाम और रकम डेमो के हैं।"). The page titles stay "Kaam ka Parcha — Workshop Estimate" and "Kaam ka Parcha — Customer Estimate Review". The "Synthetic demo data" badge stays.

### Modules
- **Shared stylesheet.** One static stylesheet holds every token and component: slip, rows, dock, mic, stepper, call card, chips, toast, receipt, stamp, voice note. It replaces the three duplicated inline style blocks.
- **Base template.** Every page extends it. It sets `lang="hi"`, the viewport, font preconnects, the stylesheet and the scripts.
- **Presentation module (server).** Pure functions, registered as template filters and used by the session payload:
  - Indian-grouped rupees from integer paise; booleans and non-integers are rejected;
  - Hindi delivery text;
  - Hindi kind and status labels;
  - a deterministic six-digit parcha number derived from the session id;
  - the latest log text for a role and mode.
- **UI helper script (browser), exposed as one global object.** Pure helpers:
  - the same rupee formatting via `Intl.NumberFormat('en-IN')`;
  - field-path-to-question text;
  - stage derivation;
  - item diffing;
  - a safe element builder that only ever sets text.

  Components:
  - a slip renderer shared by the workshop and customer pages;
  - a mic controller (start/stop, timer, Web Audio level meter, state attribute);
  - a toast;
  - clipboard copy with a legacy fallback for insecure LAN origins.
- **Page flow script.** It keeps today's endpoint calls, revision handling and window exports, and re-renders through the helpers. It also:
  - polls the session every 3 s while waiting (the workshop while `awaiting_reply` or `fallback_ready`; the customer while no read-back exists), stopping on `confirmed` or after 10 minutes;
  - calls the existing consent endpoint when the owner ticks consent;
  - plays the chime with an oscillator, so no audio asset is needed;
  - calls `navigator.vibrate` where supported.
- **Stage page.** A new route creates a session and renders both phone frames (`allow="microphone; autoplay; clipboard-write"`).

### Stage derivation (decision table)

| Session state | Stage | Dock action |
|---|---|---|
| no card | बोलो | mic |
| card with review fields | पर्चा (warning) | mic + per-row re-ask |
| card complete, status `draft` or `review` | सुनाओ | "ग्राहक को सुनाएँ" |
| `awaiting_reply` or `fallback_ready` | हाँ | share sheet + waiting |
| `confirmed` | मंज़ूर | share sealed artefacts |

### API contract changes (additive only)
- The session payload gains:
  - `parcha_no` (six-digit string);
  - `mechanic_transcript` (latest mechanic log text or null);
  - `readback_text` (latest Timbre read-back text or null);
  - `status_label` (Hindi).
- The read-back response is always valid JSON: non-finite numbers in the manifest become null.
- New `GET /stage`: an HTML page that creates a session and embeds `/workshop?session_id=…` and `/customer/{id}`.
- No other route changes. State transitions, revision checks, consent logging, fallback rules and artefact sealing are untouched.

### Dependency on the money-path plan (implemented first)
The money-path plan lands before this redesign. The redesign consumes its contracts unchanged and must not weaken them:
- Intake and amount re-ask return **HTTP 422 with `detail == {"repeat": true, "reason": …}`** when Prisma gives nothing usable. The redesign shows the money plan's Hindi repeat message as a friendly state, with the mic ready again; it is never shown as an error.
- The session payload's **`abstentions`** map (field → reason) is shown **on the flagged row**, under its question, using the money plan's Hindi abstain labels verbatim. That way the mechanic sees *why* an amount is being re-asked ("अधूरी रकम — फिर से पूछेंगे").
- Amounts come only from the numeral grammar. The UI never offers typed or tapped amount entry: re-asking is by voice only, as today.
- Every intake makes two Prisma passes. Browser-test fakes must answer by pass mode, not by call order.
- The money plan's Task 5 restyled `.abstain-reason` and edited the old workshop markup. This redesign replaces that markup, but keeps the class name, the messages and `describeHttpError`'s behaviour.

### Behaviour rules
- Voice is the only sealing path, apart from the existing digital fallback, which appears only in `fallback_ready`. Hint chips never act.
- Consent starts unticked. Ticking it records consent through the existing endpoint (which leaves the revision unchanged). The reply mic stays disabled until consent is recorded. The reply keeps sending its consent flag.
- A correction diff compares the previous and the new card by item id. Changed amounts and labels render old-struck → new, with a flash.
- If the read-back audio fails to load, the caption and slip stay visible, a Hindi notice appears, and the reply mic stays available.
- HTTP 409 on any customer or mechanic action shows the "Stale" copy with a reload button. Other errors show friendly Hindi with the server detail in small text.
- All server-derived text (labels, quotes, transcripts) is inserted only as text nodes.
- The verify verdict is green "✓ असली पर्चा" only for `confirmed`, and amber "अभी मंज़ूर नहीं" otherwise. The undefined danger colour is fixed. The legal, BSA and vehicle strings stay.
- Element ids the tests and the browser suite rely on are preserved:
  - workshop: `record`, `stop`, `message`, `transcript`, `card`, `start-readback`, `customer-link`, `review-section`, `review-count`;
  - customer: `disclosure`, `readback-player`, `customer-record`, `customer-stop`, `customer-status`, `customer-message`, `confirmed-banner`, `fallback-banner`, `fallback-approve`, `fallback-reject`, `download-pdf-link`, `whatsapp-link`, `dpdp-consent-checkbox`, `items-tbody`, `total-cell`, `delivery-info`, `card-status-badge`, `card-revision-badge`;
  - verify: `manifest-digest`, `dpdp-consent-digest`, `dpdp-compliance-panel`.
- **Budget:** our own CSS + JS ≤ 60 KB unminified; two font families; no framework, bundler or Node.

## Testing Decisions

- **Good tests here assert what a person sees or what an API returns:**
  - visible Hindi copy;
  - enabled or disabled controls;
  - a row's text;
  - a status in the payload;
  - no horizontal overflow;
  - a tap target's measured size.

  They never assert CSS class internals or the helper script's private structure (the helper object's public functions are its interface).
- **Unit (HTTP seam / pure):** the presentation module covers grouping, paise, null, the boolean/float rejection, Hindi weekdays and windows, and parcha-number determinism. The session payload's new fields and the read-back's valid JSON go through `TestClient`. Prior art: `tests/test_app.py`, `tests/test_verify.py`.
- **Browser (new seam).** One session-scoped live server with the scripted fakes, Chromium with fake media flags, a 360×800 touch context in `hi-IN`. Flows:
  - workshop record → slip → read-back → share sheet;
  - flagged field → re-ask → complete;
  - mic blocked;
  - hostile label rendered as text;
  - customer consent gating;
  - customer confirm → receipt and stamp on both phones;
  - customer correction → strike-through and fresh read-back;
  - three unclear replies → fallback approve;
  - 409 handling;
  - audio load failure;
  - verify verdicts;
  - stage view;
  - helper functions via `page.evaluate`;
  - responsive audit at 360, 390, 768 and 1440 px (overflow, tap target ≥ 48 px, mic ≥ 88 px, body font ≥ 16 px).

  Prior art: the overflow detector and viewport list in `scripts/run_webattack_suite.py`.
- Browser tests are opt-in (an `e2e` marker deselected by default), need Playwright plus Chromium and FFmpeg, consume zero credits, and save screenshots under ignored `var/`. The default offline suite is unchanged in scope.

## Out of Scope

- Real telephony, real WhatsApp sending, OTP or payments. The call stays a disclosed simulation and sending stays a user action.
- Languages beyond Hindi + English sub-lines (a native-script language picker is a later effort).
- Accounts, a garage profile or shop-name entity, vehicle-number capture, GST invoices.
- Offline/PWA, push notifications, dark mode, native apps.
- Changes to STT, extraction, the money path ([money-path safety spec](money-path-safety-spec.md)), state transitions, consent logging rules or artefact sealing.
- Per-line photos, quantities and rates (R13/R14 ideas recorded for later).
- Re-running the live webattack suite or refreshing README screenshots from live services.

## Further Notes

- **Award fit:** Demo Day Drop (stage view, burned-in captions, stamp moment), Crowd Favourite (a recognisably Indian look), Real Deal (looks like the user's own paperwork). The money-path award decision in effort 008 is unaffected.
- **Unverified research items to check during implementation:**
  - Google Fonts' served Mukta keeping `tnum` (R14); self-host from `google/fonts` if digits don't align;
  - whether Hindi-over-English reads faster than the reverse for this audience (R13 [U]);
  - whether a simulated call from a web page feels like a scam (R13 §7).
- **Publication:** `gh issue create --title "UI redesign: Digital Parcha" --body-file docs/specs/ui-digital-parcha-spec.md --label ready-for-agent`, run once `gh` is installed and signed in as HarshdipSaha.
