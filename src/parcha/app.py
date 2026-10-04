from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Kaam ka Parcha")

    @app.get("/health")
    def health() -> dict[str, bool]:
        return {"ok": True}

    return app


app = create_app()
