# Gnani Agent Builder and the Agent Builder Platform REST API

> **Sources:** `docs/raw/llms-full.txt` (Mintlify export), lines 1–7365 and 15717–16014, read in full on 2026-10-04.
> The Postman collection embedded at line 7295 (base64) was decoded and checked as well.
> Spot-checked live on 2026-10-04 with `curl https://docs.gnani.ai/<page>.md`: `introduction`, `A02_Agent`, `Platform/Get_LLM_Models` and `Platform/platform-introduction`. The live `Get_LLM_Models` page still lists only Pampa, Claude and GPT models.
> Docs footers read "Last verified: 5 Aug 2026" (Agent Builder intro) and "11 Aug 2026" (Platform API intro).
> **No Gnani API was called.** Anything marked *(inferred)* is my reading and is not stated in the docs.

---

## TL;DR

- **Agent Builder** (the docs also call it **"Gnani Agents"**) is Gnani's no-code console for **phone and web voice agents**. You assemble a knowledge base, a prompt, ASR, LLM and TTS choices, actions, dispositions and analytics, and Gnani hosts the whole loop: telephony, ASR, LLM and TTS.
  Its REST twin is the **Agent Builder Platform API** at **`https://api.inya.ai/platform`**, authenticated with an **`x-api-key`** header.
- **It is a different product and a different domain from the Speech APIs.** Prisma and Timbre live at `https://api.vachana.ai` with header `X-API-Key-ID`, and their keys come from `app.gnani.ai/voice`.
  The Platform API key comes from *"Agent Builder → Settings → API Keys"*, per the Postman header description. Neither the docs nor the hackathon emails give the console URL.
  The backend branding is **Inya** (`api.inya.ai`, `inya_data`, `hello-inya@gnani.site`, the `INYA_TRANSCRIPT` widget), so Agent Builder is very likely the former **Inya.ai** product *(inferred)*.
- **No Evon anywhere.** The word "Evon" appears **0 times** in the entire 17.8k-line docs dump. The platform's LLM list shows Gnani **"Pampa Go"** and **"Pampa Priority"**, plus Anthropic `claude-3-5-sonnet-20241022` and OpenAI `gpt-4.1-mini` / `gpt-4o-mini`.
  ASR and TTS appear as Gnani **"Vachana"** models and a TTS provider id **`vachana_timbre-v2.5`**. The name "Prisma" never appears in the Agent Builder section.
- **Real phone calls work out of the box, but only outbound to numbers you have whitelisted** (OTP-verified in the UI). The API version of Trigger Call says *"contact your account manager to register numbers"*.
  Inbound numbers mean importing your own Twilio numbers. Promotion to Production and "deployment to live infrastructure" are **done by the Gnani team on request**.
- **Big unknowns for the hackathon:**
  1. Does the 5,000-credit account include an Agent Builder login and Platform API key?
  2. What does a call minute cost?
  3. Will judges accept "Pampa" and "Vachana" as "Gnani models used"?

  **Ask on Discord before investing time.**

---

## 1. What Agent Builder is, and its concepts

Sources: <https://docs.gnani.ai/introduction>, <https://docs.gnani.ai/A02_Agent>, <https://docs.gnani.ai/M05_Chains>, <https://docs.gnani.ai/creating-a-workforce>, <https://docs.gnani.ai/F02_Org>, <https://docs.gnani.ai/F03_Env>

> "Agent Builder is the console for creating voice agents that handle customer calls … without writing application code for the core flow."

