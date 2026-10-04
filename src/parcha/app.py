from dataclasses import dataclass
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request
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

    return app


app = create_app()
