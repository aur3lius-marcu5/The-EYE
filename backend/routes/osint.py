import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db, async_session
from backend.core.models import OSINTResult, Target
from backend.core.schemas import OSINTCreate, OSINTResponse
from backend.osint.discovery import SubdomainEnumerator
from backend.osint.tech_detect import TechDetector
from backend.osint.email_recon import EmailRecon
from backend.osint.ip_enrich import IPEnricher
from backend.task_manager import create_task, update_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/osint", tags=["osint"])

_osint_tasks: dict[int, asyncio.Task] = {}


async def run_osint_task(result_id: int, domain: str, modules: list[str]):
    async with async_session() as db:
        try:
            result_row = await db.execute(select(OSINTResult).where(OSINTResult.id == result_id))
            osint = result_row.scalar_one_or_none()
            if not osint:
                return
            osint.status = "running"
            osint.started_at = datetime.utcnow()
            await db.commit()

            findings = {}
            total = len(modules)
            for i, module in enumerate(modules):
                update_task(osint.task_id, "running", (i / total) * 100, f"Running {module}...")
                osint.heartbeat_at = datetime.utcnow()
                await db.commit()

                if module == "discovery":
                    enumerator = SubdomainEnumerator()
                    findings["discovery"] = await enumerator.enumerate(domain)
                    osint.source = "crtsh,dns"
                    await enumerator.close()
                elif module == "tech_detect":
                    detector = TechDetector()
                    findings["tech_detect"] = await detector.detect(f"https://{domain}" if not domain.startswith("http") else domain)
                    await detector.close()
                elif module == "email_recon":
                    recon = EmailRecon()
                    findings["email_recon"] = await recon.investigate(domain)
                    await recon.close()
                elif module == "ip_enrich":
                    enricher = IPEnricher()
                    import socket
                    try:
                        _, _, ips = socket.gethostbyname_ex(domain)
                        findings["ip_enrich"] = []
                        for ip in ips[:5]:
                            findings["ip_enrich"].append(await enricher.enrich(ip))
                    except Exception:
                        findings["ip_enrich"] = []
                    await enricher.close()

            osint.findings = findings
            osint.status = "completed"
            osint.completed_at = datetime.utcnow()
            await db.commit()
            update_task(osint.task_id, "completed", 100.0, "OSINT investigation complete")
        except Exception as e:
            logger.error(f"OSINT {result_id} failed: {e}")
            osint.status = "failed"
            osint.completed_at = datetime.utcnow()
            await db.commit()
            update_task(osint.task_id, "failed", 0.0, str(e))
        finally:
            _osint_tasks.pop(result_id, None)


@router.post("", response_model=OSINTResponse, status_code=201)
async def start_investigation(data: OSINTCreate, db: AsyncSession = Depends(get_db)):
    target = await db.execute(select(Target).where(Target.id == data.target_id))
    target_obj = target.scalar_one_or_none()
    if not target_obj:
        raise HTTPException(status_code=404, detail="Target not found")
    domain = target_obj.domain or target_obj.name
    if not domain:
        raise HTTPException(status_code=400, detail="Target must have a domain for OSINT")

    task_id = create_task()
    result = OSINTResult(
        target_id=data.target_id,
        task_id=task_id,
        module=",".join(data.modules),
    )
    db.add(result)
    await db.commit()
    await db.refresh(result)

    task = asyncio.create_task(run_osint_task(result.id, domain, data.modules))
    _osint_tasks[result.id] = task
    return result


@router.get("", response_model=list[OSINTResponse])
async def list_investigations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    target_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(OSINTResult).offset(skip).limit(limit).order_by(OSINTResult.created_at.desc())
    if target_id:
        query = query.where(OSINTResult.target_id == target_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{result_id}", response_model=OSINTResponse)
async def get_investigation(result_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OSINTResult).where(OSINTResult.id == result_id))
    osint = result.scalar_one_or_none()
    if not osint:
        raise HTTPException(status_code=404, detail="OSINT investigation not found")
    return osint


@router.delete("/{result_id}", status_code=204)
async def delete_investigation(result_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OSINTResult).where(OSINTResult.id == result_id))
    osint = result.scalar_one_or_none()
    if not osint:
        raise HTTPException(status_code=404, detail="OSINT investigation not found")
    if osint.id in _osint_tasks:
        _osint_tasks[osint.id].cancel()
        del _osint_tasks[osint.id]
    await db.delete(osint)
    await db.commit()
