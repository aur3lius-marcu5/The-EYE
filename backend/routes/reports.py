from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.models import Report
from backend.core.schemas import ReportCreate, ReportResponse

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("", response_model=ReportResponse, status_code=201)
async def generate_report(data: ReportCreate, db: AsyncSession = Depends(get_db)):
    file_path = f"reports/target_{data.target_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{data.format}"
    report = Report(
        target_id=data.target_id,
        scan_ids=data.scan_ids,
        osint_ids=data.osint_ids,
        report_type=data.report_type,
        format=data.format,
        file_path=file_path,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("", response_model=list[ReportResponse])
async def list_reports(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report).offset(skip).limit(limit).order_by(Report.generated_at.desc())
    )
    return result.scalars().all()


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/{report_id}", status_code=204)
async def delete_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    await db.delete(report)
    await db.commit()
