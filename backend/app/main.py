import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Make both `ai.*` (project root) and `app.*` (backend dir) importable no matter
# where uvicorn is launched from.
ROOT_DIR = Path(__file__).resolve().parents[2]      # project root -> enables `import ai`
BACKEND_DIR = Path(__file__).resolve().parents[1]   # backend/     -> enables `import app`
for _p in (str(BACKEND_DIR), str(ROOT_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.config import get_settings
from app.routers import admin, claims, items, notifications

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting %s", settings.app_name)

    if settings.warmup_models:
        # Preload the ML models once at boot so the first user request isn't slow
        # (and so any model-download/load failure surfaces here, not mid-request).
        try:
            from ai.embeddings import EmbeddingService

            logger.info("Warming up ML models (first run downloads ~500MB)...")
            svc = EmbeddingService()
            svc.generate_text_embedding("warmup")
            logger.info("ML models ready.")
        except Exception:
            logger.exception("Model warmup failed; models will load lazily on first request")

    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = settings.api_prefix
    app.include_router(items.router, prefix=prefix)
    app.include_router(claims.router, prefix=prefix)
    app.include_router(notifications.router, prefix=prefix)
    app.include_router(admin.router, prefix=prefix)

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()
