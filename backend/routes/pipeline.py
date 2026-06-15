import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db, async_session
from backend.core.models import PipelineRun, Target
from backend.core.schemas import PipelineRunCreate, PipelineRunResponse
from backend.pipeline.runner import load_profile, run_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

_running_pipelines: dict[int, asyncio.Task] = {}


async def _run_pipeline_task(pr_id: int, target_id: int, profile_name: str, run_uuid: str):
    try:
        await run_pipeline(target_id, profile_name, run_uuid)
    except Exception as e:
        logger.error(f"Pipeline {pr_id} failed: {e}")
        async with async_session() as db:
            pr = await db.get(PipelineRun, pr_id)
            if pr:
                pr.status = "failed"
                await db.commit()
    finally:
        _running_pipelines.pop(pr_id, None)


@router.post("/run", response_model=PipelineRunResponse, status_code=201)
async def start_pipeline(data: PipelineRunCreate, db: AsyncSession = Depends(get_db)):
    target = await db.get(Target, data.target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    try:
        profile = load_profile(data.profile_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid profile: {e}")
    if not profile:
        raise HTTPException(status_code=400, detail=f"Unknown profile: {data.profile_name}")
    import uuid
    run_uuid = str(uuid.uuid4())
    pr = PipelineRun(
        target_id=data.target_id,
        profile_name=data.profile_name,
        status="running",
        started_at=datetime.utcnow(),
        stage_results=[],
    )
    db.add(pr)
    await db.commit()
    await db.refresh(pr)
    task = asyncio.create_task(_run_pipeline_task(pr.id, data.target_id, data.profile_name, run_uuid))
    _running_pipelines[pr.id] = task
    target_name = target.name or target.domain or target.ip_range or ""
    return {
        "id": pr.id,
        "target_id": pr.target_id,
        "target_name": target_name,
        "profile_name": pr.profile_name,
        "status": pr.status,
        "stage_results": pr.stage_results,
        "started_at": pr.started_at,
        "completed_at": pr.completed_at,
    }


@router.get("/runs", response_model=list[PipelineRunResponse])
async def list_pipeline_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    target_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(PipelineRun).offset(skip).limit(limit).order_by(PipelineRun.started_at.desc())
    if target_id:
        query = query.where(PipelineRun.target_id == target_id)
    result = await db.execute(query)
    runs = result.scalars().all()
    out = []
    for pr in runs:
        tg = await db.get(Target, pr.target_id)
        target_name = (tg.name or tg.domain or tg.ip_range or "") if tg else ""
        out.append({
            "id": pr.id,
            "target_id": pr.target_id,
            "target_name": target_name,
            "profile_name": pr.profile_name,
            "status": pr.status,
            "stage_results": pr.stage_results,
            "started_at": pr.started_at,
            "completed_at": pr.completed_at,
        })
    return out


@router.get("/runs/{run_id}", response_model=PipelineRunResponse)
async def get_pipeline_run(run_id: int, db: AsyncSession = Depends(get_db)):
    pr = await db.get(PipelineRun, run_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    tg = await db.get(Target, pr.target_id)
    target_name = (tg.name or tg.domain or tg.ip_range or "") if tg else ""
    return {
        "id": pr.id,
        "target_id": pr.target_id,
        "target_name": target_name,
        "profile_name": pr.profile_name,
        "status": pr.status,
        "stage_results": pr.stage_results,
        "started_at": pr.started_at,
        "completed_at": pr.completed_at,
    }


@router.post("/runs/{run_id}/cancel", response_model=PipelineRunResponse)
async def cancel_pipeline_run(run_id: int, db: AsyncSession = Depends(get_db)):
    pr = await db.get(PipelineRun, run_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    if run_id in _running_pipelines:
        _running_pipelines[run_id].cancel()
        del _running_pipelines[run_id]
    pr.status = "interrupted"
    await db.commit()
    await db.refresh(pr)
    tg = await db.get(Target, pr.target_id)
    target_name = (tg.name or tg.domain or tg.ip_range or "") if tg else ""
    return {
        "id": pr.id,
        "target_id": pr.target_id,
        "target_name": target_name,
        "profile_name": pr.profile_name,
        "status": pr.status,
        "stage_results": pr.stage_results,
        "started_at": pr.started_at,
        "completed_at": pr.completed_at,
    }


@router.get("/profiles", response_model=list[str])
async def list_profiles():
    from backend.pipeline.runner import PROFILES_DIR
    files = os.listdir(PROFILES_DIR) if os.path.exists(PROFILES_DIR) else []
    return [f.replace(".yaml", "") for f in files if f.endswith(".yaml")]