| Concept | What it is | Where (console path) |
|---|---|---|
| **Knowledge Base (KB)** | Uploaded PDF, DOC/DOCX, XLS/XLSX, CSV or TXT files, or a public URL crawled **one level deep**. After "Start Training" you can link it to any agent. **Test Knowledge** previews answers. | Knowledge Base → Add Knowledge Base |
| **FAQ KB** (API only) | Up to **100 Q&A pairs per agent per environment**, each with up to 10 phrasings and a `language`. They are **matched before the LLM answers**. | `/v1/agents/{botId}/faqs` |
| **Agent** | System prompt, greeting and ending message, LLM provider/model, temperature, max tokens, linked KB, languages (max 3), region, timezone, ASR, TTS voice, plus **Customize** settings: DTMF, Advanced ASR, voicemail detection, pre-call variables. Built from scratch or from a template. | Manage Agents → Create Agent |
| **Integrations** | Credentials for Twilio SMS, Zoho CRM, Mailchimp or SendGrid email, Zoho Desk tickets, Webex CC, or a **Custom HTTP** endpoint (method, URL, auth header). | Manage Agents → agent → Integration tab |
| **Actions** | A named trigger that uses an integration. **On-Call** actions run mid-conversation: the agent speaks a "Speak During Action" line, with *Before-API* variables sent and *After-API* variables received. **Post-Call** actions run after hang-up. The LLM decides when to fire based on the action **Description**, so this is effectively tool calling *(inferred)*. Every execution is logged. | Agent → Action tab |
| **Variables** | Typed placeholders (Boolean, Integer, Float or String), each with a "prompt" saying how to fill it from the user, e.g. "Ask for 6-digit PIN". | Action tab |
| **Pre-call / dynamic variables** | `{{var}}` placeholders resolved **before** the call from your **Dynamic Messages API**, or entered manually in tests. | Customize → Pre-Call Variables / Dynamic Variables |
| **Agent Chains** (older flow builder) | A visual canvas with **Default** (speak/prompt), **User** (capture input), **Decision** (branch by condition, retry count, KB) and **Event** (End Call, Reset, Transfer) nodes. Connection rules: Default→User; User→Decision/Default/Event; Decision→Default/Event; Event is terminal. Create from scratch, **from a prompt** (auto-generated flow), or from a JSON import. Global prompt, KB, LLM, ASR and TTS are set per chain. | Agent Chains → + |
| **Workforce** (newer multi-agent) | A canvas of linked agent nodes from your library, joined by edges carrying **natural-language handoff conditions** ("User wants to cancel"). The full transcript, extracted data and session context pass on handoff. **Every workforce currently starts from an Outbound Call Trigger.** | Build → Workforce |
| **Dispositions** | A post-call LLM classification of the outcome (a default prompt plus named dispositions, each with a condition prompt). The result shows in Analytics, Logs, the Stats API (`overallCallDisposition`) and the webhook (`STAGE_CODE`, `disposition_result`). | Agent → Analytics Config tab |
| **Environments** | Development → Staging → Production, strictly linear. Each step **overwrites** the next, with no versioning or rollback. Only available inside Organizations. | — |
| **Organizations** | A shared workspace with Org Admin, Developer and QA roles. Agents are private-by-default memberships. **Orgs are created only by Gnani on request.** Everyone also has a **Personal workspace**, and agents cannot be moved between workspaces. | — |
| **Logs and analytics** | Conversational Logs (recording, transcript, latency, call insights), **Dev Logs** (per-module events tagged CALL, ORCH, TTS, ASR/TRANSCRIBE, LLM, KB, BARGE, ERROR, useful for latency debugging), Agent Analytics (sentiment trend, intents, topics, dispositions, drop-off), Action Logs, and an account-wide Dashboard. | — |

### End-to-end flow to a working voice agent (console)
Sources: <https://docs.gnani.ai/introduction>, <https://docs.gnani.ai/A03_Testing>, <https://docs.gnani.ai/A04_Whitelisting>

1. **Knowledge Base** → upload documents or a URL → Start Training → Test Knowledge.
2. **Manage Agents → Create Agent**, from scratch or a template. Then set:
   - the system prompt, greeting and end message;
   - LLM, temperature and max tokens;
   - the linked KB;
   - in **Customize**: languages, region, timezone, ASR, TTS voice, DTMF, Advanced ASR, voicemail detection and pre-call variables.
3. **Test** in three ways:
   - (a) **Chat Window**;
   - (b) **Web-based (Voice)**: talk in the browser. **"Generate Shareable Link" gives a no-login link that is valid for only 5 minutes.**
   - (c) **Trigger Agent Call**: a real phone call to a whitelisted number.
4. **Phone Numbers → Whitelisted → Add Number**, then verify by OTP. The number then appears in the test-call dropdown.
5. Optionally add Integrations and Actions, dispositions (Analytics Config), and a post-call webhook (API).
6. Review in Conversational Logs, Dev Logs and Analytics.
7. "Go live": inside an Org you promote the agent to **Production**, then **contact the Gnani team to deploy**. Deployment is not self-serve.

---

## 2. Model, ASR and TTS providers exposed by the platform

Sources: <https://docs.gnani.ai/Platform/Get_LLM_Models>, <https://docs.gnani.ai/Platform/Get_Transcriber_Config>, <https://docs.gnani.ai/Platform/Get_TTS_Config>, <https://docs.gnani.ai/Platform/Update_Agent>, <https://docs.gnani.ai/Platform/Get_Agent>

All values below come from the **example responses** in the docs. They are not a live catalogue. The real lists come from the `/config/*` endpoints.

### LLM (`llmParams.provider` / `model`)
| providerId | modelId (label) | functionCalling | supportedLanguages (example) |
|---|---|---|---|
| `gnani` | **`Pampa Go`** (used as the default in Get Agent and Update examples) | true | en-IN, hi-IN, ta-IN, kn-IN, en-US |
| `gnani` | **`Pampa Priority`** | true | same |
| `anthropic` | `claude-3-5-sonnet-20241022` | true | en-IN, hi-IN, ta-IN, kn-IN, en-US |
| `openai` | `gpt-4.1-mini`, `gpt-4o-mini` | true | en-IN, hi-IN, en-US |

