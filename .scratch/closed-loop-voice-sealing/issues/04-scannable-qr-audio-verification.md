# 04: Scannable Verification QR Code & Audio Replay Endpoint

**What to build:** Implement a public verification interface (`/verify/{session_id}`) and embed a scannable dynamic QR code directly on the sealed PDF linking to it. The verification route displays cryptographic SHA-256 audio signatures, exact timestamps, and an integrated audio player allowing instant playback of the 5-second mechanic intake and customer confirmation recordings, satisfying electronic record standards under Sections 61–63 of the *Bharatiya Sakshya Adhiniyam, 2023*.

**Blocked by:** 03: Confidence-Gated Multi-Channel Digital Fallback.

**Status:** ready-for-agent

- [ ] Implement `GET /verify/{session_id}` route rendering verification metadata and streaming playback for intake and confirmation audio clips.
- [ ] Integrate dynamic QR code generation into ReportLab PDF rendering pipeline pointing to verification URL.
- [ ] Render cryptographic audio SHA-256 signatures and timestamps clearly in both the verification web interface and PDF header.
- [ ] Add offline unit tests asserting QR code generation in PDF streams and verification endpoint JSON/HTML responses.
