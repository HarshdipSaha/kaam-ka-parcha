# Kaam Ka Parcha (काम का पर्चा) — 60-Second Demo Storyboard & Run Sheet

> **"A job card your mechanic speaks over engine noise, and your customer confirms by phone in Hinglish, with the rupees right."**

This document details the exact 60-second video demo storyboard, live rehearsal script, two-browser operational run sheet, technical transitions, and fallback checklist for Kaam Ka Parcha.

---

## 1. 60-Second Video Storyboard & Script

### Target Timing & Narrative Arc

| Timestamp | Segment | Visual Scene | Spoken Audio / Dialogue | On-Screen Action & System State |
|---|---|---|---|---|
| **00:00 – 00:03** | **The Hook** | Split-screen: Loud two-wheeler garage on left (running engine, tools clinking); customer on right holding mobile phone. | **Voiceover:** *"Mechanic speaks in a noisy garage. Customer gets a crystal-clear estimate over the phone."* | High-contrast title card: **काम का पर्चा (Kaam Ka Parcha)**. Audio introduces engine roar (78 dB SPL). |
| **00:03 – 00:08** | **The Problem** | Mechanic hands covered in black grease. Customer at vehicle pickup looking at a handwritten slip arguing. | **Voiceover:** *"India's repair shops run on verbal deals. Estimates get lost and bills get disputed."* | Quick cut to disputed slip with scribbles. Text overlay: *"₹400 bola tha, ₹750 ka bill kaise bana?"* |
| **00:08 – 00:15** | **Workshop Capture (Leg 1)** | Mechanic taps large mic button on `/workshop` tablet screen. Idling scooter revving right behind him. | **Mechanic (Hinglish):** *"Bhaiya, front brake pad badla, part saade chaar sau, labour do sau, Somvaar shaam tak gaadi mil jayegi."* | Live waveform pulses. Prisma STT dual-pass runs (`format=transcribe` + `bias_list`). Job card dynamically populates: **Front brake pad (₹450)**, **Labour (₹200)**, **Total: ₹650**, Delivery: **Monday 6:00 PM**. State: `DRAFT` $\to$ `READ_BACK_READY`. |
| **00:15 – 00:35** | **Customer Leg & Telephony Simulation (Leg 2)** | Customer receives interactive telephony screen on mobile `/customer/{session_id}`. Call UI displays incoming estimate with degraded 8 kHz speakerphone audio. | **Timbre TTS (8 kHz $\mu$-law through G.711 + 5 dB noise):** *"Aapki gaadi ka kul chhe sau pachaas rupaye hua, Somvaar shaam tak milegi. Agar theek hai toh kahiye 'Haan, theek hai'."* | On-screen disclosure banner prominently visible: *"Simulated Telephony Line: G.711 $\mu$-law 8 kHz + 5 dB street noise. No PSTN call placed."* Customer hears authentic narrowband telephone audio. |
| **00:35 – 00:45** | **Targeted Voice Correction & Sealing** | Customer taps mic to contest one item. | **Customer (Hinglish):** *"Nahi, brake pad saade teen sau bola tha."*<br>**System:** Recalculates total $\to$ ₹550.<br>**Timbre:** *"Naya kul paanch sau pachaas rupaye. Theek hai?"*<br>**Customer:** *"Haan, theek hai."* | Extractor runs targeted delta update on `brake_pad` item only (₹450 $\to$ ₹350). Other items and promised date remain untouched. Total updates from ₹650 to ₹550. On affirmative confirmation, state shifts: `CUSTOMER_REVIEW` $\to$ `SEALED`. Lock animation clicks shut. |
| **00:45 – 00:53** | **Sealed Artefacts** | Customer screen reveals confirmed Parcha card with green verification shield and instant export buttons. | **Voiceover:** *"A tamper-evident record in seconds. Immutable, timestamped, and auditable."* | Customer clicks **Download PDF**: PDF opens with itemized breakdown, Hindi read-back transcript, customer confirmation audio SHA-256 hash, and embedded `transcripts.json` audit trail. Mechanic clicks **Copy WhatsApp**: Formatted summary copied to clipboard with one click. |
| **00:53 – 01:00** | **Line Noise Lab & Close** | Line Noise Lab setup showing evaluation conditions for codecs (G.711, AMR-NB), noise, and packet loss. | **Voiceover:** *"Line Noise Lab is ready for evaluation. Voice-sealed repairs with Kaam Ka Parcha."* | Proof Card displays evaluation settings and pending measurements. End card with Gnani AI badge & hashtags: `#GreatIndianAIHackathon #NoiseCanceller`. |

