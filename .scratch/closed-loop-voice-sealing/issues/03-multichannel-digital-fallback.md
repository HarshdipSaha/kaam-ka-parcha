# 03: Confidence-Gated Multi-Channel Digital Fallback

**What to build:** Implement confidence evaluation on customer telephony voice replies. When speech recognition returns a confidence score below 0.65 or voice recognition encounters repeated retries on degraded cellular channels, expose an interactive fallback confirmation payload (`[Approve Estimate]` / `[Request Changes]`) to ensure the estimation agreement completes without customer abandonment.

**Blocked by:** 02: Phrasal Telephony Prompting & VAD Stabilization Engine.

**Status:** ready-for-agent

- [ ] Add confidence threshold evaluation logic to telephony customer reply handler.
- [ ] Implement `POST /sessions/{id}/fallback` endpoint and session state transition for digital confirmation fallback.
- [ ] Render interactive one-tap confirmation controls in customer review interface when fallback condition triggers.
- [ ] Add offline unit tests asserting state transitions and fallback payload integrity under low-confidence mock conditions.
