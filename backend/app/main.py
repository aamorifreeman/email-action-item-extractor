"""FastAPI application entrypoint: lifespan, CORS, router registration."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables and warm ML singletons so the first request is fast."""
    init_db()
    from app.ml.embeddings import get_embedder
    from app.ml.rule_based import get_nlp

    get_nlp()
    get_embedder()
    yield


app = FastAPI(
    title="InboxIQ API",
    description="Email action-item extraction — rule-based NLP and Gemini engines.",
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


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


# Routers (implemented under app/api/).
from app.api import extraction, integrations, tasks  # noqa: E402

app.include_router(extraction.router, prefix="/api", tags=["extraction"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])
app.include_router(integrations.router, prefix="/api", tags=["integrations"])