- **Evon is not listed** in any example, and the string "Evon" appears nowhere in the docs. "Pampa" is presumably Gnani's in-house LLM line, and whether Pampa is the same as or related to Evon v3.3 is **unknown** *(inferred: probably a different, hosted product name)*.
- Agent defaults: temperature `0.5`, max tokens `300`, range 1–4096. Dev Logs mention errors "from OpenAI or other APIs".

### ASR / transcriber (`asrParams`)
| providerId | modelIds seen | Notes |
|---|---|---|
| `gnani` (description: "Purpose-built for Indian languages and accents") | `gnani_vachana_rest` ("Vachana Rest", tier `balanced`), `gnani_v2` ("Vachana", tier `custom`), **`gnani_asr`** (streaming; used in the Get Agent example; supports custom vocabulary and `minWordsForBargeIn`) | Vachana models: hi, en, te, ta, mr, bn, kn, ml (-IN), all multilingual |
| `microsoft` | `microsoft_rest` (balanced), `microsoft_streaming` (responsive), `microsoft_streaming_multilingual` (in the multilingual example) | en-IN, hi-IN, en-US, ta-IN, te-IN |
| `elevenlabs` | `elevenlabs_streaming`, `elevenlabs_rest` (the only model supporting `asrPreemptive` "Fast Streaming") | from the compatibility table |
| `gladia` *(inferred id)* | `gladia_streaming` | compatibility table |
| Google *(inferred)* | `gemini-2.5-flash-native-audio-preview-09-2025` | compatibility table |
| `deepgram` | — | only mentioned as a `providerId` filter example |

- The language-switch prompt talks about **outputs from "multiple STT engines" (S1/S2/S3)**. Stats responses also return `totalResults` with one transcript per configured language, e.g. `{"en-IN": "how much is my due amount", "hi-IN": "हाउ मच इज़ माइ ड्यू अमाउंट"}`.
  So the platform appears to run **parallel per-language ASR** and pick between the results *(inferred)*.
- "Prisma v2.5" (the hackathon STT, called as `gnani-prisma-v2.5` on `api.vachana.ai`) is **not named** in Agent Builder. The Gnani ASR here is called "Vachana", which is likely the same family or an older rebrand *(inferred, unverified)*.

### TTS (`ttsParams`)
| providerId | model | voices seen |
|---|---|---|
| **`vachana_timbre-v2.5`** (label "Gnani") | `vachana-voice-v1-standard-streaming` ("Gnani Vachana"), supporting en-IN, hi-IN, kn-IN, ta-IN, te-IN | **Pranav** (male, en/hi, multilingual), **Shubhra** (female, en/hi). **Nalini** appears in the multilingual Update example. |

- **Inconsistency:** Get TTS Config returns `providerId: "vachana_timbre-v2.5"`, but the Get Agent and Update Agent examples send `"provider": "gnani"`. Check against the live `/config/tts_config` before relying on either.
- TTS settings: `ttsRate` 0.5–2.0, `enableCaching` (default on).
- The provider id contains **"timbre-v2.5"**, so Agent Builder TTS likely *is* Timbre v2.5, the hackathon TTS *(inferred, strong)*. Only Gnani TTS appears in the examples.

---

## 3. Telephony, regions and languages

Sources: <https://docs.gnani.ai/A04_Whitelisting>, <https://docs.gnani.ai/Platform/Trigger_Call>, <https://docs.gnani.ai/M16x_Import_Number>, <https://docs.gnani.ai/Platform/Get_Regions>, <https://docs.gnani.ai/Platform/Get_Languages>, <https://docs.gnani.ai/Platform/Update_Agent>, <https://docs.gnani.ai/F02_Org>, <https://docs.gnani.ai/B04_Dynamic_Variables>

- **Test calls are outbound only, to whitelisted numbers.**
  - In the UI: Phone Numbers → Whitelisted → Add Number → **OTP verify** → Manage Agents → Test → Trigger Agent Call.
  - Through the API: `POST /v1/agents/{botId}/trigger_call?environment=development` with `{phone, countryCode, name, clientReferenceId?}`.
  - An unregistered number returns **400 "Phone number is not registered for outbound calls"**. The API doc says to *"contact your account manager to register numbers"*, while the UI doc describes self-serve OTP whitelisting.
  - The docs mark this endpoint as *"for testing — not large-scale production campaigns."*
- **Caller ID:** the webhook example shows `srcPhone: "+918035218872"`, a Bangalore (080) number, and `callType: "Outbound"`. So Gnani supplies the Indian outbound line in testing *(inferred)*.
- **Twilio import:** Phone Numbers → Active Numbers → Import. You enter the Twilio Account SID and Auth Token, then multi-select numbers, which can then be assigned to agents "for inbound or outbound calls". This is the only documented self-serve route to an **inbound** number.
- **Production:** "Deployment to live infrastructure is handled by the Gnani Agents team" and is open only to agents in the Production environment.
  - There is **no built-in campaign manager**: Dynamic Messages and campaigns are enabled "only by contacting us".
  - Webex Contact Center integration also needs the Gnani team, which sets up credits.
