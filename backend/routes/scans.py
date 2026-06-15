import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.models import Scan
from backend.core.schemas import ScanCreate, ScanResponse, TaskStatusResponse
from backend.scanner.nmap_runner import NmapRunner
from backend.scanner.fingerprint import fingerprint_services
from backend.scanner.validate import validate_target
from backend.analysis.risk_engine import calculate_risk_score
from backend.analysis.cve_lookup import CVELookup
from backend.task_manager import create_task, update_task, get_task, TASKS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scans", tags=["scans"])

nmapper = NmapRunner()
cve_lookup = CVELookup()

_scan_tasks: dict[int, asyncio.Task] = {}


async def run_scan_task(scan_id: int, target: str, profile: str):
    async with async_session() as db:
        try:
            result = await db.execute(select(Scan).where(Scan.id == scan_id))
            scan = result.scalar_one_or_none()
            if not scan:
                return
            scan.status = "running"
            scan.started_at = datetime.utcnow()
            await db.commit()

            def progress_callback(percent: float):
                scan.heartbeat_at = datetime.utcnow()
                TASKS[scan.task_id] = TASKS.get(scan.task_id, {})
                TASKS[scan.task_id]["progress"] = percent
                TASKS[scan.task_id]["detail"] = f"Scanning... {percent:.0f}%"

            scan_result = await nmapper.run(target, profile, progress_callback=progress_callback)
            all_ports = []
            cve_data = []
            for host in scan_result.get("hosts", []):
                ports = fingerprint_services(host.get("ports", []))
                all_ports.extend(ports)
                for port in ports:
                    for cve_hint in port.get("vulnerability_hints", []):
                        cve_data.append({"id": cve_hint, "severity": "medium", "description": ""})
            risk_score = calculate_risk_score(all_ports, cve_data)
            scan.ports = all_ports
            scan.risk_score = risk_score
            scan.cve_data = cve_data
            scan.summary = f"Found {len(all_ports)} open ports across {len(scan_result.get('hosts', []))} hosts"
            scan.status = "completed"
            scan.completed_at = datetime.utcnow()
            await db.commit()
            update_task(scan.task_id, "completed", 100.0, "Scan complete")
        except Exception as e:
            logger.error(f"Scan {scan_id} failed: {e}")
            scan.status = "failed"
            scan.completed_at = datetime.utcnow()
            await db.commit()
            update_task(scan.task_id, "failed", 0.0, str(e))
        finally:
            _scan_tasks.pop(scan_id, None)


@router.post("", response_model=ScanResponse, status_code=201)
async def start_scan(data: ScanCreate, db: AsyncSession = Depends(get_db)):
    target = await db.execute(select(Target).where(Target.id == data.target_id))
    target_obj = target.scalar_one_or_none()
    if not target_obj:
        raise HTTPException(status_code=404, detail="Target not found")
    target_str = target_obj.ip_range or target_obj.domain or target_obj.name
    validate_target(target_str)

    task_id = create_task()
    scan = Scan(
        target_id=data.target_id,
        task_id=task_id,
        scan_profile=data.scan_profile,
        options=data.options,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    task = asyncio.create_task(run_scan_task(scan.id, target_str, data.scan_profile))
    _scan_tasks[scan.id] = task
    return scan

from backend.core.database import async_session
from backend.core.models import Target


@router.get("", response_model=list[ScanResponse])
async def list_scans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = Query(None),
    target_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Scan).offset(skip).limit(limit).order_by(Scan.created_at.desc())
    if status:
        query = query.where(Scan.status == status)
    if target_id:
        query = query.where(Scan.target_id == target_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.delete("/{scan_id}", status_code=204)
async def delete_scan(scan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.id in _scan_tasks:
        _scan_tasks[scan.id].cancel()
        del _scan_tasks[scan.id]
    await db.delete(scan)
    await db.commit()


@router.post("/{scan_id}/cancel", response_model=ScanResponse)
async def cancel_scan(scan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.id in _scan_tasks:
        _scan_tasks[scan.id].cancel()
        del _scan_tasks[scan.id]
    scan.status = "interrupted"
    await db.commit()
    update_task(scan.task_id, "interrupted", 0.0, "Cancelled by user")
    return scan
