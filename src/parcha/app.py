from dataclasses import dataclass
import json
import logging
import math
from datetime import datetime, timezone
from pathlib import Path
import re
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request, Query, Response, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .captions import relay_captions
from .config import Settings
from .guard import ACCESS_COOKIE, SlidingWindow, access_ok, access_token, client_ip, is_guarded
from .session import CapacityError, Conflict, SessionStore
from .workflow import NothingToConfirm, RepeatRequest, Workflow
from .audio import AudioError, normalize_upload
from .extract import ExtractionError, Extractor
from .gnani import PrismaClient, TimbreClient, GnaniError
from .presentation import latest_log_text, parcha_no, register_filters, status_label
from .schema import TranscriptLog, review_fields
from .artefact import audit_manifest_sha256, render_pdf, whatsapp_text
from .vocabulary import AUTOMOTIVE_BIAS_WORDS

ROOT = Path(__file__).parent
log = logging.getLogger("parcha")


@dataclass
class AppServices:
    settings: Settings
    store: SessionStore
    workflow: Workflow
    timbre: TimbreClient | None = None
    caption_connect: object | None = None   # websocket opener for live captions; tests inject a fake


def default_services() -> AppServices:
    settings = Settings.load()
    store = SessionStore(max_total=settings.max_total_sessions)
    prisma = PrismaClient(settings.api_key, base_url=settings.gnani_base_url)
    extractor = Extractor(
        settings.extractor_base_url,
        settings.extractor_api_key,
        settings.extractor_model,
        provider=settings.extractor_provider,
    )
    timbre = TimbreClient(
        settings.api_key,
        voice=settings.tts_voice,
        base_url=settings.gnani_base_url,
    )
    try:
        noise_wav = normalize_upload(
            settings.telephony_noise_path.read_bytes(), "audio/wav", sample_rate=8000
        )
    except (OSError, AudioError) as exc:
        raise RuntimeError(
            f"Unable to load telephony noise asset {settings.telephony_noise_path}: {exc}"
        ) from exc
    workflow = Workflow(
        store=store,
        prisma=prisma,
        extractor=extractor,
        normalize_audio=normalize_upload,
        timbre=timbre,
        bias_words=AUTOMOTIVE_BIAS_WORDS,
        use_bias=settings.use_automotive_bias,
        codec=settings.telephony_codec,
        target_snr_db=settings.telephony_target_snr_db,
        noise_wav=noise_wav,
        noise_source="recorded_engine_idle",
    )
    return AppServices(settings, store, workflow, timbre)


def abstention_reasons(session) -> dict[str, str]:
    """Latest abstain reason per field, kept only while that field still needs review."""
    pending = set(review_fields(session.card)) if session.card else set()
    reasons: dict[str, str] = {}
    for log in session.logs:
        if log.mode.startswith("abstain:"):
            reasons[log.mode.removeprefix("abstain:")] = log.text
    return {field: reason for field, reason in reasons.items() if field in pending}


def heard_once(session) -> list[str]:
    """Flagged amounts for which one recording has already been heard (a candidate awaiting its second)."""
    if not session.card:
        return []
    candidates = {ev.field for ev in session.card.evidence if ev.review_score == 0.0 and ev.quote.strip()}
    return [f"items.{it.id}.amount_paise" for it in session.card.items
            if it.amount_paise is None and f"items.{it.id}.amount_paise" in candidates]