- **Call transfer:** `callTransferConfig.details[{phoneNumber, countryCode, prompt, message}]` sets transfer-to-human numbers. Chains and Workforce have Transfer events.
- **Voicemail detection** (outbound): 1–5 detection attempts, a 1–10 s playback delay, a message of up to 300 characters (supports `{{vars}}`), and post-detection actions (SMS, email, API).
- **DTMF:** toggle it in Customize, **and** append signals to the prompt text, e.g. `"…phone number after the beep tone? | DTMF1010"`. In `DTMFXXYY`, XX is the number of digits and YY the seconds allowed. `DTMF0610` means a 6-digit PIN with 10 s.
- **Noisy-line controls** (`advanceSettings`):

  | Setting | Value / range |
  |---|---|
  | `useDenoiser` | default true |
  | `suppressionLevel` | 20–100, default 80 |
  | `barge` | interruptions on/off |
  | `initialMessageBarge` | allow interrupting the greeting |
  | `minWordsForBargeIn` | 1–5 (streaming ASR) |
  | `minTimeToBarge` | 0.1–3 s (REST ASR) |
  | `maxSpeechDuration` | 1–240 s, default 30 |
  | `speechInitialSilenceTimeout` | 10–30/60 s |
  | `endSilenceTimeout` | ms, default 800 |
  | `speechSegmentationSilenceTimeout` | 0.1–5 s |
  | `enableItnForAsr` | inverse text normalization |
  | `phraseConfig.phrase` | ≤100 custom-vocabulary phrases, weight 0–2; only `gnani_asr`, `microsoft_streaming`, `elevenlabs_*` |

  Sending a field the chosen model does not support returns HTTP 400.
- **Regions:** `asia` (default), `america`, `europe`. **Timezones** per region, e.g. `Asia/Kolkata` (default), `Asia/Singapore`, `Asia/Tokyo`, `Asia/Dubai`, `Asia/Bangkok`.
- **Languages** (Get Languages example): `en-IN`, `hi-IN`, `ta-IN`, `te-IN`, `kn-IN`. Each has allowed **pairs**:

  | Language | Allowed pairs |
  |---|---|
  | en-IN | hi, kn, ta, te |
  | hi-IN | en, kn, ta |
  | ta-IN, te-IN, kn-IN | hi, en |

  Vachana ASR also lists mr-IN, bn-IN and ml-IN. **At most 3 languages per agent.** ASR, TTS and voice must support *all* configured languages, or the call returns 400.
- **Language switching:** `languageSwitch` (bool), `languageSwitchMode: "implicit" | "explicit"`, `explicitLanguageSwitch`, and `minWordsForLangSwitch` (≥1, default 2).
  The "Language Switch Prompt" (Overview tab) must list every configured language, or switching **silently fails**.

---

## 4. Platform API reference

Sources: <https://docs.gnani.ai/Platform/platform-introduction>, <https://docs.gnani.ai/Platform/Error_Reference>, plus each endpoint page linked below.

- **Base URL:** `https://api.inya.ai/platform`, HTTPS only.
- **Auth:** `x-api-key: <key>` on every request, plus `Content-Type: application/json` and `Accept: application/json`, as in the Postman collection.
  - Key scopes: **`agents`** covers `/v1/agents/*` and **`conversations`** covers `/v1/conversations/*`.
  - A bad key returns 401. A valid key without the right scope returns 403.
  - The QA role cannot create or update (403).
- **Envelope:** `{"status":"success"|"failure","requestId":"uuid","message":"…","response":{…}}`. Paginated responses add `pageNo`, `pageSize`, `totalCount` and `totalPages`.
- **Errors:** 400, 401, 403, 404, 409 (duplicate `botName`), **429 rate limit** (no numbers given; back off at 1/2/4 s) and 500. Always log `requestId`.
- **`?environment=development`** is "often required". Developer-role keys get 403 without it on trigger_call and logs.
- **Postman collection:** 25 requests, embedded as base64 on the platform-introduction page. Placeholders are `YOUR_PLATFORM_API_KEY`, `YOUR_BOT_ID`, `YOUR_CONVERSATION_ID` and `YOUR_FAQ_ID`.

