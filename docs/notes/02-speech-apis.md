# 02 — Gnani Speech APIs: build-ready reference (STT · TTS · Voice Cloning)

Source: `docs/raw/llms-full.txt` lines 7365–13788 (Mintlify export of docs.gnani.ai, "Last verified: 5 August 2026"), plus live `.md` pages fetched 2026-10-04 for fields the export stripped (REST STT param names/defaults, VC embeddings response, OpenAPI blocks). No Gnani API was called; nothing here has been checked against the live service.
Legend: **(inferred)** = my own conclusion, not stated in the docs. **CONFLICT** = the docs contradict themselves; see §7.

---

## 0. Cheat sheet (one screen)

Base URL `https://api.vachana.ai`. Auth on every call is header `X-API-Key-ID: <key>` (the STT WebSocket docs write it lowercase, `x-api-key-id`). Key from https://app.gnani.ai/voice. Missing/bad key → `401`. **`403 FORBIDDEN` = bad key / org status / out of credits.**

| Capability | Endpoint | Transport | Hard limits | Best for |
|---|---|---|---|---|
| STT short clip (Prisma v2.5) | `POST /stt/v3` | multipart/form-data, sync JSON | ≤ **60 s** (ideal ≤30 s); WAV/MP3/OGG/FLAC/AAC/M4A; 8–44.1 kHz in (auto-converted to 16 kHz mono); 10 langs | Push-to-talk, voice notes, ITN demos, code-mixed hi+en via `multi_lang_codes` |
| STT realtime | `wss://api.vachana.ai/stt/v3/stream` | WebSocket: binary PCM in, JSON out | raw PCM s16le mono, **exactly 1024-byte frames** at real-time pace; 8/16/44.1/48 kHz; **15-min session cap**; one language per session; finals only (no partials documented) | Live mic, phone calls, voice agents, live compliance |
| STT batch | `POST /stt/v3/batch/jobs` → `/start` → poll → `/files` → GET `transcript_url` | REST async (+ optional webhook) | ≤ **4 h**/file; upload: 10 MB/file, 100 files/job, ZIP 50 MB (200 MB unzipped); public URL: no byte cap, 30-min download; **diarization max 2 speakers**; **no ITN**; 8 langs (no gu/pa) | Long recordings, call archives, podcasts, two-speaker diarization, noisy audio (`with_denoise`) |
| TTS full file (Timbre v2.5) | `POST /api/v1/tts/inference` | JSON in, binary audio out | `speed` 0.85–1.15; 8k–48k Hz; wav/raw/mp3/ogg/mulaw/alaw | Pre-rendered prompts, downloads |
| TTS streaming | `POST /api/v1/tts/sse` | SSE, base64 chunks | same; OGG arrives as **one** chunk (not streamed) | Progressive playback without WebSockets |
| TTS realtime | `wss://api.vachana.ai/api/v1/tts` | WebSocket: JSON request, JSON+base64 chunks | same; config via headers + JSON body | Lowest-latency agent replies |
| Voice list | (static page, no endpoint) | — | 42 voices, 11 language buckets | Picking voices |
| Clone: embedding | `POST /api/v1/tts/voice-clone/embeddings` | multipart (`audio_file`) | 5–30 s of clean reference audio (WAV/MP3) | One-time per voice; cache it |
| Clone: synth | same 3 TTS endpoints + `speaker_embedding` (`model: vachana-vc-v1`) | REST / SSE / WS | sample_rate 8000–**44100**; containers raw/mp3/wav/mulaw/ogg (**no alaw**); mp3 96k/128k/192k | "Speak in my/parent's/teacher's voice" demos |

