import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Optional

import yaml
from sqlalchemy import select

from backend.core.database import async_session
from backend.core.models import PipelineRun, Target
from backend.core.config import settings
from backend.pipeline.stages import STAGE_REGISTRY
from backend.osint.auto_discover import discover_from_pipeline_results, save_discovered_targets
from backend.task_manager import create_task, update_task

logger = logging.getLogger(__name__)

PROFILES_DIR = os.path.join(os.path.dirname(__file__), "profiles")

_profile_cache: dict[str, dict] = {}


def load_profile(name: str) -> Optional[dict]:
    if name in _profile_cache:
        return _profile_cache[name]
    path = os.path.join(PROFILES_DIR, f"{name}.yaml")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        profile = yaml.safe_load(f)
    _profile_cache[name] = profile
    return profile


async def resolve_stage_order(profile: dict) -> list[dict]:
    stages = profile.get("stages", [])
    stage_map = {s["id"]: s for s in stages}
    ordered = []
    added = set()

    def add_stage(sid: str):
        if sid in added:
            return
        stage = stage_map.get(sid)
        if not stage:
            return
        for dep in stage.get("depends_on", []):
            add_stage(dep)
        if sid not in added:
            ordered.append(stage)
            added.add(sid)

    for stage in stages:
        add_stage(stage["id"])
    return ordered


async def run_pipeline(target_id: int, profile_name: str, pipeline_run_id: Optional[str] = None) -> dict:
    profile = load_profile(profile_name)
    if not profile:
        raise ValueError(f"Unknown pipeline profile: {profile_name}")

    async with async_session() as db:
        t_result = await db.execute(select(Target).where(Target.id == target_id))
        target = t_result.scalar_one_or_none()
        if not target:
            raise ValueError(f"Target {target_id} not found")
        target_name = target.ip_range or target.domain or target.name

        if pipeline_run_id:
            run_uuid = pipeline_run_id
        else:
            task_id = create_task()
            run_uuid = task_id
            pr = PipelineRun(
                target_id=target_id,
                profile_name=profile_name,
                status="running",
                started_at=datetime.utcnow(),
                stage_results=[],
            )
            db.add(pr)
            await db.commit()
            await db.refresh(pr)
            pipeline_run_id_local = str(pr.id)
        await db.commit()

    stages = await resolve_stage_order(profile)
    stage_inputs: dict[str, Any] = {}
    results: list[dict] = []
    overall_status = "completed"

    for i, stage in enumerate(stages):
        sid = stage["id"]
        handler = STAGE_REGISTRY.get(sid)
        if not handler:
            logger.warning(f"No handler for stage {sid}, skipping")
            results.append({"id": sid, "status": "skipped", "reason": "no_handler"})
            continue

        stage_result = {"id": sid, "status": "running", "started_at": datetime.utcnow().isoformat()}
        update_task(pipeline_run_id or target_name, "running", (i / len(stages)) * 100, f"Running {sid}...")

        try:
            if sid in ("cve_lookup", "gravatar", "ai_analysis"):
                output = await handler(target_id, pipeline_run_id, target_name, stage, stage_inputs)
            else:
                output = await handler(target_id, pipeline_run_id, target_name, stage)

            stage_inputs[sid] = output
            stage_result["status"] = "completed"
            stage_result["completed_at"] = datetime.utcnow().isoformat()
            if isinstance(output, dict):
                stage_result["findings_count"] = len([k for k in output if k in ("subdomains", "ports", "emails", "ips", "cves") and isinstance(output[k], list)])
        except Exception as e:
            logger.error(f"Stage {sid} failed: {e}")
            stage_result["status"] = "failed"
            stage_result["error"] = str(e)
            overall_status = "partial"

        results.append(stage_result)

    discovered = await discover_from_pipeline_results(target_id, stage_inputs)
    if discovered:
        new_ids = await save_discovered_targets(target_id, discovered)
        for sid, info in stage_inputs.items():
            if isinstance(info, dict):
                info.setdefault("_discovered_targets", []).extend(
                    {"id": nid, "name": d["name"]}
                    for nid, d in zip(new_ids, discovered)
                    if nid
                )

    async with async_session() as db:
        pr_result = await db.execute(
            select(PipelineRun).where(PipelineRun.target_id == target_id).order_by(PipelineRun.started_at.desc())
        )
        pr = pr_result.scalar_first()
        if pr:
            pr.status = overall_status
            pr.stage_results = results
            pr.completed_at = datetime.utcnow()
            await db.commit()

    update_task(pipeline_run_id or target_name, overall_status, 100.0, "Pipeline complete")
    return {"pipeline_run_id": pipeline_run_id, "status": overall_status, "stages": results, "discovered_targets": len(discovered)}