### Endpoint table (25 endpoints)
| # | Method | Path | Purpose | Key params / notes |
|---|---|---|---|---|
| 1 | GET | `/v1/agents/config/languages` | Supported languages and allowed pairs | — |
| 2 | GET | `/v1/agents/config/regions` | Regions | → `asia`, `america`, `europe` |
| 3 | GET | `/v1/agents/config/timezone/{regId}` | IANA timezones for a region | 404 "Region not found" |
| 4 | GET | `/v1/agents/config/llm_models` | LLM providers and models | `?provider=gnani\|openai\|anthropic`; an unknown provider returns 200 with an empty list |
| 5 | GET | `/v1/agents/config/transcriber_config` | ASR providers and models for the given languages | **`language` required**, repeatable (`?language=en-IN&language=hi-IN`); `providerId` |
| 6 | GET | `/v1/agents/config/tts_config` | TTS providers, models and voices (gender, demoAudioUrl, accent, tone) | **`language` required**, repeatable; `providerId` |
| 7 | POST | `/v1/agents` | Create an agent and get a `botId` (201) | `botName` (unique, required), `description`, `region`, `timeZone` |
| 8 | GET | `/v1/agents` | List agents | `pageNo` (≥1; **0 returns 500**), `pageSize`, `search` |
| 9 | GET | `/v1/agents/{botId}` | Full config: overview, asr/llm/ttsParams, advanceSettings, preCall, voicemail, transfer, webhook, faqEnabled | `environment` field is always `development` |
| 10 | PUT | `/v1/agents/{botId}` | **Partial update of everything** (prompt, models, languages, advanceSettings, language switch, preCall, voicemail, transfer, **post-call webhook**) | 400 on language or model incompatibility |
| 11 | DELETE | `/v1/agents/{botId}` | Permanent delete | — |
| 12 | POST | `/v1/agents/prompt/validate` | Jinja2 check, extracted `variables`, and a **KV-cache and optimisation score** | body `{systemPrompt}`. Invalid syntax returns **200** with `isValidTemplate:false`. **A missing or misnamed field also returns 200 and "valid"**, so check `variables`. |
| 13 | POST | `/v1/agents/{botId}/trigger_call` | Outbound test call to a whitelisted number | `?environment=development`; body `phone` (no country code), `countryCode` ("+91"), `name`, `clientReferenceId?`. A 200 means the call is *being placed*. |
| 14 | GET | `/v1/agents/faqs/sample` | Sample FAQ JSON | the sample uses `english`, but real calls need BCP-47 codes |
| 15 | POST | `/v1/agents/{botId}/faqs` | Add FAQs; sets `faqEnabled=true` | `botId`, `environment`, `faq[{questions[≤10], answer, language, signal?}]`; over 100 returns 400 |
| 16 | GET | `/v1/agents/{botId}/faqs` | List FAQs with `faqId`s | `?environment=` |
| 17 | PUT | `/v1/agents/{botId}/faqs` | Update one FAQ | `faq.faqId`, plus questions, answer, language |
| 18 | POST | `/v1/agents/{botId}/faqs/import` | Bulk import | **entries beyond 100 are silently trimmed** (`trimmed`, `trimWarning`) |
| 19 | DELETE | `/v1/agents/{botId}/faqs` | Delete FAQs (body `faqIds[]`) | deleting all of them sets `faqEnabled=false` |
| 20 | POST | `/v1/conversations/logs` | Search and list calls to get `conversationId` | query `environment`, `botId`; body `pageNo`, `pageSize`, `searchTerm`, `filter.{startDate,endDate,callStatus,botId}`. The `transcript` here is often empty. |
| 21 | GET | `/v1/conversations/{conversationId}/stats` | `callStatus`, `overallCallDisposition`, `callSummary`, **`utteranceAnalytics`** (full transcript with detectedLanguage, totalResults, userInterruptionFlag), `averageAgentLatency` | `callSummary` is null until analytics finish (retry after 30–60 s) |
| 22 | GET | `/v1/conversations/{conversationId}/audio` | MP3 recording (`audio/mpeg`) | 404 if recording is off or the call was too short. Use GET, since HEAD may return 405. |
| 23 | GET | `/v1/agents/{botId}/chat-sdk-config` | Chat widget config | `?environment=` |
| 24 | PUT | `/v1/agents/{botId}/chat-sdk-config` | Update widget styling, `enabled`, `allowedOrigins` | ORG_ADMIN or DEVELOPER role |
| 25 | POST | `/v1/agents/{botId}/chat-sdk-icon` | Upload the launcher icon (multipart `file`) | JPEG, PNG, GIF, BMP, WebP, TIFF or SVG; returns `fileUrl` |

