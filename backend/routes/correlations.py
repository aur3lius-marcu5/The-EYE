import logging
from fastapi import APIRouter
from backend.analysis.correlation import correlate_all, get_dashboard_stats

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/correlations", tags=["correlations"])


@router.get("/")
async def list_correlations():
    return await correlate_all()


@router.get("/dashboard")
async def dashboard_stats():
    try:
        return await get_dashboard_stats()
    except Exception as e:
        logger.warning(f"Dashboard stats failed: {e}")
        return {"total_targets": 0, "discovered_targets": 0, "total_pipeline_runs": 0, "completed_runs": 0, "running_runs": 0}