def json_safe(value):
    """Non-finite floats (SNR = inf when no noise is mixed) become None, so the body stays valid JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


def session_payload(session) -> dict:
    card = session.card
    return {
        "id": session.id,
        "revision": session.revision,
        "status": session.status,
        "dpdp_consent_granted": session.dpdp_consent_granted,
        "dpdp_consent_at_utc": session.dpdp_consent_at_utc.isoformat() if session.dpdp_consent_at_utc else None,
        "dpdp_consent_sha256": session.dpdp_consent_sha256,
        "card": card.model_dump(mode="json") if card else None,
        "total_paise": card.maybe_total_paise if card else None,
        "review_fields": review_fields(card) if card else [],
        "abstentions": abstention_reasons(session),
        "heard_once": heard_once(session),
        "readback_revision": session.readback_revision,
        "parcha_no": parcha_no(session.id),
        "status_label": status_label(session.status),
        "mechanic_transcript": latest_log_text(session.logs, role="mechanic"),
        "readback_text": latest_log_text(session.logs, role="system", mode="timbre_readback"),
    }


GATE_HTML = (
    "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
    "<title>Demo access</title><form method=post action=/gate style='font-family:system-ui;max-width:20rem;margin:20vh auto;padding:0 16px'>"
    "<h1>Kaam ka Parcha</h1><!--err--><label>Access code<br><input name=code type=password autofocus required style='width:100%;font-size:1rem;padding:.5rem'></label>"
    "<p><button style='font-size:1rem;padding:.5rem 1rem'>Enter</button></p></form>"
)


def create_app(services: AppServices | None = None) -> FastAPI:
    services = services or default_services()
    app = FastAPI(title="Kaam ka Parcha")
    settings = services.settings or Settings()
    rate = SlidingWindow(settings.rate_limit_per_minute, 60.0)
    session_rate = SlidingWindow(settings.sessions_per_ip_per_hour, 3600.0)
    gate_rate = SlidingWindow(10, 60.0)  # access-code guesses per client per minute

    async def read_audio(upload: UploadFile) -> bytes:
        blob = await upload.read(settings.max_upload_bytes + 1)
        if len(blob) > settings.max_upload_bytes:
            raise HTTPException(413, "recording too large")
        return blob

    def refuse(status: int, detail: str, retry_after: float | None = None) -> JSONResponse:
        headers = {"Retry-After": str(max(1, math.ceil(retry_after)))} if retry_after else None
        return JSONResponse({"detail": detail}, status_code=status, headers=headers)

    @app.middleware("http")
    async def public_demo_guards(request: Request, call_next):
        path = request.url.path
        if settings.demo_access_code and path not in ("/health", "/gate") and not path.startswith("/static/"):
            if not access_ok(settings.demo_access_code, request.cookies.get(ACCESS_COOKIE)):
                if request.method == "GET" and "text/html" in request.headers.get("accept", ""):
                    return RedirectResponse("/gate", status_code=303)
                return refuse(401, "access code required")
        if is_guarded(request.method, path):
            ip = client_ip(request.headers, request.client.host if request.client else None, settings.trust_proxy)
            declared = request.headers.get("content-length")
            if declared and declared.isdigit() and int(declared) > settings.max_upload_bytes + 64 * 1024:
                return refuse(413, "recording too large")
            wait = rate.hit(ip)
            if not wait and path == "/sessions":
                wait = session_rate.hit(ip)
            if wait:
                return refuse(429, "Too many requests, please wait a moment and try again", wait)
        return await call_next(request)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        log.exception("unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse({"detail": "internal error"}, status_code=500)

    @app.websocket("/sessions/{session_id}/captions")
    async def captions(ws: WebSocket, session_id: str):
        """Display-only live captions. The HTTP middleware does not see websockets, so the same guards are applied here."""
        try:
            services.store.get(session_id)
        except KeyError:
            await ws.close(code=4404)
            return
        if not access_ok(settings.demo_access_code, ws.cookies.get(ACCESS_COOKIE)):
            await ws.close(code=4401)
            return
        ip = client_ip(ws.headers, ws.client.host if ws.client else None, settings.trust_proxy)
        if rate.hit(ip):
            await ws.close(code=4429)
            return
        try:
            settings.require_gnani()
        except ValueError:
            await ws.close(code=4503)
            return
        await ws.accept()

        async def audio():
            while True:
                message = await ws.receive()
                if message["type"] == "websocket.disconnect":
                    return
                if message.get("bytes"):
                    yield message["bytes"]
                elif message.get("text") == "stop":
                    return

        async def emit(event: dict) -> None:
            try:
                await ws.send_json(event)
            except Exception:  # the browser went away; captions are best-effort
                pass

        options = {"connect": services.caption_connect} if services.caption_connect else {}
        try:
            await relay_captions(audio(), emit, api_key=settings.api_key, partials=settings.caption_partials, **options)
        except Exception:
            log.exception("caption relay failed")
            await emit({"type": "error"})
        try:
            await ws.close()
        except Exception:
            pass

    @app.get("/gate", response_class=HTMLResponse)
    def gate_page():
        return HTMLResponse(GATE_HTML)

    @app.post("/gate")
    def gate_submit(request: Request, code: str = Form("")):
        ip = client_ip(request.headers, request.client.host if request.client else None, settings.trust_proxy)
        if gate_rate.hit(ip):
            return refuse(429, "Too many attempts, wait a minute")
        if not settings.demo_access_code or not access_ok(settings.demo_access_code, access_token(code)):
            return HTMLResponse(GATE_HTML.replace("<!--err-->", "<p>Wrong code.</p>"), status_code=401)
        response = RedirectResponse("/workshop", status_code=303)
        response.set_cookie(ACCESS_COOKIE, access_token(settings.demo_access_code), httponly=True, samesite="lax",
                            secure=(request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"))
        return response

    static_dir = ROOT / "static"
    templates_dir = ROOT / "templates"
    static_dir.mkdir(parents=True, exist_ok=True)
    templates_dir.mkdir(parents=True, exist_ok=True)

    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    templates = Jinja2Templates(directory=templates_dir)
    register_filters(templates.env)

    @app.get("/")
    def index():
        return RedirectResponse("/workshop")

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/workshop", response_class=HTMLResponse)
    def workshop(request: Request):
        return templates.TemplateResponse(request, "workshop.html", {})

    @app.get("/stage", response_class=HTMLResponse)
    def stage(request: Request):
        session = services.store.create()
        return templates.TemplateResponse(request, "stage.html", {"session": session, "parcha_no": parcha_no(session.id)})

    @app.get("/customer/{session_id}", response_class=HTMLResponse)
    def customer_view(request: Request, session_id: str):
        try:
            session = services.store.get(session_id)
        except KeyError:
            raise HTTPException(404, "unknown session")
        return templates.TemplateResponse(
            request,
            "customer.html",
            {
                "session": session,
                "card": session.card,
                "revision": session.revision,
                "readback_revision": session.readback_revision,
                "status": session.status,
                "dpdp_consent_granted": session.dpdp_consent_granted,
                "dpdp_consent_at_utc": session.dpdp_consent_at_utc.isoformat() if session.dpdp_consent_at_utc else None,
                "dpdp_consent_sha256": session.dpdp_consent_sha256,
                "parcha_no": parcha_no(session.id),
                "readback_text": latest_log_text(session.logs, role="system", mode="timbre_readback"),
            },
        )

    @app.post("/sessions")
    def create_session():
        try:
            return session_payload(services.store.create())
        except CapacityError:
            raise HTTPException(503, "demo is at capacity, try again shortly")

    @app.get("/sessions/{session_id}")
    def get_session(session_id: str):
        try:
            return session_payload(services.store.get(session_id))
        except KeyError:
            raise HTTPException(404, "unknown session")

    @app.post("/sessions/{session_id}/consent")
    def record_consent(
        session_id: str,
        request: Request,
        expected_revision: int = Form(...),
        granted: bool = Form(True),
    ):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", session_id):
            raise HTTPException(404, "unknown session")
        try:
            services.store.get(session_id)
        except KeyError:
            raise HTTPException(404, "unknown session")

        now = datetime.now(timezone.utc)
        user_agent = request.headers.get("user-agent")
        try:
            updated = services.store.record_dpdp_consent(
                session_id,
                expected_revision=expected_revision,
                when=now,
                user_agent=user_agent,
                granted=granted,
            )
            return {
                "id": updated.id,
                "revision": updated.revision,
                "status": updated.status,
                "dpdp_consent_granted": updated.dpdp_consent_granted,
                "dpdp_consent_at_utc": updated.dpdp_consent_at_utc.isoformat() if updated.dpdp_consent_at_utc else None,
                "dpdp_consent_sha256": updated.dpdp_consent_sha256,
            }
        except Conflict as exc:
            raise HTTPException(409, str(exc))

    @app.post("/sessions/{session_id}/intake")
    async def intake(
        session_id: str,
        expected_revision: int = Form(...),
        audio: UploadFile = File(...),
    ):
        try:
            blob = await read_audio(audio)
            if not blob:
                raise AudioError("empty recording")
            services.settings.require_gnani()
            services.settings.require_extractor()
            result = services.workflow.intake(
                session_id,
                blob,
                audio.content_type or "",
                expected_revision=expected_revision,
            )
            base_dir = Path("var/sessions").resolve()
            wav_path = (base_dir / session_id / "intake.wav").resolve()
            if wav_path.is_relative_to(base_dir):
                wav_path.parent.mkdir(parents=True, exist_ok=True)
                wav_path.write_bytes(blob)
            return session_payload(result)
        except KeyError:
            raise HTTPException(404, "unknown session")
        except Conflict as exc:
            raise HTTPException(409, str(exc))
        except RepeatRequest as exc:
            raise HTTPException(422, {"repeat": True, "reason": exc.reason})
        except (AudioError, ExtractionError) as exc:
            raise HTTPException(422, str(exc))
        except ValueError as exc:
            raise HTTPException(503, str(exc))
        except GnaniError as exc:
            raise HTTPException(502, str(exc))

    @app.post("/sessions/{session_id}/reask/{field:path}")
    async def reask(
        session_id: str,
        field: str,
        expected_revision: int = Form(...),
        audio: UploadFile = File(...),
    ):
        try:
            blob = await read_audio(audio)
            if not blob:
                raise AudioError("empty recording")
            services.settings.require_gnani()
            services.settings.require_extractor()
            result = services.workflow.reask(
                session_id,
                field,
                blob,
                audio.content_type or "",
                expected_revision=expected_revision,
            )
            return session_payload(result)
        except KeyError:
            raise HTTPException(404, "unknown session")
        except Conflict as exc:
            raise HTTPException(409, str(exc))
        except RepeatRequest as exc:
            raise HTTPException(422, {"repeat": True, "reason": exc.reason})
        except (AudioError, ExtractionError) as exc:
            raise HTTPException(422, str(exc))
        except ValueError as exc:
            raise HTTPException(503, str(exc))
        except GnaniError as exc:
            raise HTTPException(502, str(exc))

    @app.post("/sessions/{session_id}/confirm-estimate")
    async def confirm_estimate(
        session_id: str,
        expected_revision: int = Form(...),
        audio: UploadFile = File(...),
    ):
        try:
            blob = await audio.read()
            if not blob:
                raise AudioError("empty recording")
            services.settings.require_gnani()
            services.settings.require_extractor()
            result = services.workflow.confirm_estimate(
                session_id, blob, audio.content_type or "", expected_revision=expected_revision
            )
            return session_payload(result)
        except KeyError:
            raise HTTPException(404, "unknown session")
        except Conflict as exc:
            raise HTTPException(409, str(exc))
        except NothingToConfirm as exc:
            raise HTTPException(422, str(exc))
        except (AudioError, ExtractionError) as exc:
            raise HTTPException(422, str(exc))
        except ValueError as exc:
            raise HTTPException(503, str(exc))
        except GnaniError as exc:
            raise HTTPException(502, str(exc))

    @app.post("/sessions/{session_id}/readback")
    async def start_readback(
        session_id: str,
        expected_revision: int = Form(...),
    ):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", session_id):
            raise HTTPException(404, "unknown session")

        try:
            readback = services.workflow.start_readback(session_id, expected_revision)
            base_dir = Path("var/sessions").resolve()
            wav_path = (base_dir / session_id / f"{readback.revision}.wav").resolve()
            if not wav_path.is_relative_to(base_dir):
                raise HTTPException(400, "invalid path")
            wav_path.parent.mkdir(parents=True, exist_ok=True)
            wav_path.write_bytes(readback.audio_wav)
            payload = {
                "revision": readback.revision,
                "readback_revision": readback.readback_revision,
                "audio_url": f"/sessions/{session_id}/readback.wav?revision={readback.revision}",
                "text": readback.text,
                "manifest": readback.manifest,
            }
            return Response(
                content=json.dumps(json_safe(payload), ensure_ascii=False, allow_nan=False),
                media_type="application/json",
            )
        except KeyError:
            raise HTTPException(404, "unknown session")
        except Conflict as exc:
            raise HTTPException(409, str(exc))
        except ValueError as exc:
            raise HTTPException(503, str(exc))
        except GnaniError as exc:
            raise HTTPException(502, str(exc))

    @app.get("/sessions/{session_id}/readback.wav")
    def get_readback_wav(
        session_id: str,
        revision: int = Query(...),
    ):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", session_id):
            raise HTTPException(404, "unknown session")

        try:
            session = services.store.get(session_id)
        except KeyError:
            raise HTTPException(404, "unknown session")

        if session.status != "awaiting_reply" or session.readback_revision != revision:
            raise HTTPException(409, "readback revision is stale or invalid")

        base_dir = Path("var/sessions").resolve()
        wav_path = (base_dir / session_id / f"{revision}.wav").resolve()
        if not wav_path.is_relative_to(base_dir):
            raise HTTPException(400, "invalid path")

        if not wav_path.is_file():
            raise HTTPException(404, "audio file not found")

        content = wav_path.read_bytes()
        return Response(content=content, media_type="audio/wav")

    @app.post("/sessions/{session_id}/reply")
    async def reply(
        session_id: str,
        request: Request,
        expected_revision: int = Form(...),
        readback_revision: int = Form(...),
        audio: UploadFile = File(...),
        dpdp_consent: bool = Form(True),
    ):
        try:
            blob = await read_audio(audio)
            if not blob:
                raise AudioError("empty recording")
            services.settings.require_gnani()

            if dpdp_consent:
                try:
                    current_s = services.store.get(session_id)
                    if not current_s.dpdp_consent_granted:
                        services.store.record_dpdp_consent(
                            session_id,
                            expected_revision=expected_revision,
                            when=datetime.now(timezone.utc),
                            user_agent=request.headers.get("user-agent"),
                            granted=True,
                        )
                except Exception:
                    pass

            result = services.workflow.reply(
                session_id,
                blob,
                audio.content_type or "",
                expected_revision=expected_revision,
                readback_revision=readback_revision,
            )
            base_dir = Path("var/sessions").resolve()
            wav_path = (base_dir / session_id / "reply.wav").resolve()
            if wav_path.is_relative_to(base_dir):
                wav_path.parent.mkdir(parents=True, exist_ok=True)
                wav_path.write_bytes(blob)
            return {
                "outcome": result.outcome,
                "transcript": result.transcript,
                "message": result.message,
                "fallback_payload": result.fallback_payload,
                "id": result.session.id,
                "revision": result.session.revision,
                "readback_revision": result.session.readback_revision,
                "status": result.session.status,
                "card": result.session.card.model_dump(mode="json") if result.session.card else None,
                "total_paise": result.session.card.maybe_total_paise if result.session.card else None,
                "review_fields": review_fields(result.session.card) if result.session.card else [],
            }
        except KeyError:
            raise HTTPException(404, "unknown session")
        except Conflict as exc:
            raise HTTPException(409, str(exc))
        except (AudioError, ExtractionError) as exc:
            raise HTTPException(422, str(exc))
        except ValueError as exc:
            raise HTTPException(503, str(exc))
        except GnaniError as exc:
            raise HTTPException(502, str(exc))

    @app.post("/sessions/{session_id}/fallback")
    def digital_fallback(
        session_id: str,
        action: str = Form("trigger"),
        expected_revision: int = Form(...),
    ):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", session_id):
            raise HTTPException(404, "unknown session")
        try:
            session = services.store.get(session_id)
        except KeyError:
            raise HTTPException(404, "unknown session")

        now = datetime.now(timezone.utc)
        log = TranscriptLog(
            role="customer",
            mode=f"digital_fallback_{action}",
            text=f"Digital fallback: {action}",
            recorded_at_utc=now,
        )

        try:
            if action in ("approve", "confirm"):
                updated = services.store.confirm(
                    session_id,
                    expected_revision=expected_revision,
                    when=now,
                    log=log,
                )
            elif action in ("request_changes", "change", "reject"):
                updated = services.store.request_changes(
                    session_id,
                    expected_revision=expected_revision,
                    log=log,
                )
            else:
                updated = services.store.trigger_fallback(
                    session_id,
                    expected_revision=expected_revision,
                    log=log,
                )

            return {
                "id": updated.id,
                "status": updated.status,
                "revision": updated.revision,
                "readback_revision": updated.readback_revision,
                "actions": [
                    {"label": "Approve Estimate", "action": "approve"},
                    {"label": "Request Changes", "action": "request_changes"},
                ],
                "card": updated.card.model_dump(mode="json") if updated.card else None,
                "total_paise": updated.card.maybe_total_paise if updated.card else None,
            }
        except Conflict as exc:
            raise HTTPException(409, str(exc))


    @app.get("/sessions/{session_id}/parcha.pdf")
    @app.get("/sessions/{session_id}/pdf")
    def get_parcha_pdf(session_id: str):
        try:
            session = services.store.get(session_id)
        except KeyError:
            raise HTTPException(404, "unknown session")
        try:
            pdf_bytes = render_pdf(session)
        except Conflict as exc:
            raise HTTPException(409, str(exc))
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="parcha-{session_id}-rev{session.revision}.pdf"'
            },
        )

    @app.get("/sessions/{session_id}/whatsapp.txt")
    @app.get("/sessions/{session_id}/whatsapp")
    def get_whatsapp_text(session_id: str):
        try:
            session = services.store.get(session_id)
        except KeyError:
            raise HTTPException(404, "unknown session")
        try:
            text = whatsapp_text(session)
        except Conflict as exc:
            raise HTTPException(409, str(exc))
        return Response(
            content=text,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="parcha-{session_id}.txt"'},
        )

    @app.get("/sessions/{session_id}/intake.wav")
    def get_intake_wav(session_id: str):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", session_id):
            raise HTTPException(404, "unknown session")
        try:
            services.store.get(session_id)
        except KeyError:
            raise HTTPException(404, "unknown session")

        base_dir = Path("var/sessions").resolve()
        wav_path = (base_dir / session_id / "intake.wav").resolve()
        if not wav_path.is_relative_to(base_dir):
            raise HTTPException(400, "invalid path")
        if wav_path.is_file():
            return Response(content=wav_path.read_bytes(), media_type="audio/wav")

        import struct
        pcm_wav = b"RIFF" + struct.pack("<I", 36) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 8000, 16000, 2, 16) + b"data" + struct.pack("<I", 0)
        return Response(content=pcm_wav, media_type="audio/wav")

    @app.get("/sessions/{session_id}/reply.wav")
    def get_reply_wav(session_id: str):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", session_id):
            raise HTTPException(404, "unknown session")
        try:
            services.store.get(session_id)
        except KeyError:
            raise HTTPException(404, "unknown session")

        base_dir = Path("var/sessions").resolve()
        wav_path = (base_dir / session_id / "reply.wav").resolve()
        if not wav_path.is_relative_to(base_dir):
            raise HTTPException(400, "invalid path")
        if wav_path.is_file():
            return Response(content=wav_path.read_bytes(), media_type="audio/wav")

        import struct
        pcm_wav = b"RIFF" + struct.pack("<I", 36) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 8000, 16000, 2, 16) + b"data" + struct.pack("<I", 0)
        return Response(content=pcm_wav, media_type="audio/wav")

    @app.get("/verify/{session_id}")
    def verify_session(
        session_id: str,
        request: Request,
        format: str | None = Query(None),
    ):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", session_id):
            raise HTTPException(404, "unknown session")
        try:
            session = services.store.get(session_id)
        except KeyError:
            raise HTTPException(404, "unknown session")

        intake_log = next((l for l in session.logs if l.role == "mechanic" and l.mode in ("intake", "transcribe", "verbatim")), None)
        if intake_log is None:
            intake_log = next((l for l in session.logs if l.role == "mechanic"), None)

        confirmation_log = next(
            (l for l in session.logs if l.role == "customer" and l.mode in ("reply", "digital_fallback_approve", "digital_fallback_confirm")),
            None,
        )
        if confirmation_log is None:
            confirmation_log = next((l for l in session.logs if l.role == "customer"), None)

        audit_digest = audit_manifest_sha256(session)
        vehicle = "KA-01-AB-1234 (Synthetic Demo)"
        legal_compliance = "Bharatiya Sakshya Adhiniyam, 2023 (Sections 61-63) Tamper-Evident Electronic Record"

        is_json = format == "json" or request.headers.get("accept", "").startswith("application/json")
        if is_json:
            return {
                "session_id": session.id,
                "status": session.status,
                "vehicle": vehicle,
                "revision": session.revision,
                "confirmed_at_utc": session.confirmed_at_utc.isoformat() if session.confirmed_at_utc else None,
                "audit_manifest_sha256": audit_digest,
                "legal_compliance": legal_compliance,
                "dpdp_consent": {
                    "granted": session.dpdp_consent_granted,
                    "recorded_at_utc": session.dpdp_consent_at_utc.isoformat() if session.dpdp_consent_at_utc else None,
                    "user_agent": session.dpdp_user_agent,
                    "consent_sha256": session.dpdp_consent_sha256,
                },
                "intake": {
                    "transcript": intake_log.text if intake_log else "",
                    "recorded_at_utc": intake_log.recorded_at_utc.isoformat() if intake_log else None,
                    "audio_sha256": intake_log.audio_sha256 if intake_log else None,
                    "audio_url": f"/sessions/{session.id}/intake.wav",
                },
                "confirmation": {
                    "transcript": confirmation_log.text if confirmation_log else "",
                    "recorded_at_utc": confirmation_log.recorded_at_utc.isoformat() if confirmation_log else None,
                    "audio_sha256": confirmation_log.audio_sha256 if confirmation_log else None,
                    "audio_url": f"/sessions/{session.id}/reply.wav",
                },
                "card": session.card.model_dump(mode="json") if session.card else None,
                "total_paise": session.card.maybe_total_paise if session.card else None,
            }

        return templates.TemplateResponse(
            request,
            "verify.html",
            {
                "session": session,
                "vehicle": vehicle,
                "confirmed_at_utc": session.confirmed_at_utc.isoformat() if session.confirmed_at_utc else None,
                "audit_manifest_sha256": audit_digest,
                "legal_compliance": legal_compliance,
                "dpdp_consent": {
                    "granted": session.dpdp_consent_granted,
                    "recorded_at_utc": session.dpdp_consent_at_utc.isoformat() if session.dpdp_consent_at_utc else None,
                    "user_agent": session.dpdp_user_agent,
                    "consent_sha256": session.dpdp_consent_sha256,
                },
                "intake": {
                    "transcript": intake_log.text if intake_log else "No intake transcript available",
                    "recorded_at_utc": intake_log.recorded_at_utc.isoformat() if intake_log else None,
                    "audio_sha256": intake_log.audio_sha256 if intake_log else None,
                    "audio_url": f"/sessions/{session.id}/intake.wav",
                },
                "confirmation": {
                    "transcript": confirmation_log.text if confirmation_log else "Pending confirmation",
                    "recorded_at_utc": confirmation_log.recorded_at_utc.isoformat() if confirmation_log else None,
                    "audio_sha256": confirmation_log.audio_sha256 if confirmation_log else None,
                    "audio_url": f"/sessions/{session.id}/reply.wav",
                },
                "total_paise": session.card.maybe_total_paise if session.card else None,
                "parcha_no": parcha_no(session.id),
            },
        )

    return app



app = create_app()
