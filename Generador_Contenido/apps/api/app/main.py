from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ORIGINS
from app.core.session import sweep_expired_sessions
from app.routers import activities, documents, export, generation, materials, usage


import asyncio

async def _periodic_session_sweep():
    while True:
        try:
            sweep_expired_sessions()
        except Exception:
            pass
        await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    sweep_expired_sessions()
    task = asyncio.create_task(_periodic_session_sweep())
    try:
        yield
    finally:
        task.cancel()



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
app.include_router(materials.router)
app.include_router(activities.router)
app.include_router(usage.router)



@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
