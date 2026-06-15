from fastapi import APIRouter, HTTPException

from backend.core.schemas import TaskStatusResponse
from backend.task_manager import get_task

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(
        task_id=task_id,
        status=task.get("status", "unknown"),
        progress=task.get("progress", 0.0),
        detail=task.get("detail", ""),
    )
