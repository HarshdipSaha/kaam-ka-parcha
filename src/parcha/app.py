from dataclasses import dataclass
import json
from pathlib import Path
import re
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request, Query, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import Settings
from .session import Conflict, SessionStore
from .workflow import Workflow
from .audio import AudioError, normalize_upload
from .extract import ExtractionError, Extractor
from .gnani import PrismaClient, TimbreClient, GnaniError
from .schema import review_fields

ROOT = Path(__file__).parent


@dataclass
class AppServices:
    settings: Settings
    store: SessionStore
    workflow: Workflow
    timbre: TimbreClient | None = None


def default_services() -> AppServices:
    settings = Settings.load()
    store = SessionStore()
    prisma = PrismaClient(settings.api_key, base_url=settings.gnani_base_url)
    extractor = Extractor(
        settings.extractor_base_url,
        settings.extractor_api_key,
        settings.extractor_model,
    )
    timbre = TimbreClient(
        settings.api_key,
        voice=settings.tts_voice,
        base_url=settings.gnani_base_url,
    )
    workflow = Workflow(
        store=store,
        prisma=prisma,
        extractor=extractor,
        normalize_audio=normalize_upload,
        timbre=timbre,
    )
    return AppServices(settings, store, workflow, timbre)


def session_payload(session) -> dict:
    card = session.card
    return {
        "id": session.id,
        "revision": session.revision,
        "status": session.status,
        "card": card.model_dump(mode="json") if card else None,
        "total_paise": card.maybe_total_paise if card else None,
        "review_fields": review_fields(card) if card else [],
    }


def create_app(services: AppServices | None = None) -> FastAPI:
    services = services or default_services()
    app = FastAPI(title="Kaam ka Parcha")

    static_dir = ROOT / "static"
    templates_dir = ROOT / "templates"
    static_dir.mkdir(parents=True, exist_ok=True)
    templates_dir.mkdir(parents=True, exist_ok=True)

    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    templates = Jinja2Templates(directory=templates_dir)

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/workshop", response_class=HTMLResponse)
    def workshop(request: Request):
        return templates.TemplateResponse(request, "workshop.html", {})

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
            },
        )

    @app.post("/sessions")
    def create_session():
        return session_payload(services.store.create())

    @app.get("/sessions/{session_id}")
    def get_session(session_id: str):
        try:
            return session_payload(services.store.get(session_id))
        except KeyError:
            raise HTTPException(404, "unknown session")

    @app.post("/sessions/{session_id}/intake")
    async def intake(
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
            result = services.workflow.intake(
                session_id,
                blob,
                audio.content_type or "",
                expected_revision=expected_revision,
            )
            return session_payload(result)
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

    @app.post("/sessions/{session_id}/reask/{field:path}")
    async def reask(
        session_id: str,
        field: str,
        expected_revision: int = Form(...),
        audio: UploadFile = File(...),
    ):
        try:
            blob = await audio.read()
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
                content=json.dumps(payload, ensure_ascii=False),
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
        expected_revision: int = Form(...),
        readback_revision: int = Form(...),
        audio: UploadFile = File(...),
    ):
        try:
            blob = await audio.read()
            if not blob:
                raise AudioError("empty recording")
            services.settings.require_gnani()
            result = services.workflow.reply(
                session_id,
                blob,
                audio.content_type or "",
                expected_revision=expected_revision,
                readback_revision=readback_revision,
            )
            return {
                "outcome": result.outcome,
                "transcript": result.transcript,
                "message": result.message,
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

    return app


app = create_app()