Latency claims (Gnani's own figures, none measured by us): "P95 ~200 ms for STT" (intro page); the WS `transcript.latency` example is 320 ms; compliance tutorial: "~300–500 ms from end of speech to transcript"; hackathon page: "Streams in under 200ms". Real end-of-utterance delay ≈ `x-min-silence-ms` (default 500 ms) + `latency` **(inferred)**.
Pricing / credit cost per call: **not documented anywhere in the docs.** Only: Batch "billing is per audio duration"; substitution doesn't change billing. Rate limits: **no numbers**, just `429`.

---

## 1. Languages (all endpoints)

| Language | STT REST | STT WS | STT Batch | TTS `language` | TTS voices |
|---|---|---|---|---|---|
| English (India) | `en-IN` | `en-IN` | `en-IN` | `en-IN` | 6 |
| Hindi | `hi-IN` | `hi-IN` | `hi-IN` | `hi-IN` | 13 |
| Hinglish (code-mixed) | — (use `hi-IN`, or `multi_lang_codes`, see §2.1) | — | — (lang-ID picks one per file) | `hi-en` (**CONFLICT**: the SDK says `auto`) | 1 (Poorvi) |
| Bengali | `bn-IN` | `bn-IN` | `bn-IN` (`bn-BD` only on older pages, **CONFLICT**) | `bn-IN` | 2 |
| Gujarati | `gu-IN` | `gu-IN` | **not supported** | `gu-IN` | 2 |
| Kannada | `kn-IN` | `kn-IN` | `kn-IN` | `kn-IN` | 2 |
| Malayalam | `ml-IN` | `ml-IN` | `ml-IN` | `ml-IN` | 2 |
| Marathi | `mr-IN` | `mr-IN` | `mr-IN` | `mr-IN` | 2 |
| Punjabi | `pa-IN` | `pa-IN` | **not supported** | `pa-IN` | 2 |
| Tamil | `ta-IN` | `ta-IN` | `ta-IN` | `ta-IN` | 5 |
| Telugu | `te-IN` | `te-IN` | `te-IN` | `te-IN` | 5 |
| Auto-detect | — | — | up to 3 comma-separated codes, decided per **file** | `auto` (by script) | — |

- STT output is in native script (e.g. `hi-IN` → Devanagari). The batch sample transcripts mix Devanagari with Latin-script English words ("EMI", "loan account number").
- Word boosting only works on the "v2-model" languages: `hi, en, ta, bn, kn, te, ml, mr` (-IN). It is silently ignored for gu/pa.
- ITN coverage: the REST/WS pages imply every language, but the SDK page and the compliance tutorial say **ITN works for `hi-IN` and `en-IN` only** (**CONFLICT**; treat as hi/en-only).
- The hackathon page claims "Hinglish, Tanglish and Benglish" STT support. The API docs expose no such codes.

---

## 2. Speech-to-Text — Gnani Prisma v2.5

### 2.1 REST `POST https://api.vachana.ai/stt/v3` (≤60 s)
Source: https://docs.gnani.ai/api/STT/speech-to-text

`Content-Type: multipart/form-data`. Fields:

| Field | Type | Req | Default | Notes |
|---|---|---|---|---|
| `audio_file` | file | ✓ | — | WAV, MP3, OGG, FLAC, AAC, M4A. Max 60 s (ideal ≤30 s). Input 8–44.1 kHz, auto-converted to 16 kHz mono |
| `language_code` | enum | ✓ | — | the 10 codes above |
| `format` | enum | | `verbatim` | `verbatim` = spoken form; `transcribe` = ITN on |
| `itn_native_numerals` | bool | | `false` | With `transcribe`: `₹५,०००` instead of `₹5,000` |
| `enable_substitution` | bool | | `false` | Turns on find-and-replace |
| `substitution_map` | JSON string | | — | ≤10 rules `[{"patterns":[...],"replacement":"..."}]`; case-insensitive, Unicode word boundaries, longest match first, single pass. Billing keeps the raw transcript |
| `bias_list` | string | | — | ≤100 single words, letters only (Latin or Indic), as a JSON array or CSV. Use with `format=verbatim` |
| `bias_score` | number | | off | `0.0` `0.5` `1.0` `1.5` `2.0`. Start at 1.0 |
| `multi_lang_codes` | ? | | — | **Mentioned, never specified.** "Multilingual support for English and Hindi together" / "Multiple languages: uses multilingual model (supports en-IN, hi-IN)". The SDK doesn't expose it. Format unknown — verify live |
| `model` | string | | default | Only mentioned in passing: default = `vachana-audio-intelligence-v2` (boosting needs the default model) |

**Invalid `bias_list`/`bias_score` on REST is silently ignored** (still `200`, no boosting).

Response `200`:
```json
{"success": true, "request_id": "req_abc123", "timestamp": "20251226_143052.123", "transcript": "नमस्ते, आप कैसे हैं?"}
```
(The quick start also shows `"model": "gnani-prisma-v2.5"` in the body.)
Errors use the shape `{"success":false,"error":{"type":"INVALID_REQUEST_ERROR","message":"Audio duration exceeds maximum limit of 60 seconds, ..."}}`. Statuses: `400` bad params/format/too long · `403 FORBIDDEN` (key/org/**credits**) · `429 RATE_LIMIT_ERROR` · `500 API_ERROR` (retry with backoff) · `503 SERVICE_UNAVAILABLE`.

```bash
curl --request POST --url https://api.vachana.ai/stt/v3 \
  --header 'X-API-Key-ID: <api-key>' \
  --form audio_file='@recording.wav' --form language_code=hi-IN \
  --form format=transcribe --form itn_native_numerals=true
# boosting:  --form 'bias_list=["Prisma","EMI"]' --form bias_score=1.0   (with format=verbatim)
# subst:     --form enable_substitution=true --form 'substitution_map=[{"patterns":["okay","ok"],"replacement":"acknowledged"}]'
```

**ITN rules** (`format=transcribe`; same on WS):
- Indian digit grouping: दो हज़ार→2,000; पाँच लाख बीस हज़ार→5,20,000; five lakh→5,00,000; ordinals पहला→1st.
- Currency: पाँच सौ रुपये→₹500; तीन रुपये पचास पैसे→₹3.50; "pay do lakh rupees"→₹2,00,000.
- Dates: बीस जनवरी दो हज़ार पच्चीस→20 जनवरी 2025. Times: शाम पाँच बजे→शाम 17:00 (24-hour).
- Phone/PIN: a 10-digit stream→9876543210, 6 digits→PIN, "डबल/double" expanded.
- Code-mixed: "कल थ्री फिफ्टी पीएम को पाँच सौ रुपये transfer करना है"→"कल 15:50 को ₹500 transfer करना है".
- Left alone on purpose: दो तीन ("a few"), कर दो / ले दो.

### 2.2 Realtime WebSocket `wss://api.vachana.ai/stt/v3/stream`
Source: https://docs.gnani.ai/api/STT/stt-websocket

**All config goes in upgrade headers** (values are strings). **Browser `WebSocket` can't set headers → proxy through your backend** (this also keeps the key off the client).

| Header | Req | Default | Values |
|---|---|---|---|
| `x-api-key-id` | ✓ | — | key |
| `lang_code` | ✓ | `en-IN` | one of the 10 codes (one language per session) |
| `x-sample-rate` | | `16000` | `8000`, `16000`, `44100`, `48000` (must match the source; 44.1/48k are resampled server-side) |
| `x-format` | | `verbatim` | `verbatim` / `transcribe` (ITN) |
| `itn_native_numerals` | | `false` | bool |
| `x-enable-substitution` | | `false` | bool. Can change mid-session |
| `x-substitution-map` | | — | JSON rules (≤10). Can change mid-session |
| `x-bias-list` | | — | JSON array/CSV, ≤100 words; Indic as `\uXXXX` escapes (`["नमस्ते"]`). Can change mid-session |
| `x-bias-score` | | off | 0.0/0.5/1.0/1.5/2.0 |
| `x-vad-threshold` | | `0.7` | 0.0–1.0 (clean mic 0.45–0.55; telephony 0.65–0.75) |
| `x-min-silence-ms` | | `500` | 100–2000 (IVR 300–400; telephony 400–600; conversation 600–900). **Biggest latency lever** |
| `x-min-speech-ms` | | `100` (`200` at 8 kHz) | 50–2000 (raise to 200–300 when noisy) |
| `x-min-segment-ms` | | `120` | 100–1000 (raising it too far silently drops "yes"/"no") |
| `x-max-speech-s` | | disabled | 5.0–120.0 (set 20–30 for monologues so text keeps flowing) |

VAD headers are fixed for the whole connection; to change them, reconnect. Undocumented extras mentioned once: an `x-partials` header producing `partial_transcript` messages, and a `/stt/v4/stream` route (same boosting headers, no `update_settings`). The Pipecat page says "today Gnani sends final transcripts only".

**Audio frames:** PCM signed 16-bit LE, mono, **512 samples = exactly 1024 bytes per binary frame**, sent at real-time cadence (32 ms per frame at 16 kHz, 64 ms at 8 kHz; for 44.1/48k the docs still say send 1024-byte frames "at the appropriate cadence" ≈ 11.6 / 10.7 ms **(inferred)**). Never burst: it degrades VAD. No containers mid-stream.

**Protocol:**
1. Connect with headers → server sends `connected` immediately.
2. Client streams binary frames continuously.
3. When VAD sees end of speech → `processing`; shortly after → `transcript` (one per VAD segment).
4. Either side closes. **No end-of-stream message, no flush command and no keepalive/ping are documented.** To get the last utterance out, send ≥`x-min-silence-ms` of zero frames before closing **(inferred)**. Session hard cap: 15 min, so plan reconnects. Close code **4001 = auth failure** (from the compliance tutorial).

Server messages (JSON text, all carry `type` and ISO `timestamp`):
```json
{"type":"connected","message":"STT service ready — VAD service connected","timestamp":"…","config":{"sample_rate":16000,"chunk_size":512}}
{"type":"processing","timestamp":"…"}
{"type":"transcript","timestamp":"…","text":"Hello, how are you today?","audio_duration_ms":2340,"segment_id":"<id>","segment_index":0,"latency":320}
{"type":"error","timestamp":"…","message":"STT engine failed to initialize"}   // may be recoverable; socket can stay open
{"type":"settings_updated","timestamp":"…","config":{"language_code":"en-IN","format":"verbatim","itn_native_numerals":false,"substitution_enabled":true,"bias_word_count":2,"bias_score":1.5}}
```
`latency` = ms from end-of-speech detection to transcript delivery. `transcript` messages carry no word timestamps, confidence or speaker labels.

Client control frame (JSON text frame, mixed in with the binary audio). Fields you leave out keep their values. It applies from the **next** segment, and an invalid update is ignored as a whole:
```json
{"type":"update_settings","substitution":{"enabled":true,"map":[{"patterns":["ok","okay"],"replacement":"acknowledged"}]}}
{"type":"update_settings","bias":{"list":["Vachana","EMI"],"score":1.5}}     // list [] or null = boosting off
```
Only substitution and bias can change mid-session. Language, format and VAD can't.

Presets (copied from the docs):
```text
Telephony 8k:  lang_code hi-IN | x-sample-rate 8000 | x-vad-threshold 0.7 | x-min-speech-ms 200 | x-min-silence-ms 500
IVR:           x-sample-rate 8000 | x-min-silence-ms 300 | x-min-speech-ms 100 | x-min-segment-ms 100
Web mic 48k:   x-sample-rate 48000 | x-vad-threshold 0.5 | x-min-silence-ms 700
Dictation:     x-sample-rate 16000 | x-min-silence-ms 800 | x-max-speech-s 30
```
```python
import websockets
headers = {"x-api-key-id": KEY, "lang_code": "hi-IN", "x-sample-rate": "8000",
           "x-vad-threshold": "0.7", "x-min-speech-ms": "200", "x-min-silence-ms": "500"}
async with websockets.connect("wss://api.vachana.ai/stt/v3/stream",
                              additional_headers=headers) as ws:   # extra_headers on websockets<13
    ...  # task A: await ws.send(frame_1024_bytes); await asyncio.sleep(0.064)
         # task B: async for msg in ws: json.loads(msg)["type"] ...
```
The SDK (`GnaniSTTStreamClient`) **does not expose the VAD, substitution or bias headers**, so use a raw `websockets` client when you need them. See 03-sdks-and-integrations.md.

### 2.3 Batch jobs (long files, diarization)
Sources: https://docs.gnani.ai/api/STTBatch/Introduction (+ Create_Job, Start_Job, Get_Job, Get_Job_Files, List_Jobs, Cancel_Job). Older duplicate pages live under /api/STT/batch/*.

**Flow:** `POST /stt/v3/batch/jobs` (201, `CREATED`) → **`POST /stt/v3/batch/jobs/{id}/start`** (202, `STARTING`; creating a job does NOT start it) → poll `GET /stt/v3/batch/jobs/{id}` every **≥10 s** (30 s for 100+ files) → `GET /stt/v3/batch/jobs/{id}/files?status=COMPLETED` → `GET transcript_url` (pre-signed S3, **no API key**, **expires in 1 h**, re-call `/files` for a fresh one). Ignore the create response's mention of `/v1/jobs/...`.

**Create body.** Option A, multipart: `config` = JSON string sent as part `;type=application/json`, plus `files` repeated (audio or ZIP), plus optional `callback_url`. Option B, `application/json`:
```json
{"config":{"model":"gnani-prisma-v2.5","language_code":"en-IN","mode":"transcribe"},
 "source":{"type":"cloud_storage","auth":{"mode":"public"},"paths":["https://cdn.example.com/a.mp3"]},
 "callback_url":"https://yourapp.com/webhooks/stt"}
```
Public or presigned HTTPS only (no private-bucket auth). A path ending in `/` expands to every audio file under the prefix: billed, and the file count is uncapped. URLs are validated at `/start`; if all are bad you get `START_FAILED`.

| `config` field | Type | Req | Default | Notes |
|---|---|---|---|---|
| `model` | string | ✓ | — | `"gnani-prisma-v2.5"` |
| `language_code` | string | ✓ | — | one code, or ≤3 comma-separated (`"hi-IN,en-IN"`) for **per-file** language ID; the first code is the fallback |
| `mode` | string | | `transcribe` | the only value |
| `with_diarization` | bool | | `false` | |
| `num_speakers` | int | if diarizing | — | **max 2** |
| `is_multi_channel` | bool | | `false` | true multi-channel audio only |
| `with_denoise` | bool | | `false` | speech enhancement for every file in the job; adds ~25% of the audio duration to processing time; same billing |
| `bias_list` / `bias_score` | string[] / number | | score 1.0 if list given | **invalid → `400 INVALID_CONFIG`** (unlike REST) |

ITN: **not supported** on batch, so output is verbatim.
Limits: ≤4 h and ≥0.1 s per file; ≤5,000 speech segments per file; uploads only: 100 files/job (ZIP contents count), 10 MB/file, ZIP 50 MB compressed / 200 MB decompressed / 50:1 ratio; cloud: no byte cap, 30-min download limit, file count uncapped. A file over 4 h → `AUDIO_TOO_LONG`. Silent or tone-only files → file `FAILED` "Empty transcript after 3 retries".
Formats: `.wav .mp3 .mp4 .flac .ogg .opus .m4a .aac .webm .amr`.

Job statuses: `CREATED → STARTING → QUEUED → IN_PROGRESS → COMPLETED`. Terminal: `COMPLETED`, `PARTIAL_FAILURE`, `FAILED`, `START_FAILED` (read `cancel_reason`), `CANCELLED`. `CANCELLING` is transient. File statuses: `COMPLETED` / `FAILED` / `SKIPPED` / `CANCELLED` (+ `error_message`).

Responses:
```json
// GET /jobs/{id}
{"job_id":"…","status":"COMPLETED","config":{"model":"gnani-prisma-v2.5","mode":"transcribe","language_code":"en-IN","with_diarization":false,"num_speakers":null,"is_multi_channel":false,"with_denoise":false},
 "progress":{"total_files":1,"completed_files":1,"failed_files":0,"in_progress_files":0,"queued_files":0,"cancelled_files":0},
 "cancel_reason":null,"created_at":"…","started_at":"…","completed_at":"…","cancelled_at":null,"updated_at":"…"}
// GET /jobs/{id}/files   (query: status, limit 1–100, cursor)
{"job_id":"…","data":[{"file_id":"…","original_path":"customer_call.wav","status":"COMPLETED","duration_seconds":"6.01","transcript_url":"https://gnaniasraudios.s3.amazonaws.com/…?X-Amz-Expires=3600","error_message":null,"created_at":"…","completed_at":"…"}],
 "pagination":{"has_more":false,"next_cursor":null,"total_count":1}}
// transcript_url JSON
{"file_id":"…","job_id":"…","original_path":"customer_call.wav","language_code":"en-IN","duration_seconds":6.01,"model":"gnani-prisma-v2.5","mode":"transcribe",
 "segments":[{"segment_id":0,"start_time":0.0,"end_time":0.71,"text":"hello","speaker_id":1,"confidence":null,"language_detected":null,"sentiment":null,"emotion":null}, …],
 "full_transcript":"hello how can i help you today …","created_at":"…"}
```
`language_code` in the transcript = the language **actually used** (the resolved one when you sent a list). `confidence`, `language_detected`, `sentiment` and `emotion` are always `null`; get sentiment from your LLM. `speaker_id` is an int (1/2). In the docs' sample, **`segment_id` is 0 for every segment**, so don't treat it as a key.

List: `GET /stt/v3/batch/jobs?status=&limit=&cursor=`. Cancel: `POST /stt/v3/batch/jobs/{id}/cancel` with an optional body `{"reason":"..."}` (CREATED → immediately CANCELLED; running → CANCELLING→CANCELLED; already cancelled → `409 JOB_CANCELLED`).
Errors: `400 UNSUPPORTED_LANGUAGE` (also for >3 codes), `400 INVALID_CONFIG`, `401 {"detail":{"error_code":"MISSING_API_KEY",…}}`, `404 JOB_NOT_FOUND`, `409 JOB_ALREADY_STARTED`, `422` (literal `{job_id}` left in the URL), `429` if you poll too fast.

Webhook (`callback_url`; best-effort, polling remains the source of truth). Events `job.completed | job.partial_failure | job.failed (also START_FAILED) | job.cancelled`. Payload: `{event, job_id, org_id, user_id, status, total_files, completed_files, failed_files, cancelled_files, completed_at, callback_url, transcripts:[ <full transcript JSON per file> ]}`. Check `status`, not `event`. No signature or auth scheme is documented for webhooks.

```bash
curl -X POST https://api.vachana.ai/stt/v3/batch/jobs -H 'X-API-Key-ID: <KEY>' \
  -F 'config={"model":"gnani-prisma-v2.5","language_code":"hi-IN","with_diarization":true,"num_speakers":2,"with_denoise":true};type=application/json' \
  -F "files=@./call.wav"
curl -X POST https://api.vachana.ai/stt/v3/batch/jobs/<JOB>/start -H 'X-API-Key-ID: <KEY>'
```

---

## 3. Text-to-Speech — Gnani Timbre v2.5 (beta per the hackathon brief)

Sources: https://docs.gnani.ai/api/TTS/tts-inference · /tts-sse · /tts-websocket · /available-voices

### 3.1 Request body (identical for REST, SSE and WS)
```json
{"text":"नमस्ते, आप कैसे हैं?","voice":"Nalini","model":"timbre-v2.5","language":"hi-IN","speed":1.0,
 "audio_config":{"sample_rate":48000,"num_channels":1,"sample_width":2,"encoding":"linear_pcm","container":"wav"}}
```
| Field | Type | Req (OpenAPI) | Default | Values |
|---|---|---|---|---|
| `text` | string | ✓ | — | No max length documented |
| `model` | enum | ✓ | — | `timbre-v2.5` only (v2.0 deprecated; **the SDK defaults to v2.0 → 400**) |
| `voice` | string | (docs say req) | SDK/plugins: `Pranav` | §3.4 |
| `language` | string | (docs say req) | — | `auto`, `hi-IN`, `en-IN`, `hi-en`, `ta-IN`, `te-IN`, `kn-IN`, `ml-IN`, `mr-IN`, `pa-IN`, `bn-IN`, `gu-IN` |
| `speed` | number\|string | | `1.0` | 0.85–1.15, or `"slow"`=0.85, `"medium"`=1.0, `"fast"`=1.15 |
| `audio_config.sample_rate` | int | | 48000 | 8000, 16000, 22050, 24000, 44100, 48000 |
| `audio_config.num_channels` | int | | 1 | 1–8 |
| `audio_config.sample_width` | int | | 2 | 1–4 bytes |
| `audio_config.encoding` | enum | | `linear_pcm` | `linear_pcm`, `pcm_s16le`, `pcm_mulaw`, `pcm_alaw`, `oggopus` |
| `audio_config.container` | enum | | `wav` | `wav`, `raw`, `mp3`, `ogg`, `mulaw`, `alaw` |
| `audio_config.bitrate` | enum | | `128k` | `32k` `64k` `96k` `128k` `192k` (MP3 only) |

| container | output | Content-Type |
|---|---|---|
| `wav` | WAV with header | `audio/wav` |
| `raw` | raw 16-bit PCM | `application/octet-stream` |
| `mp3` | MP3 | `audio/mpeg` |
| `ogg` | OGG Opus (**never streamed: one chunk at the end**) | `audio/ogg` |
| `mulaw` / `alaw` | raw G.711, **forces 8000 Hz** | `audio/basic` / `audio/alaw` |
Aliases: `raw`+`pcm_mulaw` = `mulaw`; `raw`+`pcm_alaw` = `alaw`; `raw|ogg`+`oggopus` = `ogg`.

Errors: `400 INVALID_REQUEST_ERROR` ("Invalid text or audio configuration." / unsupported voice) · `403 FORBIDDEN` (credits) · `429` · `500` · `503`, all in the `{"success":false,"error":{type,message}}` shape.

### 3.2 REST `POST https://api.vachana.ai/api/v1/tts/inference`
Returns `200` with the raw audio bytes. `curl … -d '{…}' --output response.wav`.

### 3.3 SSE `POST https://api.vachana.ai/api/v1/tts/sse` and WS `wss://api.vachana.ai/api/v1/tts`
SSE events:
```text
event: start     data: {"status":"streaming_started","text":"…"}
event: chunk     data: {"chunk_index":1,"audio":"<base64>","is_final":false}
event: complete  data: {"chunk_index":3,"audio":"","is_final":true}
event: error     data: {…}
```
WebSocket: put `X-API-Key-ID` (and `Content-Type: application/json`) in the upgrade headers, then **send the JSON body above as one text message**. Server replies:
```json
{"type":"start","message":"Streaming started","request_id":"req_abc123"}
{"type":"audio","data":{"chunk_index":1,"audio":"<base64>","is_final":false}}
{"type":"complete","data":{"chunk_index":12,"audio":"","is_final":true}}
{"type":"error","message":"Invalid text or audio configuration."}      // VC WS variant adds "error":"SYNTHESIS_FAILED"
```
Note the WS chunks are wrapped in `data`; SSE chunks are not. Send **one request at a time**. The API page says you can send another request on the same socket after `complete`; the SDK instead opens **one socket per synthesis** and treats `complete` as "connection closing" (**CONFLICT**, verify). There is no incremental text input (you can't stream LLM tokens into one utterance), so chunk the LLM output into sentences and send them in turn **(inferred)**. Per the SDK, SSE chunks for `linear_pcm`+`wav` are **headerless PCM** and the SDK adds the RIFF header when collecting **(inferred from SDK docs; verify)**.

```python
import websocket, json, base64
def on_open(ws): ws.send(json.dumps({"text":"नमस्ते","voice":"Nalini","model":"timbre-v2.5","language":"hi-IN",
    "audio_config":{"sample_rate":8000,"encoding":"pcm_mulaw","container":"mulaw"}}))
def on_message(ws, m):
    msg = json.loads(m)
    if msg.get("type") == "audio": buf.extend(base64.b64decode(msg["data"]["audio"]))
ws = websocket.WebSocketApp("wss://api.vachana.ai/api/v1/tts",
        header={"Content-Type":"application/json","X-API-Key-ID":KEY}, on_open=on_open, on_message=on_message)
```

### 3.4 Voices (42, Timbre v2.5)
Match `voice` with its preferred `language`. Preview at https://app.gnani.ai/voice/text-to-speech.

| `language` | Female | Male |
|---|---|---|
| `en-IN` | Kaveri (prof., firm support), Trupti (prof., upbeat), Devika (prof., authoritative) | Pranav (friendly support, **plugin default**), Shlok (conversational), Girish (expressive storyteller) |
| `hi-IN` | Nalini (friendly, playful), Bhavna (friendly support), Yashvi (warm, reassuring), Urmila (prof., formal announcements), Jwala (friendly everyday), Chitra (warm, mature care), Ambuja (prof. assistant) | Deepak (prof., measured), Roopesh (prof., grounded), Vikrant (conversational, warm), Hemraj (confident, demos), Jalaj (expressive storyteller), Omkar (confident, energetic support) |
| `hi-en` (Hinglish) | Poorvi (conversational, bilingual) | — |
| `ta-IN` | Asmita (prof., corporate), Trisha (friendly guidance), Brinda (prof., steady), Vedika (prof., crisp), Noopur (friendly, warm) | — |
| `te-IN` | Suhana (warm, calm), Lehara (warm, reassuring), Lavanya (warm, empathetic), Yukti (friendly, welcoming), Varuni (conversational) | — |
| `kn-IN` | Saanvi (expressive, ads) | Kavin (prof., presentations) |
| `ml-IN` | Reshma (friendly, greetings) | Riyaan (conversational) |
| `mr-IN` | Zahira (expressive, sales) | Ishaan (prof., instructions) |
| `bn-IN` | Kirra (conversational, soft) | Dhruva (conversational) |
| `gu-IN` | Falak (conversational, narration) | Veera (friendly) |
| `pa-IN` | Mehuli (expressive, promos) | Zayan (warm, empathetic) |

That's 27 F / 15 M. Tamil and Telugu have **no male voice**; for a male voice there, use a clone.

### 3.5 Text normalization (TN) — runs automatically on every request
Source: https://docs.gnani.ai/api/TTS/tts-input-formating
- Pipeline: strip inline pause/speed markup (**syntax undocumented**) → resolve language → honorifics → address/business abbreviations → numbers/currency/dates/IDs (specific before general) → initialisms spelled out → pause commas for dense IDs.
- **This page uses short codes** `auto`(default), `hi en mr ta te kn ml gu pa bn`, while the TTS endpoints use `hi-IN` etc. `"hinglish"` is **rejected**; Hinglish is only an internal result of `auto` on mixed Devanagari+Latin text. `auto` + Latin-only text → always English numbers, so pass the language explicitly to get native-language numbers for "42".
- Deepest coverage: en, hi, mr, ta. Always read in English: units, AM/PM, URLs and emails. "point"/"percent" localize only when the language is set explicitly (Hindi: दशमलव/प्रतिशत).
- Numbers: Indian grouping everywhere (`2,40,000` → two lakh forty thousand). Digit-by-digit when near `account/OTP/card/PIN/Aadhaar/PAN`, for runs of 6+ digits, or for exactly 4/6/10/12/16 digits. Duration words (`minutes/hours/days`) force a quantity reading. Only English compresses repeats ("double eight"). `–` between numbers = "to".
- Currency `₹599` / `Rs 500` / `₹4,312.50` (rupees and paise) / `₹12.6 crore` / `$4.7 million`. `%` and `p.a.` handled.
- Dates `DD/MM/YYYY`, `DD-MM-YYYY`, `25 Jun 2026`; **`23/06` reads as a fraction** (include the year). `FY2024-25`, `Q1`. Times `5:30 PM`, `20:00`→eight P M, `22:00 hrs`.
- IDs: PAN, Aadhaar (4-4-4), IFSC, GSTIN, 10-digit phone (3-3-4), `+91…`, toll-free, OTP, masked `****4821`, vehicle plates, flight/train numbers, EPIC, seat/gate, `#12345`, UPI `9876543210@ybl`.
- Units: kg, g (lowercase), km, mg (lowercase), ml, L, °C/°F, GB/MB/TB, `Mbps` (exact case only), km/h, sqft, `5'11"`. A bare `5°` is not normalized.
- Math symbols, fractions (`1/2` → "one by two"; native connectors only in hi/mr), Roman numerals only after trigger words.
- Initialisms spelled out: OTP, EMI, UPI, NEFT, KYC, GST, IFSC, ATM, HDFC, ICICI, SBI, … Read as words: PIN, SIM, RAM, SEBI, TRAI, CIBIL, RERA. "Gnani" is pronounced "Gyaanee"/ज्ञानी.
- Known issues: 4-segment EPIC IDs; OTP digits may be compressed ("double four"); 14+ digit references read as one raw run (add separators); `hr` → "H R"; `minus` isn't localized. Custom pronunciations require contacting Gnani.
- The intro page claims "SSML supported on TTS", but **no SSML syntax is documented anywhere**.

---

## 4. Voice cloning

Sources: https://docs.gnani.ai/api/VC/voice-clone-embeddings · /vc-inference · /vc-sse · /vc-websocket

**Step 1 — embedding** (once per voice; cache it):
```bash
curl -X POST https://api.vachana.ai/api/v1/tts/voice-clone/embeddings \
  -H 'X-API-Key-ID: <KEY>' -F audio_file='@reference.wav'     # 5–30 s clean speech, WAV/MP3
```
Response: **CONFLICT**. The OpenAPI schema says `{"success":true,"message":"Voice embeddings generated successfully","data":{"voice_clone_embedding":{"embedding":"<base64>","shape":[1,768],"dtype":"torch.bfloat16"}}}`, but the quick start shows the flat `{"embedding":…,"shape":[1,768],"dtype":"torch.bfloat16"}`. Parse both shapes defensively. No documented limits on embedding count or storage; nothing about consent; no "list or delete my voices" endpoint (the embedding is just a blob you keep).

**Step 2 — synthesize** using the same three TTS endpoints (REST `/api/v1/tts/inference`, SSE `/api/v1/tts/sse`, WS `wss://…/api/v1/tts`) with the same response protocols as §3:
```json
{"text":"नमस्ते, आप कैसे हैं?","model":"vachana-vc-v1",
 "audio_config":{"sample_rate":44100,"num_channels":1,"sample_width":2,"encoding":"linear_pcm","container":"wav"},
 "speaker_embedding":{"embedding":"<base64>","shape":[1,768],"dtype":"torch.bfloat16"}}
```
- Required: `text`, `speaker_embedding{embedding,shape,dtype}`, `audio_config`. `model` = `vachana-vc-v1` and is auto-set when an embedding is present. `voice`, `language` and `speed` are **not in the VC schema**, so whether the language can be controlled is unknown **(verify)**.
- VC `audio_config` is narrower than TTS: sample_rate **8000–44100**, encoding `linear_pcm|oggopus`, container `raw|mp3|wav|mulaw|ogg` (**no alaw**), bitrate `96k|128k|192k`.
- The VC WS page says "include a complete audio_config" (its own examples omit fields). Quick-start VC WS says "server streams **binary PCM**", but the VC WS page says JSON+base64 like TTS WS (**CONFLICT**; handle both).
- The SDK example passes `model="timbre-v2.5"` together with `speaker_embedding` (**CONFLICT** with `vachana-vc-v1`).

---

## 5. Common error/response envelope summary
| API | Error shape |
|---|---|
| STT REST, TTS, VC | `{"success":false,"error":{"type":"INVALID_REQUEST_ERROR|FORBIDDEN|RATE_LIMIT_ERROR|API_ERROR|SERVICE_UNAVAILABLE","message":"…"}}` |
| Batch | `{"error":"UNSUPPORTED_LANGUAGE|INVALID_CONFIG|JOB_NOT_FOUND|JOB_ALREADY_STARTED|JOB_CANCELLED","message":"…"}`; 401 = `{"detail":{"error_code":"MISSING_API_KEY",…}}` |
| STT WS | `{"type":"error","timestamp":…,"message":…}`; close code 4001 = auth |
| TTS/VC WS | `{"type":"error","message":…}` (+`"error":"SYNTHESIS_FAILED"`) |
Optional tracing header on any call: `X-API-Request-ID: <uuid>` (the SDK sends one automatically).

---

## 6. Which API for which hackathon use-case

The award categories from the registration email include regional languages, Hinglish/code-mixed, **noisy telephonic audio**, real-world impact and best 60-s demo.

| Use-case | STT choice | TTS choice | Notes |
|---|---|---|---|
| **Live phone-call voice agent** (IVR, Exotel/Twilio-style 8 kHz) | WS `/stt/v3/stream`, `x-sample-rate: 8000`, telephony preset (thr 0.7, min-speech 200, min-silence 400–500) | WS `/api/v1/tts` with `container: mulaw` (or `alaw`) → 8 kHz G.711, no transcoding (µ-law from the carrier must be decoded to PCM16 before STT **(inferred)**) | Orchestrate with Pipecat (`GnaniTTSService` = barge-in) or LiveKit. LLM is not a Gnani API (see 03). Plan reconnects for the 15-min cap. Expected end-of-turn ≈ min-silence + ~300 ms |
| **Browser voice assistant** | WS at 48000 (or downsample to 16k), via a **backend proxy** (no headers from the browser) | WS or SSE, `raw` PCM 24k/48k for Web Audio | Lower `x-min-silence-ms` (~400) feels snappier, but sentences split |
| **Offline long recordings** (lectures, court, podcasts, call archives) | Batch; public-URL source for >10 MB files (≤4 h); `with_diarization`+`num_speakers:2`; `with_denoise` if noisy; webhook or poll | REST/SSE for any audio summary | No ITN in batch, so normalize numbers yourself or with an LLM. Diarization is 2 speakers max, so panels are out of scope. Gujarati/Punjabi → split to ≤60 s chunks + REST, or WS **(inferred)** |
| **Code-mixed Hinglish** | REST with `language_code=hi-IN` (+ try `multi_lang_codes` hi-IN,en-IN, unverified); WS with `lang_code: hi-IN` (single language per session) | Voice **Poorvi**, `language: hi-en` (or `auto` with mixed Devanagari+Latin text) | ITN handles code-mixed money/time. Batch lang-ID is per file, not per segment. Word-boost English brand words (`bias_list`) on hi-IN |
| **Noisy telephony 8 kHz audio** | Live: WS 8000 + raise `x-vad-threshold` 0.7–0.75, `x-min-speech-ms` 200–300, `x-min-segment-ms` 200. Offline: Batch `with_denoise:true` | `mulaw/alaw` 8k | REST accepts 8k files (auto-upsampled). Prisma is "trained on 14M+ hours of telephonic audio" (brief) |
| **Regional-language app (ta/te/kn/ml/bn/mr/gu/pa)** | REST/WS for all 10; Batch for 8 | Voices exist for all 10 (ta/te female only) | Explicit `language` makes TN read numbers natively |
| **Personalized voice (clone)** | — | Embedding once → VC WS/SSE | 5–30 s clean sample; store the embedding in your DB |
| **Domain vocab (banking, medicine, product names)** | `bias_list` (≤100 single words, letters only, `format=verbatim`) + `substitution_map` (≤10 rules) | TN handles IFSC/PAN/UPI/₹ | Boost invalid on REST = silent no-op |

---

## 7. Gotchas · unknowns · verify with a live call

**Doc conflicts (resolve empirically):**
1. **Batch languages**: the newest Intro and Create_Job error list 8 codes (no `bn-BD`). Older /api/STT/batch pages and the podcast/call-analytics tutorials list `bn-BD` (and call-analytics lists `hi-en`). Assume 8.
2. **Batch word boosting**: the REST page says it's "not available on Batch STT", while the Batch pages document it (with 400 on invalid input).
3. **ITN languages**: all languages (REST/WS pages) vs **hi-IN/en-IN only** (SDK and compliance tutorial).
4. **Hinglish TTS code**: `hi-en` (API and OpenAPI) vs `auto` (SDK voice table) vs TN page ("hinglish" rejected, short codes `hi`/`en`).
5. **VC embeddings response**: nested `data.voice_clone_embedding` vs flat.
6. **VC model**: `vachana-vc-v1` vs the SDK example's `timbre-v2.5`.
7. **VC WS output**: JSON base64 vs "binary PCM".
8. **TTS WS socket reuse**: allowed (API) vs one socket per synthesis (SDK).
9. **REST STT max**: 60 s almost everywhere, but one OpenAPI line says "Maximum duration: 30 seconds".
10. **Python version**: 3.10+ (most pages) vs 3.9+ (SDK intro).

**Unknowns to measure in the first live session** (each a few seconds of audio, cheap on credits **(inferred)**):
- [ ] **Credit cost per call**: STT per second? TTS per character? Clone embedding? Check the dashboard usage after each test call. Nothing is documented; the only signal is `403 FORBIDDEN` "…available credits".
- [ ] Rate limits and concurrent WS sessions per key (only `429` is documented).
- [ ] STT WS: what happens on clean close mid-utterance (is the last segment flushed?), idle timeout without audio, whether zero-padding works as a flush, whether `x-partials: true` yields `partial_transcript`.
- [ ] `/stt/v4/stream` existence and differences.
- [ ] `multi_lang_codes` on REST: format (CSV? repeated field?) and output script for Hinglish.
- [ ] Hinglish STT output: Devanagari vs Latin for English words; how `hi-IN` vs `en-IN` handle mixed speech.
- [ ] Real end-of-speech → transcript latency on 8k vs 16k from India (log `latency`, and wall-clock from the last frame).
- [ ] TTS: time-to-first-chunk SSE vs WS; is the max text length per request enforced?; WAV-container chunk headers; socket reuse after `complete`.
- [ ] TTS `language: hi-en` vs `auto` with Poorvi.
- [ ] VC: response shape; supports `language`?; quality on 8k phone recordings vs clean; works for non-Hindi text?
- [ ] Batch: real turnaround time for a 5–10 min file; diarization quality; whether `num_speakers:1` is allowed.
- [ ] Webhook: any signing header? Retry policy?
- [ ] Inline pause/speed markup syntax in TTS (mentioned, not documented), and whether SSML works at all.

**Hard-won rules:**
- STT WS frames must be **exactly 1024 bytes**, real-time paced. Pad the last frame with zeros (`b"\x00"`, not spaces; the compliance full example pads with `b" "`, which is a bug).
- REST STT bias errors are silent. Batch bias errors return 400.
- Batch: always call `/start`; transcripts only come via `transcript_url` (1 h expiry) or webhook; `GET /files` returns `data[]`, not `files[]`, and progress counters live under `progress.*`. **Both tutorials get these two wrong.**
- Batch upload is capped at 10 MB/file. Compress to opus/mp3 with ffmpeg, or host the file and use `cloud_storage` (up to 4 h).
- `transcript` events have no speaker labels or word timings. For live diarization you'd need two channels → two WS sessions (agent leg, customer leg) **(inferred)**.
- TTS `mulaw/alaw` force 8 kHz regardless of `sample_rate`. OGG is never streamed.
- TTS needs `model: "timbre-v2.5"` explicitly (SDK default v2.0 = 400).
- Tamil/Telugu have only female voices. Gujarati "Veera" is male.
