from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.models import Finding
from backend.core.schemas import FindingCreate, FindingResponse

router = APIRouter(prefix="/api/findings", tags=["findings"])


@router.post("", response_model=FindingResponse, status_code=201)
async def create_finding(data: FindingCreate, db: AsyncSession = Depends(get_db)):
    finding = Finding(
        target_id=data.target_id,
        pipeline_run_id=data.pipeline_run_id,
        source_tool=data.source_tool,
        finding_type=data.finding_type,
        severity=data.severity,
        data=data.data,
    )
    db.add(finding)
    await db.commit()
    await db.refresh(finding)
    return finding


@router.get("", response_model=list[FindingResponse])
async def list_findings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    target_id: Optional[int] = Query(None),
    finding_type: Optional[str] = Query(None),
    source_tool: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Finding).offset(skip).limit(limit).order_by(Finding.created_at.desc())
    if target_id:
        query = query.where(Finding.target_id == target_id)
    if finding_type:
        query = query.where(Finding.finding_type == finding_type)
    if source_tool:
        query = query.where(Finding.source_tool == source_tool)
    if severity:
        query = query.where(Finding.severity == severity)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.delete("/{finding_id}", status_code=204)
async def delete_finding(finding_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    await db.delete(finding)
    await db.commit()
