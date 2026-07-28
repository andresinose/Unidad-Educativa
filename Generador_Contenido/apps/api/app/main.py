from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ORIGINS
from app.core.session import sweep_expired_sessions
from app.routers import documents, generation, export


@asynccontextmanager
async def lifespan(app: FastAPI):
    sweep_expired_sessions()
    yield


app = FastAPI(
    title="Motor de análisis curricular y generación de recursos",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(generation.router)
app.include_router(export.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