### Create Agent → Update Agent → Trigger Call (key examples)
```bash
# 1. create (201) -> response.botId
curl -X POST https://api.inya.ai/platform/v1/agents -H "x-api-key: $KEY" -H "Content-Type: application/json" \
  -d '{"botName":"Support Agent","description":"Handles inbound customer support calls.","region":"asia","timeZone":"Asia/Kolkata"}'
# -> {"status":"success","message":"Agent created successfully.","response":{"botId":"fb79…0275","botName":"Support Agent"},"requestId":"…"}
# New agents default to: barge-in on, TTS caching on, temperature 0.5, maxTokens 300.

# 2. configure (all fields optional; condensed from the docs' "full configuration" example)
curl -X PUT https://api.inya.ai/platform/v1/agents/$BOT -H "x-api-key: $KEY" -H "Content-Type: application/json" -d '{
  "greetingMessage":"Hello, how can I help you today?","endMessage":"Thank you. Have a great day!",
  "systemPrompt":"You are a helpful support agent for {{company_name}}.",
  "botDetails":{"language":["en-IN","hi-IN"],"region":"asia","timeZone":"Asia/Kolkata"},
  "asrParams":{"provider":"gnani","model":"gnani_vachana_rest","language":"en-IN"},
  "llmParams":{"provider":"gnani","model":"Pampa Go","temperature":0.7,"maxTokens":400},
  "ttsParams":{"provider":"gnani","voice":"Pranav","language":"en-IN","ttsRate":1.2,"enableCaching":true},
  "advanceSettings":{"barge":true,"useDenoiser":true,"suppressionLevel":80,"maxSpeechDuration":15,"endSilenceTimeout":800,"enableDtmf":false},
  "languageSwitch":true,"languageSwitchMode":"explicit","minWordsForLangSwitch":2,
  "preCall":{"preCallVariableStatus":true,"preCallParams":{"primaryVariable":"customer_name",
     "variables":[{"variable":"customer_name","sampleValue":"Alice","description":"Customer name"}]}},
  "hasPostCallTrigger":true,
  "postCallTriggerAPIConfig":{"hasHeaders":true,"method":"POST","url":"https://your-server.example.com/call-completed",
     "headers":[{"id":"1","key":"Authorization","value":"Bearer your-token"}]}
}'

# 3. test call (whitelisted number only)
curl -X POST "https://api.inya.ai/platform/v1/agents/$BOT/trigger_call?environment=development" \
  -H "x-api-key: $KEY" -H "Content-Type: application/json" \
  -d '{"phone":"9876543210","countryCode":"+91","name":"Jane Doe","clientReferenceId":"crm-lead-42"}'
# -> {"status":"success","message":"Call is being triggered to 9876543210","response":{"clientReferenceId":"crm-lead-42"},"requestId":"…"}
# Errors: 403 "Developer can only trigger calls in the development environment"; 400 "Phone number is not registered for outbound calls";
#         400 "Phone number provided is Invalid"; 400 "Please check your dynamic greeting message API or precall/dynamic variables…"
```

### Post-call webhook (snake_case payload) and outcome fields
- Set `hasPostCallTrigger: true` and `postCallTriggerAPIConfig` (GET or POST, URL, headers). The platform POSTs when each call ends.
  It **may deliver more than once**, so key your handler on `conversation_id`. Return 2xx fast.
- Payload keys:
  - identity: `conversation_id`, `bot_id`, `bot_name`, `bot_type` (`voice_outbound`/`voice_inbound`), `bot_language(s)`, `environment`, `call_type`, `flow_id`, `organization_id`;
  - caller: `phone`, `phone_number`, `user_context`;
  - outcome: `callStatus`, **`STAGE_CODE`**, **`disposition_result`** / `post_call_extraction_v2` (fields come from your disposition prompt, e.g. `DISPOSITION`, `ptp_date`, `clbk_date`, `language_captured`);
  - conversation: `transcript[]` / `conversation_log[]`, where user turns carry `detected_language`, `total_results` and `user_interruption_flag`;
  - telephony: `call_infra.call_status` (CDR: `srcPhone`, `dstPhone`, `ringingTime`, `setupTime`, `gnanivb_billing_duration`, timestamps, `rec_path`).
- Standard `overallCallDisposition` codes: `PTP` (promise to pay), `RTP` (refused to pay), `AP` (already paid), `CLBK` (callback), `WRNG` (wrong number), `DSCN` (disconnected), `RNR` (no answer), `DND`.
  The examples are all debt-collection (Muthoot), and custom codes are allowed.

---

## 5. Prompt patterns worth reusing

Sources: <https://docs.gnani.ai/C03_Jinja>, <https://docs.gnani.ai/M10_Dynamic_Variables>, <https://docs.gnani.ai/B04_Dynamic_Variables>, <https://docs.gnani.ai/C02_Language_Switch>, <https://docs.gnani.ai/C01_Disposition>, <https://docs.gnani.ai/B01_DTMF>, <https://docs.gnani.ai/Platform/Validate_Prompt>

**Jinja system prompt.** It is validated on save. Bad syntax disables Save and Test. An undeclared variable at runtime gives "Call triggered failed."
```jinja
Hello {{ customer_name }}.
{% if loyalty_status == 'Gold' %}As a Gold member, you get a special 20% discount.
{% elif loyalty_status == 'Silver' %}As a Silver member, you get a 10% discount.
{% else %}Thank you for being our customer.{% endif %}
Your order #{{ order_id }} is ready.
```
- Conditionals **cut input tokens, cost and latency**. Validate Prompt also returns a `kvCache` score.
  Tip from the docs: put per-call content (names and so on) **at the end** of the prompt to maximise KV-cache reuse.