---

## 2. Shot-by-Shot Director Cue Sheet

| Shot # | Duration | Angle / View | Visual Framing | Audio Track | Subtitles / Captions (English) |
|---|---|---|---|---|---|
| **S01** | 3.0s | Dynamic Split Screen | 50% left: Workshop bay with two-wheeler. 50% right: Customer standing by roadside. | Workshop engine rumble + subtle phone ring. | *Two people. One verbal deal. Zero misunderstandings.* |
| **S02** | 5.0s | Macro Close-up | Greasy hands holding spanner, gesturing at engine. Cut to receipt slip with crossed-out numbers. | Ambient garage clatter (wrenches, compressor). | *Verbal garage estimates lead to daily bill disputes at vehicle pick-up.* |
| **S03** | 7.0s | Screen Capture + Picture-in-Picture | Browser window at `http://localhost:8000/workshop`. Mechanic taps "Record Estimate". | Live voice: *"front brake pad badla, part saade chaar sau..."* | *"Front brake pad changed, part ₹450, labour ₹200, delivery Monday evening."* |
| **S04** | 5.0s | UI Animation Focus | Parsed line items appear in realtime table with confidence badges (High). | Pleasant chime as card transitions to `READ_BACK_READY`. | *Prisma v2.5 dual-pass parses colloquial numbers (saade chaar sau $\to$ ₹450) and automotive parts.* |
| **S05** | 8.0s | Mobile Device Screen | Mobile viewport showing `/customer/{session_id}`. Call active banner with audio visualizer. | 8 kHz band-limited telephony audio with audible 5 dB street background noise. | *Timbre v2.5 reads back total: "Total ₹650, ready Monday evening. Say 'Yes, it's fine' to confirm."* |
| **S06** | 7.0s | On-Screen Legal Badge | Zoom into simulation disclosure header bar. | Telephony hiss + background traffic. | *Simulated phone line: G.711 $\mu$-law 8 kHz + 5 dB noise. Transparent & reproducible.* |
| **S07** | 5.0s | Customer Face / Phone | Customer speaking firmly into smartphone microphone. | Customer voice: *"Nahi, brake pad saade teen sau bola tha."* | *"No, the brake pad was quoted at ₹350."* |
| **S08** | 5.0s | UI Delta Animation | Line item for brake pad flashes yellow, updates to ₹350. Total shifts to ₹550. Read-back re-triggers. | Short Timbre read-back: *"Naya kul paanch sau pachaas rupaye."* Customer: *"Haan theek hai."* | *Targeted delta update preserves untouched items. Customer confirms revised total.* |
| **S09** | 5.0s | Screen Capture | Green padlock locks. Status: `SEALED`. "Download Confirmed PDF" button clicked. | Satisfying latch/lock sound effect. | *Session sealed. Tamper-evident PDF generated with cryptographic audit trail.* |
| **S10** | 3.0s | Document Inspection | Adobe Reader / browser PDF viewer showing PDF with embedded `transcripts.json`. | Paper rustle sound effect. | *Includes audio SHA-256 signatures, exact Hinglish transcripts, and paise totals.* |
| **S11** | 4.0s | UI Action | Mechanic taps "Copy WhatsApp Summary" $\to$ toast notification "Copied to clipboard". | Subtle digital click. | *Instant WhatsApp-formatted summary ready for one-tap dispatch.* |
| **S12** | 3.0s | Technical Card | Line Noise Lab evaluation setup for codec and noise conditions. | Upbeat tech-outro music swell. | *Line Noise Lab: Synthetic telephony evaluation setup.* |

