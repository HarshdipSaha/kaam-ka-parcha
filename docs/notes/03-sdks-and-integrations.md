# 03 — SDKs, framework plugins, tutorials, and the "is there an LLM API?" question

Source: `docs/raw/llms-full.txt` (Mintlify export; line refs below point into it), with the hackathon brief files `docs/abouthack.txt`, `docs/response.txt` and `docs/links.txt`. No Gnani API was called.
Legend: **(inferred)** = my own conclusion, not stated in the docs. Endpoint and protocol details are in `02-speech-apis.md`.

---

## 0. TL;DR

| Package | Install | Import | Wraps | Python |
|---|---|---|---|---|
| Official SDK | `pip install gnani-vachana` (or `uv add gnani-vachana`) | `gnani.stt`, `gnani.tts` | STT REST+WS, TTS REST+SSE+WS (+ voice-clone synthesis via `SpeakerEmbedding`) | 3.10+ (SDK intro says 3.9+). Deps: `requests`, `websockets`. Typed (`py.typed`) |
| LiveKit Agents plugin | `pip install livekit-plugins-gnani` | `from livekit.plugins.gnani import STT, TTS` | Own `aiohttp`/`websockets` implementation (doesn't use gnani-vachana) | 3.10+ |
| Pipecat plugin | `pip install pipecat-gnani` | `from pipecat_gnani import …` | Adapter over `gnani-vachana>=0.7.3`; tested with Pipecat v1.5.0 | 3.10+ |

All three take one API key (`GNANI_API_KEY` env var or `api_key=`). `organization_id`/`user_id` were removed in SDK 0.7.x; remove them from any old code.
**None of them exposes an LLM. Evon is not served by any Gnani API in these docs (§5).**

---

## 1. Python SDK `gnani-vachana`
Sources: https://docs.gnani.ai/python-sdk/introduction · /python-sdk/speech-to-text · /python-sdk/text-to-speech (lines 16749–17787)

### 1.1 Client classes
| Class | Module | Transport | Sync/async |
|---|---|---|---|
| `GnaniSTTClient` | `gnani.stt` | REST `POST /stt/v3` (≤60 s) | sync |
| `GnaniSTTStreamClient` | `gnani.stt` | WS `/stt/v3/stream` | async (async context manager) |
| `GnaniTTSClient` | `gnani.tts` | REST `/api/v1/tts/inference` | sync |
| `GnaniTTSStreamClient` | `gnani.tts` | SSE `/api/v1/tts/sse` | sync generator |
| `GnaniTTSRealtimeClient` | `gnani.tts` | WS `/api/v1/tts` | async |
| Helpers | `gnani.tts.AudioConfig`, `gnani.tts.SpeakerEmbedding`; `gnani.stt.STREAM_CHUNK_BYTES` (1024), `STREAM_CHUNK_SAMPLES` (512) | | |

All constructors take `api_key=None` (falls back to `GNANI_API_KEY`; if both are missing → `AuthenticationError` at construction) and `base_url="https://api.vachana.ai"` (WS URL derived as https→wss). Every method takes `request_id=None`; when omitted the SDK generates one and sends it as `X-API-Request-ID`.

### 1.2 STT
```python
from gnani.stt import GnaniSTTClient
c = GnaniSTTClient()
r = c.transcribe("rec.wav", language_code="hi-IN", format="transcribe", itn_native_numerals=False, request_id=None)
r["transcript"], r["request_id"]          # dict = raw JSON {success, request_id, timestamp, transcript}
r = c.transcribe_bytes(audio_bytes, filename="upload.wav", language_code="en-IN")   # filename ext = decoder hint
GnaniSTTClient.supported_languages()       # {"en-IN": "English (India)", ...}
```
- `transcribe(audio: str|Path|BinaryIO|bytes, language_code="en-IN", format="verbatim", itn_native_numerals=False, request_id=auto)`. Raw `bytes` also works per the STT REST page.
- Locally accepted extensions: `.wav .mp3 .flac .ogg .m4a .aac`. Anything else → `InvalidAudioError` with no network call.
- **Not exposed by the SDK:** `bias_list`/`bias_score`, `enable_substitution`/`substitution_map` (absent from the SDK param tables **(inferred)**), `multi_lang_codes` (explicitly "not yet exposed"). Use raw `requests` for these.

```python
from gnani.stt import GnaniSTTStreamClient, StreamTranscriptEvent, StreamProcessingEvent, StreamConnectedEvent, StreamErrorEvent
async with GnaniSTTStreamClient(api_key=None, language_code="hi-IN", sample_rate=16000,   # 8000|16000|44100|48000
                                format="verbatim", itn_native_numerals=False) as stream:
    # (a) easiest: paces frames for you, returns all transcripts
    ts = await stream.stream_audio(f_or_async_iter, on_transcript=cb, on_processing=cb2, on_error=cb3,
                                   chunk_size=1024, realtime_pace=True)
    # (b) manual: run sender and receiver as SEPARATE tasks for live sources
    await stream.send_audio(frame_1024)       # then asyncio.sleep(0.032 @16k / 0.064 @8k)
    async for ev in stream: ...
# (c) lifecycle: ev = await stream.connect(request_id=None); await stream.send_audio(f); ts = await stream.close()
#     props: is_connected, connected_config, transcripts
```
- Events (dataclasses with `.raw`): `StreamConnectedEvent(message, timestamp, sample_rate, chunk_size)`, `StreamProcessingEvent(timestamp)`, `StreamTranscriptEvent(text, audio_duration_ms, segment_id, segment_index, latency, timestamp)`, `StreamErrorEvent(message, timestamp)`.
- If you set no `on_error` → `StreamError` is raised. Without a callback, `stream_audio` raises on server errors.
- **No VAD-tuning, bias or substitution parameters in the SDK.** Use raw `websockets` with headers for those (see 02 §2.2). It's single-language per session.
- STT exceptions (all subclass `GnaniSTTError`, from `gnani.stt` or `gnani.stt.exceptions`): `AuthenticationError`, `InvalidAudioError`, `APIError(.status_code, .body)`, `StreamConnectionError` (handshake failed, e.g. 401), `StreamClosedError` (sent on a closed stream), `StreamError(.message, .timestamp)`. Bad constructor values → `ValueError`.

### 1.3 TTS
> **Always pass `model="timbre-v2.5"`.** The SDK default is `timbre-v2.0`, which the API no longer serves (`400 The supported models are "timbre-v2.5"`).

Shared params for all three TTS clients: `text` (req), `voice="Pranav"`, `model="timbre-v2.0"`(!), `language=None` (v2.5 only; `auto|hi-IN|en-IN|ta-IN|te-IN|kn-IN|ml-IN|mr-IN|bn-IN|gu-IN|pa-IN`), `speed=1.0` (0.85–1.15; v2.5 only), `audio_config=AudioConfig()` (default 48 kHz mono 16-bit WAV), `speaker_embedding=None` (voice ignored when set), `output_file=None` (writes the file and creates parent dirs; not available on streaming generators), `request_id`. Invalid voice/speed/sample rate etc. → `ValueError` locally.

```python
from gnani.tts import GnaniTTSClient, GnaniTTSStreamClient, GnaniTTSRealtimeClient, AudioConfig, SpeakerEmbedding
audio = GnaniTTSClient().synthesize("नमस्ते", voice="Nalini", model="timbre-v2.5", language="hi-IN", output_file="o.wav")  # -> bytes

for chunk in GnaniTTSStreamClient().synthesize_stream("Hi", voice="Kaveri", model="timbre-v2.5", language="en-IN"):
    player.write(chunk)                 # raw PCM chunks, NO WAV header
GnaniTTSStreamClient().synthesize(..., output_file="x.wav")   # collects + adds RIFF header for linear_pcm/wav

async with GnaniTTSRealtimeClient() as c:
    async for chunk in c.synthesize(text, voice="Nalini", model="timbre-v2.5", language="hi-IN"): ...
    audio = await c.synthesize_and_collect(text, ..., output_file="reply.wav")
    async for ev in c.synthesize_events(text, ...):   # TTSStartEvent(request_id,message) /
        ...                                            # TTSAudioChunkEvent(data: bytes, chunk_index, is_final) /
                                                       # TTSCompletedEvent(request_id, total_chunks)
GnaniTTSClient.supported_voices("timbre-v2.5")         # ["Ambuja","Asmita",...]
```
- The realtime client opens **one WebSocket per call** (no pooling). Reusing a client instance is "safe and cheap".
- `AudioConfig(sample_rate=48000, encoding="linear_pcm", num_channels=1, sample_width=2, container="wav", bitrate=None)`. Presets: µ-law `AudioConfig(sample_rate=8000, encoding="pcm_mulaw", container="mulaw")`, A-law `(8000,"pcm_alaw","alaw")`, MP3 `(container="mp3", bitrate="128k")`, Opus `(encoding="oggopus", container="raw")`.
- Voice cloning: `SpeakerEmbedding(embedding=str, shape=[1,768], dtype="torch.bfloat16")` → `synthesize(..., model="timbre-v2.5", speaker_embedding=emb)` (the docs' example; the API says model `vachana-vc-v1`, so verify). **The SDK has no method to create the embedding**; call `POST /api/v1/tts/voice-clone/embeddings` with `requests`.
- TTS exceptions (subclass `GnaniTTSError`, from `gnani.tts.exceptions`): `AuthenticationError`, `APIError`, `StreamConnectionError`, `StreamClosedError`, `StreamError`; plus a plain `ValueError`.

---

## 2. LiveKit plugin `livekit-plugins-gnani`
Source: https://docs.gnani.ai/livekit/introduction (lines 16015–16338). LiveKit's own pages: https://docs.livekit.io/agents/integrations/stt/gnani/ and …/tts/gnani/

- Installs `websockets` + `livekit-agents`. Implements LiveKit `stt.STT` / `tts.TTS`. Maintained by Gnani.

```python
from livekit.plugins.gnani import STT, TTS
stt = STT(language="hi-IN", sample_rate=16000, format="verbatim")   # recognize() → REST /stt/v3 ; stream() → WS /stt/v3/stream
tts = TTS(voice="Pranav", synthesize_method="websocket")            # "rest" (default) | "sse" | "websocket"; stream() is always WS
```
| `STT` param | Default | Notes |
|---|---|---|
| `language` | `"en-IN"` | BCP-47 `-IN` |
| `sample_rate` | `16000` | **only `8000`/`16000`** in the plugin |
| `format` | `"verbatim"` | `"transcribe"` = ITN |
| `itn_native_numerals` | `False` | (REST table) |
| `api_key` / `base_url` | env / `https://api.vachana.ai` | |

| `TTS` param | Default | Notes |
|---|---|---|
| `voice` | `"Pranav"` | |
| `model` | `"timbre-v2.5"` | (the plugin's default is correct, unlike the SDK) |
| `sample_rate` | `16000` | REST table lists 8000/16000/22050/44100 |
| `encoding` | `"linear_pcm"` | `linear_pcm`/`oggopus` |
| `container` | `"wav"` | `wav/raw/mp3/mulaw/ogg` |
| `num_channels` / `bitrate` | 1 / None | `96k/128k/192k` |
| `synthesize_method` | `"rest"` | `"sse"`, `"websocket"` |
| `update_options()` | — | change voice/model at runtime (WS) |

There's no `language` param on the LiveKit TTS (voice drives language) and no VAD/bias/substitution knobs on the LiveKit STT (none documented). The docs don't include a full LiveKit `AgentSession` example. Typical wiring would be `AgentSession(stt=gnani.STT(...), llm=<any LLM plugin>, tts=gnani.TTS(...), vad=silero.VAD.load())` **(inferred, standard LiveKit pattern)**.

---

## 3. Pipecat plugin `pipecat-gnani`
Source: https://docs.gnani.ai/pipecat/introduction (lines 16340–16746). Repo example: https://github.com/Gnani-AI-Mintlify/pipecat-gnani/blob/main/examples/foundational/agent.py

| Service | Base class | Transport | Needs |
|---|---|---|---|
| `GnaniHttpSTTService` | `SegmentedSTTService` | REST `/stt/v3` | VAD in the pipeline + `aiohttp_session` |
| `GnaniSTTService` | `STTService` | WS `/stt/v3/stream` | emits `TranscriptionFrame` (finals only today; `InterimTranscriptionFrame` only if the API ever sends `is_final:false`) |
| `GnaniHttpTTSService` | `TTSService` | REST | `aiohttp_session` |
| `GnaniSSETTSService` | `TTSService` | SSE | `aiohttp_session` |
| `GnaniTTSService` | `InterruptibleTTSService` | WS `/api/v1/tts` | **barge-in support**, recommended |

Settings objects: `GnaniSTTService.Settings(language=Language.HI_IN, sample_rate=16000)` (`Language` enum from `pipecat.transcriptions.language`; default `Language.EN_IN`; rate 8000/16000). `Gnani*TTSService.Settings(voice="Pranav", sample_rate=16000)`. Env: `GNANI_API_KEY`, plus `GROQ_API_KEY` for the example LLM.

Foundational pipeline (verbatim from the docs; the LLM is **Groq `llama-3.1-8b-instant`**, not Gnani):
```python
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair, LLMUserAggregatorParams
from pipecat.services.groq.llm import GroqLLMService
from pipecat.transcriptions.language import Language
from pipecat_gnani import GnaniSTTService, GnaniTTSService

stt = GnaniSTTService(api_key=os.environ["GNANI_API_KEY"], settings=GnaniSTTService.Settings(language=Language.HI_IN))
tts = GnaniTTSService(api_key=os.environ["GNANI_API_KEY"], settings=GnaniTTSService.Settings(voice="Pranav"))
llm = GroqLLMService(api_key=os.environ["GROQ_API_KEY"], settings=GroqLLMService.Settings(model="llama-3.1-8b-instant"))
context = LLMContext()
aggregators = LLMContextAggregatorPair(context, user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()))
pipeline = Pipeline([transport.input(), stt, aggregators.user(), llm, tts, transport.output(), aggregators.assistant()])
task = PipelineTask(pipeline, params=PipelineParams(enable_metrics=True))
```
To use Evon instead of Groq, put any OpenAI-compatible server hosting Evon behind Pipecat's `OpenAILLMService(base_url=...)` **(inferred, not in the docs)**. The Pipecat TTS docs expose no language or audio_config knobs beyond `voice`/`sample_rate`, so for µ-law telephony output you'd rely on the transport's serializer **(inferred)**.

**Plugin choice (inferred):** Pipecat if you want telephony serializers (Twilio/Exotel/Plivo) and interruptible TTS out of the box. LiveKit if you want WebRTC rooms or a browser demo. Raw SDK/WS if you need VAD tuning or word boosting (neither plugin exposes them).

---

## 4. The three use-case tutorials

### 4.1 Call Analytics Pipeline — https://docs.gnani.ai/api/use-cases/call-analytics (lines 13790–14506)
- **Architecture:** files → Batch STT (`with_diarization: true`, `num_speakers: 2`, `mode: transcribe`) → create, start, poll every 10 s, `/files?status=COMPLETED`, download `transcript_url` → write `SPEAKER_n: text` lines plus per-speaker talk time → LLM structured analysis → ad-hoc Q&A → cross-call summary report.
- **LLM:** external. `LLM_PROVIDER=claude` (`anthropic`, model `claude-opus-4-8`, max_tokens 2000) or `openai` (`gpt-4o` via `client.chat.completions.create`), lines 14129, 14141, 14383, 14388. Sentiment comes **from the LLM**; STT returns no sentiment.
- **Reusable ideas:** the `CallAnalytics` class; a 10-point analysis prompt (speaker ID, customer type, opening problem, products, agent handling, resolution, sentiment arc, upsell/cross-sell signals, competitor mentions, summary); a 9-point "2–3 word" summary prompt; Q&A per call with sha1-hashed filenames; outputs `{name}_conversation.txt`, `_timing.json`, `_analysis.txt`, `_q_<hash>.txt`, `summary_<ts>.txt`; chunk transcripts for calls >30 min.
- **Bugs in the docs' code (fix before reuse):** `resp.json().get("files", [])` should be `.get("data", [])`. Progress counters are read as top-level `completed_files`/`total_files` but actually live in `payload["progress"]`. `"audio/wav"` is hard-coded as the MIME type for every file. It also lists `bn-BD` and `hi-en` as batch languages, which conflicts with the Batch intro.
- It recommends ffmpeg to get files under the 10 MB per-file cap, and documents an optional `X-API-Request-ID` header.

### 4.2 Podcast Transcription with Speaker Labels — https://docs.gnani.ai/api/use-cases/podcast-transcription (lines 14509–15071)
- **Architecture:** the same Batch create→start→poll→files→download flow, using plain `requests` with no SDK. `parse_transcript()` writes `[MM:SS] SPEAKER_n: text` plus `_metadata.json` (full_transcript, duration, `speaker_talk_time`, segments with `language_detected`).
- **LLM:** none.
- **Reusable ideas:** timestamped speaker lines suit subtitles, chapters and clip extraction. Its list of other use cases: journalist interviews, legal depositions, EdTech lectures, doctor-patient consults (EMR), radio archives, earnings calls, documentary rough cuts.
- **Limits it stresses:** **two speakers max** (panels of 3+ "outside the current scope"); 10 MB per file (split, then stitch transcripts in order). It has the same `.get("files")` and `completed_files` bugs as 4.1.

### 4.3 Real-Time Quality & Compliance Monitoring — https://docs.gnani.ai/api/use-cases/real-time-compliance (lines 15074–15714)
- **Architecture:** telephony bridge / RTP tap (PCM16 mono, 8 or 16 kHz) → audio producer (1024-byte frames, real-time pacing) → `GnaniSTTStreamClient` (WS) → per-segment **ComplianceEngine** + **QualityEngine** → async **AlertDispatcher** (webhook, queue or dashboard; `CRITICAL` goes to a supervisor right away, `WARNING` to post-call review). One `CallSession` per call survives reconnects and is flushed at call end.
- **LLM:** none in the pipeline. "What to build next" lists agent assist (an LLM on each transcript), LLM summarisation, sentiment, diarization and a 0–100 compliance score.
- **Reusable ideas:**
  - `rules/compliance.json`: `prohibited_keywords` (e.g. SEBI "guaranteed returns", "risk-free"), `risk_phrases` (churn: "cancel my policy"; complaints: "RBI complaint", "consumer forum"), `required_disclosures` ("this call is being recorded" within the first 3 segments).
  - `rules/quality.json`: silence > 8 s, escalation phrases, interruption gap < 300 ms, short segment < 500 ms.
  - Reconnect loop with exponential backoff (base 1 s, cap 30 s, 20% jitter, max 5), deduplicating with `processed_indices`. Don't retry `StreamConnectionError` (auth/config).
  - Track p50/p95/p99 of `latency` per call. Fire alerts via `asyncio.create_task`. One asyncio Task per call; the docs claim "100+ concurrent calls" per process.
  - Debug table: close code 4001 = auth; garbled text = sample-rate mismatch or stereo; VAD firing too often = burst sending; no events = all-zero audio.
- **Claims:** "alerts in under 200ms of speech completion" (headline) vs "~300–500 ms from end of speech to transcript" (architecture section). It says ITN applies to hi-IN/en-IN only. Cross-region adds 50–150 ms RTT.
- **Bugs in the docs' code:** the full example pads the final frame with `b" "` (should be `b"\x00"`). `AlertDispatcher` is never defined. Its `stream_audio_producer` in the full script doesn't sleep (pacing comes from `file_audio_source`). Substring matching without word boundaries; the docs themselves recommend regex.

---

## 5. Is Evon (or any LLM) exposed via an API in the docs? **No.**

Searched the whole 17,787-line dump:

| Term | Hits | Finding |
|---|---|---|
| `Evon` | **0** | Not mentioned anywhere in docs.gnani.ai. Only the hackathon material mentions it: `abouthack.txt` L89–92 ("Evon v3.3 — 30B params, ~3.5B active per token, 128K context, 11 Indian languages natively, Apache 2.0 weights available by request on Hugging Face"), `response.txt` L10 ("Evon (30B parameter reasoning model, available on hugging face)"), `links.txt` L3 → **https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B** (MoE "30B-A3B"). |
| `Warp` | **0** | Only in `abouthack.txt` L198 ("Model overview: Prisma, Timbre, Warp and Evon"). Never defined in the docs. |
| `chat/completions` | 0 | No Gnani chat endpoint. `client.chat.completions.create` appears only as **OpenAI SDK** calls inside the call-analytics tutorial (L14140, L14388). |
| `LLM` | many | All of them are (a) the Agent Builder console ("Provider and model — LLM that generates replies", L87) or the Platform API, or (b) tutorials using external LLMs (Claude/OpenAI L14129–14141; Groq Llama L16429–16448). |
| `Vachana` | 143 | It's the **speech API brand and domain**, not an LLM: `api.vachana.ai`, the `gnani-vachana` SDK, `vachana-vc-v1` (clone model), `vachana-audio-intelligence-v2` (default STT model, L8417). Agent Builder ids `vachana_timbre-v2.5` / `vachana-voice-v1-standard-streaming` (TTS, L5219–5225) and `gnani_vachana_rest` (ASR, L5468, L6316). |

**The only Gnani-hosted LLM in the docs** is inside the **Agent Builder (Inya) Platform API**. That's a separate product and auth:
- Base `https://api.inya.ai/platform`, header `x-api-key` (permission-scoped `agents`/`conversations`), L7148–7200.
- `GET /v1/agents/config/llm_models` (L4810–4966) lists providers `anthropic` (claude-3-5-sonnet-20241022), **`gnani` → models `"Pampa Go"`, `"Pampa Priority"`** (L4882–4889; function calling true; langs en-IN, hi-IN, ta-IN, kn-IN, en-US), and `openai` (gpt-4.1-mini, gpt-4o-mini).
- You can only use them as an agent's `llmParams: {provider:"gnani", model:"Pampa Go", temperature 0–1, maxTokens 1–4096}` (L4008, L4085, L6219, L6319). New agents default to temperature 0.5, max tokens 300 (L3537). There is **no raw text-completion endpoint**: the LLM runs only inside a configured voice/chat agent.
- Whether the hackathon's 5,000 credits / `app.gnani.ai/voice` key works on `api.inya.ai` is **unknown**. Inya credit setup goes through `hello-inya@gnani.site` (L1694–1702).

**Implications for the build (inferred):**
1. To "use Evon" (good for scoring, since "uses Gnani models"), self-host the HF weights. Access is by request (Apache-2.0). It's a 30B MoE with ~3B active, so a quantized build fits on a single 24–48 GB GPU, or use a cloud GPU with vLLM / llama.cpp exposing an OpenAI-compatible `/v1/chat/completions`. **The local laptop has no usable GPU**, so budget cloud compute. Request HF access early.
2. Otherwise, pair Prisma+Timbre with any external LLM (Groq/Claude/OpenAI, as the docs' tutorials do) and name Evon as an optional or offline component.
3. Or build an Agent Builder agent on `provider: gnani` / `Pampa Go`. That's a no-code path, but it's a different product, the key/credits may differ, and you get less control.
4. The submission must name the Gnani models/APIs used. Prisma (STT) + Timbre (TTS) + optional voice cloning + Evon (if self-hosted) maximizes coverage.

---

## 6. Quick decision matrix
| Need | Use |
|---|---|
| Fastest working demo (file in → text, text → audio) | `gnani-vachana` REST clients |
| Live voice agent with barge-in + telephony | Pipecat + `GnaniSTTService` + `GnaniTTSService` + LLM of choice |
| Browser/WebRTC voice agent | LiveKit + `livekit-plugins-gnani` (`synthesize_method="websocket"`) |
| VAD tuning, word boosting, substitution mid-call | raw `websockets` to `/stt/v3/stream` (not SDK or plugins) |
| Long audio, diarization, denoise | raw `requests` against Batch (no SDK support documented) |
| Voice clone | `requests` POST for the embedding → SDK `SpeakerEmbedding` or raw TTS call with `speaker_embedding` |
| LLM | not a Gnani API: self-host Evon (HF) or external; Agent Builder "Pampa" only inside Inya agents |
