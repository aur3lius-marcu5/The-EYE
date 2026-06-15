import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.core.database import create_tables
from backend.routes import targets, scans, osint, ai_routes, reports, tasks, findings, pipeline, correlations
from backend.task_manager import reconcile_tasks
from backend.core.tool_check import refresh_tool_availability


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    await reconcile_tasks()
    await refresh_tool_availability()
    yield


app = FastAPI(title="THE EYE", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(targets.router)
app.include_router(scans.router)
app.include_router(osint.router)
app.include_router(ai_routes.router)
app.include_router(reports.router)
app.include_router(tasks.router)
app.include_router(findings.router)
app.include_router(pipeline.router)
app.include_router(correlations.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "name": "THE EYE"}
