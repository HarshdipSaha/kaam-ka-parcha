# 60-second demo: spoken estimate → real phone call → confirmed parcha

Record the deployed [stage view](https://kaam-ka-parcha.onrender.com/stage) and your own physical phone. The owner confirmed the Twilio integration working on 2026-10-26. The browser customer pane is a simulation; show the physical phone when demonstrating the real Twilio channel.

## The cut

- **0–4 s — Problem.** Show a disputed paper bill. Say: “₹450 bola tha… bill ₹900 kaise?” Cut straight to the app.
- **4–14 s — Speak.** Record the mechanic pane: “Front brake pad saade chaar sau, labour do sau, Somvaar shaam tak.” Show the actual extracted items. Caption: “Hinglish → itemised estimate”.
- **14–22 s — Check the money.** Repeat with “Say the whole estimate again”; show ₹450 + ₹200 = ₹650 settling. Say: “Uncertain prices need another recording.”
- **22–34 s — The real phone rings.** Trigger the existing Twilio call endpoint for this session off camera, then film your physical phone ringing and being answered. Keep the workshop pane visible in a split screen. Caption: “Real Twilio call”. Let the actual Timbre read-back be heard briefly.
- **34–45 s — Correct it.** Say into the phone: “Nahi, brake pad saade teen sau bola tha.” Show the real response and updated total, ₹650 → ₹550. Caption: “One price corrected. Other items preserved.”
- **45–54 s — Agree.** Let the revised read-back play, then say “Haan, theek hai” when prompted. Show the workshop becoming approved. Capture the actual transition; do not overlay a fabricated stamp.
- **54–60 s — The result.** Open the confirmed PDF or verification record. Say: “Mechanic bolta hai. Customer phone par confirms. Dono ke paas ek hi parcha.” End card: “Gnani Prisma + Timbre · Twilio calling · WhatsApp = copy” and the live URL.

The correction-and-approval sequence is the centrepiece. If it cannot fit naturally, use the real call with confirmation as the main story and put the correction in a separate longer walkthrough. Do not rush or omit a consent prompt to meet the edit.

## Record it

1. Open the live URL in a full browser window; hide bookmarks and turn off desktop notifications. Record at 1920×1080 with large, readable UI text. Keep captions to one short line.
2. Capture the browser window with Windows Game Bar (`Win + Alt + R`) or your existing recorder. Verify microphone and browser audio with a short test. Use a second camera for the physical phone; its actual speaker audio must be audible. Avoid feedback between the phone and computer.
3. Use the same session throughout. Once its amounts are settled, the existing `POST /sessions/{id}/telephony/call` endpoint takes `expected_revision`, `to_number` and optional `language`; see [deployment instructions](../deploy.md#real-customer-phone-call-twilio-optional). There is no workshop call button yet. Keep the request and credentials off screen.
4. Use only your own or an explicitly consented recipient's number and voice. Mask the phone number, caller ID, SMS details and notifications. Keep provider keys, the dashboard and `.env` out of every shot.
5. If your Twilio account is a trial, retain or label its announcement. Complete any requested keypad step on the phone. Never present the browser simulation as the real call.
6. Record the complete genuine flow first, then trim pauses. Mark accelerated waits. Actual calls and speech runs consume credits; rehearse controls without paid calls before recording a bounded number of real takes.

Public caption: “A mechanic speaks Hinglish. The customer gets a real phone call, corrects the price, and confirms the same parcha. Built with Gnani Prisma, Timbre and Twilio.” Include `#GnaniAI #GreatIndianAIInternshipChallenge`. Describe WhatsApp as clipboard copy; SMS is a separate Twilio channel.

## Evidence boundary

The live-site Playwright smoke on 2026-10-26 verified HTTP 200, both panes, updated UI, shared language switching, desktop/mobile overflow checks and no JavaScript page errors. It placed no paid calls and did not test speech recognition. Real Twilio operation is owner-confirmed; the final recorded call supplies the visible demonstration evidence.
