# Closed-Loop Voice Sealing & Telephony Robustness Specification

## Problem Statement

Independent automotive workshops in India operate primarily on verbal price estimates communicated at vehicle drop-off. Mechanics working with grease, lubricants, and tools cannot interact with physical keyboards or touchscreen forms while diagnosing vehicles in 75–85 dB SPL ambient bay noise. Customers who leave their vehicles often receive verbal phone updates. 

At vehicle pick-up, verbal quotes are frequently disputed (*"Aapne ₹400 bola tha, ₹750 ka bill kaise bana diya?"*), forcing independent workshops to absorb a 5% to 8% loss in gross service margins through uncollected labor and parts discounts.

Furthermore, when verbal estimates are transferred to digital telephony channels (8 kHz narrowband G.711 / AMR-NB), acoustic realities create severe operational friction:
1. **Monosyllabic Dropout**: Brief one-syllable confirmations (*"Haan"*, *"Nahi"*) are routinely truncated by Voice Activity Detectors (VAD), jitter buffers, or line noise.
2. **Transient Workshop Acoustics**: Non-stationary acoustic spikes (pneumatic wrenches, dropped metal spanners, compressor exhaust) degrade speech recognition beyond stationary engine drone.
3. **Evidentiary Weakness**: Standard printed job cards lack tamper-evident proof connecting the agreed total to the customer's actual voice authorization under the *Bharatiya Sakshya Adhiniyam, 2023* and *Information Technology Act, 2000*.
4. **Channel Dropouts**: In marginal cellular coverage, pure voice-only confirmation loops risk customer abandonment if audio drops.

## Solution

A robust, closed-loop conversational speech pipeline that converts noisy workshop dictation into an immutable, customer-sealed digital service agreement:
1. **Dual-Pass Indic Intake**: Captures spoken Hinglish estimates over workshop noise using Indic Inverse Text Normalization (ITN) for colloquial numerals and domain vocabulary biasing for automotive components.
2. **Acoustic Phrasal Telephony Prompting**: Conducts an 8 kHz narrowband read-back structured to elicit stable 3-word phrasal confirmations (*"Haan, theek hai"*), preventing VAD endpointing truncation.
3. **Confidence-Gated Multi-Channel Fallback**: Automatically provides an interactive secondary digital channel if acoustic recognition confidence falls below threshold on degraded lines.
4. **Cryptographic Proof & Scannable QR Verification**: Embeds audio SHA-256 signatures, verbatim timestamps, and a dynamic verification QR code on the sealed PDF linking to an audio playback audit endpoint.
5. **Transient Acoustic Benchmarking**: Measures speech recognition accuracy under non-stationary workshop impulse noise and engine idle hallucination boundaries.
6. **Statutory Consent Integration**: Implements explicit consent logging fulfilling the *Digital Personal Data Protection Act, 2023* requirements for voice data processing.

## User Stories

1. As a workshop mechanic with greased hands, I want to dictate repair items, labor charges, and delivery times in natural Hinglish over running engines, so that I never have to wash my hands to type on a screen.
2. As a workshop mechanic, I want specialized automotive part names (such as caliper pin, clutch plate, and shocker) to be accurately captured in verbatim dictation, so that the generated job card does not substitute incorrect mechanical terms.
3. As a workshop mechanic, I want colloquial Hindi numeral expressions (such as *saade chaar sau* and *paune paanch sau*) to automatically normalize into exact rupee amounts (₹450, ₹475), so that line item calculations are mathematically correct without manual correction.
4. As a vehicle owner receiving a repair quote over a phone line, I want the system to read back the itemized total in natural Hindi with clear rupee and date pronunciation, so that I fully understand what I am being charged.
5. As a vehicle owner on a noisy cellular call, I want the system to prompt me with a clear, stable confirmation phrase (*"Haan, theek hai"*), so that my confirmation is reliably understood without premature call termination.
6. As a vehicle owner, I want the ability to dispute or correct a specific single price item by voice (*"Nahi, brake pad saade teen sau bola tha"*), so that only that item is recalculated while preserving the rest of the estimate.
7. As a vehicle owner, I want to receive an explicit privacy notice explaining that my voice affirmation is being recorded for estimate confirmation, so that my personal data rights are respected under the DPDP Act.
8. As a vehicle owner with poor cellular reception, I want the system to seamlessly offer an interactive digital confirmation message if my voice cannot be clearly recognized, so that I can confirm my estimate without getting disconnected.
9. As a vehicle owner picking up my vehicle, I want a tamper-evident digital job card PDF that records the exact price agreed upon, so that the workshop cannot charge me surprise amounts at the billing desk.
10. As a workshop manager, I want every sealed job card to carry a scannable QR code that plays back the customer's exact verbal confirmation audio snippet, so that billing disputes at pickup can be settled in under 30 seconds.
11. As a workshop manager, I want the job card to include SHA-256 cryptographic signatures of both the mechanic intake and customer confirmation audio streams, so that the document is legally admissible under electronic record standards.
12. As a workshop manager, I want an instant one-click WhatsApp summary formatted with itemized lines and verification links, so that I can dispatch it to the customer with zero typing.
13. As a speech engineer evaluating telephony performance, I want an automated laboratory harness that measures Word Error Rate and Entity Exact-Match across G.711 and AMR-NB codecs at varying Signal-to-Noise Ratios (10 dB, 5 dB, 0 dB), so that acoustic degradation boundaries are scientifically documented.
14. As a speech engineer, I want the evaluation harness to measure speech recognition hallucination rates on non-speech engine idling segments, so that background garage noises do not produce phantom line items.
15. As a speech engineer, I want the evaluation harness to test transient impulse noise spikes (pneumatic wrenches, dropped metal spanners), so that real workshop acoustics are evaluated beyond stationary white noise.

