import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import async_session
from backend.core.models import Scan, OSINTResult

TASKS: dict[str, dict[str, Any]] = {}


def create_task() -> str:
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {
        "status": "pending",
        "progress": 0.0,
        "detail": "",
        "created_at": datetime.utcnow().isoformat(),
    }
    return task_id


def update_task(task_id: str, status: str = "", progress: float = 0.0, detail: str = ""):
    if task_id in TASKS:
        if status:
            TASKS[task_id]["status"] = status
        if progress is not None:
            TASKS[task_id]["progress"] = progress
        if detail:
            TASKS[task_id]["detail"] = detail


def get_task(task_id: str) -> Optional[dict[str, Any]]:
    return TASKS.get(task_id)


async def reconcile_tasks():
    async with async_session() as session:
        for model_cls in [Scan, OSINTResult]:
            result = await session.execute(
                select(model_cls).where(model_cls.status == "running")
            )
            rows = result.scalars().all()
            for row in rows:
                if row.heartbeat_at:
                    elapsed = (datetime.utcnow() - row.heartbeat_at).total_seconds()
                    if elapsed > 60:
                        row.status = "interrupted"
                else:
                    row.status = "interrupted"
            await session.commit()