---

## 3. Live Two-Browser Rehearsal Setup

To rehearse or record the live demo on a single workstation without physical hardware:

### A. Screen Layout
- Arrange two browser windows side-by-side on a 1080p or 1440p monitor:
  - **Left Window (50% width)**: Mechanic Workshop Portal (`http://localhost:8000/workshop`)
  - **Right Window (50% width)**: Customer Review Portal (`http://localhost:8000/customer/{session_id}`)

### B. Prerequisites & Server Launch
1. Ensure the Python 3.12 virtual environment is active:
   ```powershell
   cd "H:\augsepthacks\gnani intern"
   .\.venv\Scripts\Activate.ps1
   ```
2. Verify environment configuration:
   ```powershell
   # Verify API keys exist in .env (or test with mock offline mode)
   Get-Content .env
   ```
3. Start the FastAPI application server:
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn parcha.app:app --reload --port 8000
   ```
4. Verify server health in terminal:
   ```powershell
   curl http://localhost:8000/health
   # Returns: {"status":"healthy","version":"0.1.0","app":"Kaam ka Parcha"}
   ```

### C. Step-by-Step Rehearsal Execution

```
[WORKSHOP BROWSER]                          [CUSTOMER BROWSER]
http://localhost:8000/workshop             http://localhost:8000/customer/{id}

1. Mechanic enters vehicle & customer:
   Vehicle: "DL 3S AB 1234"
   Customer Phone: "9876543210" (synthetic)

2. Tap "Record Estimate" (or upload audio):
   Dictate: "front brake pad badla,
   part saade chaar sau, labour do sau,
   Somvaar shaam tak"

3. Click "Transcribe & Parse":
   -> Dual-pass STT extracts items:
      - Front Brake Pad: ₹450
      - Labour: ₹200
      - Total: ₹650
      - Delivery: Monday 6:00 PM
   -> Session created with UUID:
      e.g. "a1b2c3d4-..."
   -> Status: READ_BACK_READY

4. Tap "Notify Customer":
   -> Copies customer URL:
      http://localhost:8000/customer/{id}
                                          5. Open customer URL in right browser:
                                             -> Page loads in simulated telephony mode
                                             -> On-screen disclosure displayed:
                                                "Simulated Telephony Line..."
                                             -> Click "Listen to Estimate"
                                             -> Timbre 8 kHz degraded audio plays:
                                                "Aapki gaadi ka kul chhe sau..."

                                          6. Perform Targeted Voice Correction:
                                             -> Tap "Voice Correction"
                                             -> Speak: "nahi, brake pad saade teen sau"
                                             -> Extractor updates ONLY brake pad (₹350)
                                             -> Total recalculates to ₹550
                                             -> Revised audio read-back plays

                                          7. Confirm & Seal:
                                             -> Tap "Voice Confirm"
                                             -> Speak: "Haan theek hai"
                                             -> Status changes to SEALED
                                             -> Padlock locks, UI turns green

                                          8. Download PDF Artefact:
                                             -> Click "Download Sealed PDF"
                                             -> Validates embedded transcripts.json

9. Refresh / Observe Workshop Screen:
   -> Status automatically syncs to SEALED
   -> Click "Copy WhatsApp Summary"
   -> Paste into WhatsApp Web / Notepad
