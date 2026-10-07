# Deploying Kaam ka Parcha

The app is one FastAPI process with an **in-memory** session store, so deploy **one instance, one worker**;
a restart loses sessions (fine for a demo). Browsers only allow the microphone on **HTTPS** (or localhost),
so use a host that terminates TLS.

## Required settings (platform environment, never committed)
`API_KEY` (Gnani Prisma/Timbre), `EXTRACTOR_BASE_URL`, `EXTRACTOR_API_KEY`, `EXTRACTOR_MODEL`,
`EXTRACTOR_PROVIDER` (`evon` only if the served model is Gnani Evon; otherwise `openai`). `TTS_VOICE` defaults to `Vikrant` (the measured read-back leader).
See `.env.example` for the rest. FFmpeg must be present; the Dockerfile installs it.

## Render (blueprint in `render.yaml`)
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
