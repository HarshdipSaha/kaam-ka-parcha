# Effort 012 — deploy-ready (2026-10-07)

**State:** complete (repo side). Public deployment itself is a user step.

## Scope
Containerise the app so only "press deploy" and the owner's own recordings remain.

## Delivered
- `Dockerfile` (python 3.12-slim + FFmpeg, single uvicorn worker, `/health` check), `.dockerignore`, `docker-compose.yml`, `render.yaml`, `docs/deploy.md`.
- Verified 2026-10-07: `docker build` succeeds; container serves `/health`, `/workshop`, `/stage` (HTTP 200) with `.env` passed at runtime; FFmpeg 7.1 and the packaged noise asset are present. Secrets are not baked into the image (`.dockerignore` excludes `.env`).
- Sessions are in memory: run one instance; a restart loses them.

## Remaining (user)
Deploy to an HTTPS host; record the 80 owner takes (`docs/owner-recording.md`); human listening labels; Task 0 console/permission records.