## Implementation Decisions

### 1. Phrasal Acoustic Prompting Engine
- The text synthesis engine for the customer telephony read-back is configured to generate phrasal prompts rather than binary yes/no questions.
- Read-back prompt pattern: Itemized total, delivery commitment, followed by the explicit confirmation instruction: *"Agar aapko yeh manzoor hai, toh boliye: 'Haan, theek hai'. Koi badlaav chahiye toh rate batayein."*
- Increases acoustic duration and phonemic diversity by greater than 4x compared to monosyllabic responses, ensuring robust telephony ASR endpointing.

### 2. Multi-Channel Fallback Architecture
- The customer review router introduces confidence scoring evaluation on telephony voice replies.
- If the recognition confidence score is below 0.65 or if no speech is detected after two retries, the session exposes a fallback state.
- The fallback state yields an interactive digital confirmation payload with dual options: `[Approve Estimate]` and `[Request Changes]`, providing zero-failure redundancy.

### 3. Evidentiary QR Code & Verification Endpoint
- The PDF artefact generator incorporates a dynamic QR code pointing to an accessible verification route (`/verify/{session_id}`).
- The verification endpoint displays:
  - Session UUID and vehicle registration number.
  - Mechanic intake transcript, timestamp, and audio SHA-256 checksum.
  - Customer telephony confirmation transcript, timestamp, and audio SHA-256 checksum.
  - Audio playback interface allowing auditors and customers to listen to the verified confirmation recordings.
- Conforms to electronic record admissibility requirements under Sections 61–63 of the *Bharatiya Sakshya Adhiniyam, 2023*.

### 4. Domain Vocabulary Biasing Curation
- An expanded domain dictionary of 60+ two-wheeler and four-wheeler automotive mechanical parts and colloquial automotive terms is integrated into the verbatim speech recognition pass.
- Terms include: brake pad, disc plate, spark plug, clutch wire, timing belt, coolant, mobil oil, horn, shocker, battery, fuse, caliper pin, head gasket, engine oil badli, carburetor clean, brake shoe.

### 5. Transient Impulse Noise in Laboratory Suite
- The acoustic laboratory harness is expanded to support transient non-stationary noise injection alongside stationary engine drones.
- Synthesizes intermittent high-frequency impulse spikes representing pneumatic impact wrenches and metal spanner drops.
- Evaluates:
  - Character Error Rate (CER) and Word Error Rate (WER) degradation under impulse noise.
  - Rupee amount exact recovery percentage.
  - Non-speech hallucination frequency on idle engine rumble with zero vocal activity.

### 6. Statutory DPDP Act Consent Logging
- The customer telephony interface incorporates an explicit, transparent statutory consent disclosure prior to initiating voice review.
- Records a cryptographic consent timestamp and audit flag in the session metadata prior to voice processing.

## Testing Decisions

### What Makes a Good Test
- Tests must verify observable external behavior and state transitions, not internal implementation mechanics.
- All unit and laboratory tests must run completely offline without relying on external network dependencies or consuming live API credits.
- Audio degradation, acoustic mixing, and cryptographic hashing must be verified against deterministic fixtures.

### Tested Modules
- **Acoustic Prompt Normalizer**: Verifies that generated telephony prompts consistently enforce phrasal confirmation phrasing across varying line item counts.
- **Confidence-Gated Fallback Router**: Verifies state transitions when voice confidence drops below 0.65, ensuring fallback payloads are correctly structured.
- **Verification Endpoint & PDF QR Generator**: Verifies that generated PDFs contain valid QR code streams and that `/verify/{session_id}` accurately resolves audio hashes and session data.
- **Domain Bias Registry**: Asserts that verbatim recognition configurations include all curated automotive mechanical entities.
- **Transient Acoustic Evaluator**: Validates impulse noise mixing and hallucination scoring calculations.

### Prior Art
- Existing test suites in `tests/test_extract.py`, `tests/test_audio.py`, `tests/test_session.py`, `tests/test_artefact.py`, and `tests/test_lab_report.py`.

## Out of Scope

- Real PSTN telecom carrier trunking (Twilio, Exotel) — simulated 8 kHz G.711 / AMR-NB audio filtering remains the primary telephony environment.
- Live automated WhatsApp Business API cloud dispatch (interactive payload is generated and exportable, but live Meta Cloud API integration is not in critical path).
- Hardware-level microcontroller integration inside garage tools.

## Further Notes

- All changes maintain strict adherence to zero-leak comparative benchmark policies (only internal relative deltas are reported).
- The state machine maintains strict immutability once transitioning to `SEALED`.