- The docs describe two variable sources:
  - **server-side** variables come from the Dynamic API or pre-call variables, and are required;
  - **user-input** variables are filled from the caller's utterance.

  The brace syntax that tells the two apart is stripped from **both** the export and the live `C03_Jinja.md` (checked 2026-10-04). It is probably `{{x}}` for server-side and single braces `{x}` for user-input *(inferred)*. Test this in the console before relying on it.
- In tests, a pre-call variable beats the Dynamic API value when both exist.

**Dynamic Messages API.** Your endpoint, called before every call (10-second timeout; on timeout the call fails). The platform sends `{"conversation_id":"abc123","mobile":"01234567890"}` (plus `clientReferenceId` if given). You return HTTP 200 to place the call or 400 to block it:
```json
{"additional_info":{"inya_data":{
  "text":"Hi John Doe, your payment of ₹2500 is due on 2025-08-20.",
  "user_context":{"name":"John Doe","due_amount":"2500","due_date":"2025-08-20"}}}}
```
`text` overrides the greeting. `user_context` fills `{{vars}}` in the system prompt.

**Language-switch prompt.** This is an intent detector over three STT hypotheses, and its output is *only* the target language name or `None`:
```
## Input Format: S1/S2/S3 = Engine 1/2/3 output (any script)
## Output: ONLY the target language name, or "None"
Phrases: EN "switch to [lang]", "let's talk in [lang]"; HI "भाषा बदलें [lang]", "चलो [lang] में बात करें"
Valid targets: English, Hindi, Kannada ...
Example: S1 "ಮುಂದೆ ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡೋಣ" / S2 "let's speak in Kannada" / S3 "ನಾವು ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡೋಣ" -> Kannada
Conflicts -> the language most consistent across engines. Use REAL ASR outputs as examples, not translations.
```

**Disposition prompt skeleton** (post-call, JSON-only), with these sections in order:
1. `## Role` (analyst in {{Industry}}; transcripts may be in {SUPPORTED_LANGUAGES} "or mixed language");
2. `## IMPORTANT` (strict JSON, no extra keys);
3. `## Task`;
4. Context, Business and Language guidelines;
5. `### Field Definitions` (`{"STAGE_CODE": ""}`);
6. `### Allowed Values & Definitions`, a list of `{code, description, criteria}` in priority order (ESCALATED_TO_AGENT, AGREES_FOR_CALLBACK, BUSY, FAQ_HANDLED, NO_INPUT, INVALID_INPUT, WRONG_NUMBER, DND, …);
7. critical-analysis rules ("read ENTIRE transcript", "don't assume agreement from silence");
8. the output example;
9. `## Transcription <transcription>`.

**DTMF in-prompt signal:** `"Please enter your 6-digit pin after the beep. | DTMF0610"`. The docs suggest DTMF as a fallback **in noisy environments**, which matters for the hackathon's noisy-telephony award.

---

## 6. Chat widget (Chat SDK)

Sources: <https://docs.gnani.ai/Platform/Get_Chat_SDK_Config>, <https://docs.gnani.ai/Platform/Update_Chat_SDK_Config>, <https://docs.gnani.ai/Platform/Upload_Chat_SDK_Icon>, <https://docs.gnani.ai/D06_Webex>

- Per-agent and per-environment `chatSdkConfig` fields:
  - `enabled` and `allowedOrigins[]` (the CORS whitelist of domains allowed to embed it);
  - `windowCustomizations` for header (title, subtitle, logo, colours), body, userMessage, botMessage and footer (`infoText` defaults to "Powered by Gnani"; also input placeholder and border, and send-button colours);
  - `widgetCustomizations.buttonStyles` (launcher colour, width, height);
  - `quickActions`, `callTransfer` and `clearChat`, which are null when not configured.
- **The embed snippet (`<script>` tag, loader URL, botId attribute) is not documented anywhere in the dump.** The console probably shows it *(inferred)*.
  It is a **text chat** widget. The docs show no browser *voice* widget beyond the 5-minute shareable test link.
- The only script URL in the docs is the Webex desktop widget, `https://genvoice-appdev.gnani.site/sdk/inya/inya-webex-widget.min.js`, which is Webex-specific.

---

## 7. Is this usable for the hackathon?

Context: the contest requires naming the Gnani models and APIs used. Awards cover regional languages, Hinglish and code-mixed speech, noisy telephony, real-world impact, creativity, the best 60-second demo and Crowd Favourite.
The email lists resources as *"5,000 programme credits to use on Gnani AI's APIs"* through the **"API dashboard"** (app.gnani.ai), with models Prisma, Timbre and Evon ("available on hugging face"). See `notes/01-hackathon-overview.md`.

### What is unclear (ask on Discord or email before building on it)
1. **Access.** The hackathon pack points to `app.gnani.ai/voice` and Speech API keys (`api.vachana.ai`). Agent Builder lives on a **different backend (`api.inya.ai`)** with its own key from "Agent Builder → Settings → API Keys", and the docs give **no console URL or sign-up path**.
   It is unknown whether a hackathon account can log in, and whether the **5,000 credits are spendable there**.
