# 05: DPDP Act 2023 Statutory Consent & Audit Logging

**What to build:** Incorporate explicit statutory privacy notices and verbal consent verification into the customer telephony interface, logging cryptographic consent timestamps and compliance flags in session metadata prior to capturing voice data as a biometric record, fulfilling Data Fiduciary obligations under the *Digital Personal Data Protection Act, 2023*.

**Blocked by:** 04: Scannable Verification QR Code & Audio Replay Endpoint.

**Status:** ready-for-agent

- [ ] Add statutory consent disclosure modal / banner to customer telephony interface before audio recording is activated.
- [ ] Add explicit verbal consent statement to telephony read-back audio stream.
- [ ] Record consent acceptance timestamp, user agent, and cryptographic verification flag in session metadata and embedded `transcripts.json`.
- [ ] Add offline unit tests asserting consent logging across the customer review lifecycle.
