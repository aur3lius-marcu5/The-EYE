from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.models import Target
from backend.core.schemas import TargetCreate, TargetUpdate, TargetResponse
from backend.scanner.validate import validate_target

router = APIRouter(prefix="/api/targets", tags=["targets"])


@router.post("", response_model=TargetResponse, status_code=201)
async def create_target(data: TargetCreate, db: AsyncSession = Depends(get_db)):
    if data.ip_range:
        validate_target(data.ip_range)
    if data.domain:
        validate_target(data.domain)
    target = Target(
        name=data.name,
        ip_range=data.ip_range,
        domain=data.domain,
        notes=data.notes,
        tags=data.tags,
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)
    return target


@router.get("", response_model=list[TargetResponse])
async def list_targets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    name: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Target).offset(skip).limit(limit).order_by(Target.updated_at.desc())
    if name:
        query = query.where(Target.name.ilike(f"%{name}%"))
    if tag:
        query = query.where(Target.tags.any(tag))
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(target_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(target_id: int, data: TargetUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    if data.name is not None:
        target.name = data.name
    if data.notes is not None:
        target.notes = data.notes
    if data.tags is not None:
        target.tags = data.tags
    target.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(target)
    return target


@router.delete("/{target_id}", status_code=204)
async def delete_target(target_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    await db.delete(target)
    await db.commit()