2. **Cost.** The docs give no pricing. Agent Builder is clearly credit-metered: Dev Logs show "ORCH: Finalizing total call credits", Webex setup involves "purchasing and allocating required credits", and the CDR has `gnanivb_billing_duration`.
   The cost per call minute and per LLM token is unknown.
3. **Model naming.** The platform shows **Pampa Go / Pampa Priority** (not Evon), **Vachana** ASR (not "Prisma") and the **`vachana_timbre-v2.5`** TTS provider.
   Is Vachana ASR = Prisma v2.5? Is Pampa related to Evon? Can Evon be selected? None of this is answered.
4. **Phone limits.** Outbound only, to OTP-whitelisted numbers. The API doc says the account manager registers numbers. Are there call quotas for students? An inbound number needs Twilio import or a Gnani-run deployment.
5. **Public demo.** The browser voice test link lasts **5 minutes**, which is fine for a recorded video but useless as a persistent public demo. The chat widget is text-only and its embed snippet is undocumented.
6. **Rate limits** exist (429) but are unspecified.

### Pros vs building on the raw STT/TTS APIs
| Agent Builder / Platform API | Raw Prisma STT + Timbre TTS (+ an LLM you host or call) |
|---|---|
| ✅ **A real PSTN call to your own phone in an afternoon**: Indian caller ID, recording, transcript and latency, with no SIP or Twilio plumbing | ❌ You have to build telephony yourself (Twilio or Exotel, media streams, μ-law resampling) or demo only in the browser |
| ✅ Production-grade loop out of the box: barge-in, denoiser and suppression, endpointing, DTMF, voicemail detection, call transfer, multi-engine language switch, per-language `totalResults` | ❌ You build VAD, barge-in, turn-taking and code-switch handling yourself (more engineering, but also more to show off) |
| ✅ Dispositions, analytics, Dev Logs latency, post-call webhook into your backend, and Custom API actions mid-call. Your own logic can still run via webhooks and actions. | ✅ Full control. You can do novel things in the audio and turn loop (repair strategies, confidence gating, custom code-mix handling), which is where creativity points come from |
| ❌ Uncertain access and cost. Possibly not covered by the credits. | ✅ Definitely covered by the 5,000 credits and the documented hackathon path |
| ❌ The LLM is Pampa, Claude or GPT. **Evon cannot be selected**, and judges may read Claude or GPT as "not Gnani". | ✅ You can name Prisma v2.5 and Timbre v2.5 exactly, plus Evon v3.3 if you can host it. Evon needs a GPU (the user's laptop has none; see memory `dev-machine-hardware`) or a hosted endpoint. |
| ❌ Looks like "configured a SaaS bot". The individual interview will probe engineering depth, and judges may score creativity low. | ✅ The code is yours to explain in the interview and to show in the 60-second demo |
| ❌ Platform has rough edges: no versioning, Orgs and deploys need Gnani staff, the docs' TTS provider id is inconsistent, and Validate Prompt returns "valid" on a missing field | — |

### What a judge might think *(inferred)*
- A **phone-call demo on a real noisy line, in Hinglish or a regional language, with live language switching**, is exactly what the noisy-telephony, code-mixed and regional-language awards describe. Agent Builder makes that *demo* easy. Gnani staff presumably know their own product and may like seeing it used well.
- But if the whole submission is "a prompt in Agent Builder", it is hard to stand out against 400+ entrants on **creativity** or **engineering**. The required "models/APIs used" field would read "Agent Builder (Pampa Go, Vachana, Timbre)", which does not cleanly match the advertised Prisma, Timbre and Evon trio.
- The strongest framing *(inferred)*: build the **core idea on the raw Speech APIs** (Prisma streaming STT plus Timbre TTS, so the novel logic is visible and attributable). Optionally use Agent Builder as the **telephony front end or baseline**:
  - for example, an Agent Builder agent whose **On-Call Custom API actions and post-call webhook call your service**, which does the novel work (verification, repair, regional knowledge, Evon reasoning);
  - or as an A/B baseline in the write-up ("our pipeline vs the stock Agent Builder agent on the same noisy calls").
- If you use it, name it explicitly in the submission ("Gnani Agent Builder Platform API: Vachana ASR, Timbre v2.5 TTS, Pampa Go LLM"), and keep the LLM on Gnani's (Pampa) or Evon, never Claude or GPT.

### Questions to post on Discord (one message)
1. Do hackathon accounts get **Agent Builder** (Inya) console access and a Platform API key, and do the 5,000 credits apply there? What is the console URL?
2. What does one call minute and one Pampa token cost in programme credits?
3. Is Agent Builder's "Vachana" ASR the same as Prisma v2.5, and is "Pampa" related to Evon v3.3? Can Evon be selected as the agent LLM?
4. Can students whitelist their own +91 numbers for test calls by self-serve OTP, and is there a daily call cap?
