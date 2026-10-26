# Deploying Kaam ka Parcha

The app is one FastAPI process with an **in-memory** session store, so deploy **one instance, one worker**;
a restart loses sessions (fine for a demo). Browsers only allow the microphone on **HTTPS** (or localhost),
so use a host that terminates TLS.

## Required settings (platform environment, never committed)
`API_KEY` (Gnani Prisma/Timbre; several keys may be given separated by commas: a key the API refuses with 401/403, which includes spent credits, is retired for the life of the process and the next one takes over; restart or redeploy to try retired keys again), `EXTRACTOR_BASE_URL`, `EXTRACTOR_API_KEY`, `EXTRACTOR_MODEL`,
`EXTRACTOR_PROVIDER` (`evon` only if the served model is Gnani Evon; otherwise `openai`). `TTS_VOICE` defaults to `Vikrant` (the measured read-back leader).
See `.env.example` for the rest. FFmpeg must be present; the Dockerfile installs it.

## Render (blueprint in `render.yaml`; free plan by default, switch `plan: starter` for an always-on demo)
1. Push to GitHub, then Render → New → Blueprint → pick the repo.
2. Fill the four `sync: false` secrets in the dashboard.
3. Wait for `/health` to go green, then open `https://<service>.onrender.com/stage`.

## Any Docker host (build and run verified 2026-10-07)
```
docker compose up --build        # uses .env locally, http://localhost:8000/stage
# or: docker build -t kaam-ka-parcha . && docker run -p 8000:8000 --env-file .env kaam-ka-parcha
```
The image never contains `.env`; pass secrets at run time or in the platform dashboard.

## Before you demo
- Open `/stage` on the final URL once and grant the microphone.
- Use a **new session** per run (reload `/stage`). The page discloses the simulated phone line; keep it visible.
- Keep demo data synthetic: no real customer names, numbers or plates.
- The extractor must be reachable from the host; `EXTRACTOR_BASE_URL=http://localhost:8080/v1` only works locally.

## Abuse protection (public URL)
A public URL lets anyone spend your Prisma/Timbre credits, so the app ships with guards (`src/parcha/guard.py`), all off
locally and set in `render.yaml`:

| Setting | Effect |
|---|---|
| `RATE_LIMIT_PER_MINUTE` | Per-client cap on session creation and every credit-spending POST (intake, re-ask, read-back, reply, fallback, consent); excess gets HTTP 429 with `Retry-After`, before any speech call. |
| `SESSIONS_PER_IP_PER_HOUR` | Per-client cap on new sessions. |
| `MAX_TOTAL_SESSIONS` | Hard cap on live sessions (oldest untouched draft is evicted; otherwise HTTP 503). |
| `MAX_UPLOAD_BYTES` | Upload cap (default 8 MB, HTTP 413). Recordings sent to Prisma are also refused at about 30 s (HTTP 422), because Prisma's REST endpoint rejects clips that long. |
| `MAX_SPEECH_CALLS_PER_DAY` | App-wide cap on credit-spending POSTs over a rolling 24 h, shared by every client (HTTP 503 with `Retry-After` when reached). Counted per request, not per credit: choose it from your balance and the per-call rates in `docs/gates.md`. Session creation is not counted. |
| `AUDIO_CLEANUP` | `1` adds a high-pass and denoise step before Prisma. Off by default until measured. |
| `PARCHA_MOCK` | `1` swaps in scripted speech services for a keyless demo (`src/parcha/mock.py`). Never set it on the public deployment. |
| `DEMO_ACCESS_CODE` | Optional. When set, everything except `/health` needs the code entered once at `/gate` (cookie). |
| `TRUST_PROXY=1` | Behind a single trusted proxy, key limits by the rightmost `X-Forwarded-For` entry. |

Unexpected server errors return a generic body; details are logged server-side only.

## Real customer phone call (Twilio, optional)

**Owner-confirmed working, 2026-10-26:** the deployed project is at https://kaam-ka-parcha.onrender.com/stage and the owner reports the real Twilio call path works. Preserve this distinction in future demos: `/stage` is the browser simulation; an actual Twilio call is a separate channel. A Playwright smoke check of the deployed page on that date passed without placing a call, so it is not independent call-completion evidence.

`src/parcha/telephony.py` adds a second leg alongside the in-browser simulated line: an actual phone call to the
customer, placed through Twilio's REST API, with plain TwiML webhooks (no Twilio SDK dependency).

1. Create a Twilio account (free trial: $15 credit, no card, calls only to verified numbers — add your own number
   under Phone Numbers -> Verified Caller IDs). Buy a trial phone number.
2. Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` (the Twilio number, E.164) and
   `PUBLIC_BASE_URL` (this service's own `https://...onrender.com` URL) in the platform environment.
3. From the workshop, once the card is ready for read-back:
   `POST /sessions/{id}/telephony/call` with `expected_revision`, `to_number` (E.164) and optional `language`.
   Twilio calls `to_number`, plays the read-back, records the reply, and the call follows the same
   confirm/correct/retry/fallback logic as the browser leg — `<Redirect>` back to a fresh read-back after a
   correction, another `<Record>` on an ambiguous or unclear reply, `<Hangup/>` once confirmed or on fallback.
4. Every Twilio webhook (`/telephony/twilio/voice`, `/telephony/twilio/recording`, `/telephony/twilio/status`) is
   signature-checked (`X-Twilio-Signature`, verified against Twilio's own published algorithm and test vector) and
   is exempt from `DEMO_ACCESS_CODE` (Twilio can't carry that cookie); an unsigned or tampered request gets a 403.
5. A real call already passes through a real phone codec, so `start_readback`/`reply` skip the simulated
   noise+codec degradation for this leg (`degrade=False`) — that layer is for the in-browser line only.
6. Trial-account limits apply: only verified numbers, a prefixed "trial account" announcement, 30-day expiry.
   Say so plainly if you demo with this; it is real telephone audio, not simulated. On a trial account, that
   announcement needs an actual on-screen keypad tap to continue into the app — a phone's side button does
   nothing, and nothing registering just ends the call before ever reaching our webhook (confirmed 2026-10-07).
7. No UI button yet — call the endpoint directly (curl, Postman, or the browser devtools) until one is added.
8. On `confirmed`, the app sends the customer a one-line SMS with the verify link (`telephony.send_sms`, no
   Twilio SDK): `Kaam ka Parcha #<no> confirm ho gaya. Kul ₹<amount>. Parcha: <PUBLIC_BASE_URL>/verify/<id>`.
   Costs roughly $0.08/message to India, billed from the same account/credit as the call; trial accounts can
   only send to a verified number, with Twilio's own "Sent from a Twilio trial account" prefix added. A failed
   send is logged and never breaks the call — the customer still hears the spoken confirmation either way.

## Live captions (display only)
While the mechanic records, the workshop page streams the microphone (8 kHz PCM16) to `WS /sessions/{id}/captions`, which relays it
to Gnani's realtime STT and sends the transcripts back. Captions are shown in a dashed "display only" panel and never reach the card:
amounts still come from the two REST Prisma passes over the finished recording (`tests/test_captions.py` proves a caption cannot
create a card, log or amount). The socket honours `DEMO_ACCESS_CODE`, the per-client rate limit, the daily cap and a 60 s stream cap. Realtime STT emits
a transcript per speech segment (after a short pause); Interim text is requested by default through an undocumented header (`x-partials`; a live probe on 2026-10-07 showed a partial about every 0.6 s and a `final_transcript` at the end); set `CAPTION_PARTIALS=0` for per-segment finals only.
Every browser or upstream failure is silent: recording works without captions.