```

---

## 4. Technical Mechanism Highlights (What to Tell Judges)

When demonstrating or defending the implementation to hackathon evaluators:

1. **Dual-Pass Indic ASR (`PrismaClient.transcribe_dual`)**:
   - Pass 1 runs with `format=transcribe` to activate Gnani's Indic Inverse Text Normalization (ITN), transforming colloquial numbers like *"saade chaar sau"* directly into numeric paise amounts.
   - Pass 2 runs with `format=verbatim` and an automotive vocabulary `bias_list` (weight: `1.0`) ensuring specialized part names ("brake pad", "clutch plate", "carburetor") are never phonetically mangled.

2. **Acoustic Telephony Degradation Chain (`parcha.audio`)**:
   - Timbre v2.5 synthesizes 8 kHz mono $\mu$-law audio.
   - FFmpeg applies standard telephony bandpass filtering ($300\text{ Hz} – 3400\text{ Hz}$), downsamples to 8,000 Hz, injects real garage/street ambient noise at a calibrated $5\text{ dB SNR}$, and simulates carrier compression via G.711 / AMR-NB 4.75 kbps.
   - Customer hears what a real phone call sounds like over Indian 2G/telephony trunks.

3. **Targeted Field Delta Extractor (`parcha.extract`)**:
   - Correction requests do **not** discard the existing job card. The extractor receives both the previous structured card and the correction transcript.
   - Only contested fields are mutated; unaffected repairs, labour charges, and delivery promises retain their original values and timestamps.

4. **Cryptographically Sealed PDF (`parcha.artefact`)**:
   - The sealed job card compiles into a standalone PDF with ReportLab.
   - The PDF embeds a machine-readable `transcripts.json` stream attachment containing timestamps, verbatim transcripts, confidence scores, and SHA-256 hashes of the audio evidence.
   - The document is immutable: any subsequent modification attempt is rejected by the session state machine (`InvalidTransitionError`).

5. **Line Noise Lab Evaluation Harness (`parcha.lab`)**:
   - The evaluation harness supports speech-resilience runs over synthetic manifests, codecs, and noise conditions.
   - The WebSocket streaming telephony probe records short-reply outcomes for a selected zero-padding silence tail.

---

## 5. Rehearsal Checklist & Contingency Fallbacks

| Failure Scenario | Live Symptom | Pre-Tested Fallback Procedure |
|---|---|---|
| **Microphone permission blocked in browser** | Browser refuses audio recording on `/workshop` or `/customer`. | Use the "Upload WAV" file picker on both pages. Point to pre-recorded sample files in `data/` or `var/gates/`. |
| **API rate limit or connection timeout** | Gnani API returns HTTP 429 or 504 during live dictation. | Switch `.env` to fallback test fixture or demonstrate the automated offline test suite with `pytest -q`. |
| **Speaker volume / feedback on single PC** | Feedback loop between mechanic and customer browsers. | Keep customer browser muted during workshop recording; use headphones or standard desktop audio routing. |
| **Voice correction misunderstood** | Background room noise distorts "saade teen sau". | Click "Retry Voice Correction" or use the manual rupee adjustment override on the customer review card. |
| **Judges inquire about carrier PSTN dialing** | Question: "Did you place a real phone call to an Airtel/Jio SIM?" | Point directly to the on-screen disclosure banner. Explain that Kaam Ka Parcha measures real acoustic degradation (G.711/AMR-NB) without fragile carrier aggregator costs, and demonstrate the WebSocket telephony connector designed for SIP PBX trunking. |

---

## 6. Video Production Metadata

- **Resolution**: 1920 × 1080 (16:9), 60 fps.
- **Voiceover Language**: English narration with clear Hinglish audio clips.
- **Subtitles**: Full English closed captions embedded in video track.
- **Target Runtime**: Exactly 59.5 seconds (under the 60-second limit).
- **Compliance Badges**:
  - *"Simulated Telephony Line: G.711 / AMR-NB + 5 dB noise"*
  - *"All names and vehicle numbers are synthetic"*


## Stage view shot list (`/stage`)

Open `http://localhost:8000/stage` at 125% browser zoom. It creates one session and shows the mechanic and owner phones side by side. Shot order: dictation, slip, read-back, "haan", approval stamp on both phones. Screenshots in `docs/ui/` use synthetic data only.
