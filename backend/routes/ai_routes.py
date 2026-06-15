import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.models import AIAnalysis, Scan, OSINTResult
from backend.core.schemas import AIAnalyzeRequest, AIAnalysisResponse
from backend.ai.agents.scan_advisor import advise_scan
from backend.ai.agents.osint_analyst import analyze_osint
from backend.ai.agents.report_writer import write_report
from backend.ai.engine import analyze_with_ai

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai"])

AGENT_MAP = {
    "scan_advisor": advise_scan,
    "osint_analyst": analyze_osint,
    "report_writer": write_report,
}


@router.post("/analyze", response_model=AIAnalysisResponse)
async def analyze(data: AIAnalyzeRequest, db: AsyncSession = Depends(get_db)):
    target_id = data.target_id
    scan_id = data.scan_id
    osint_id = data.osint_id
    agent_type = data.agent_type

    if not target_id and not scan_id and not osint_id:
        raise HTTPException(status_code=400, detail="At least one of target_id, scan_id, or osint_id required")

    target_str = ""
    scan_data = {}
    osint_data = {}

    if scan_id:
        result = await db.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one_or_none()
        if scan:
            target_str = f"scan_{scan_id}"
            scan_data = {
                "ports": scan.ports or [],
                "risk_score": scan.risk_score or 0,
                "cve_data": scan.cve_data or [],
                "profile": scan.scan_profile or "standard",
            }

    if osint_id:
        result = await db.execute(select(OSINTResult).where(OSINTResult.id == osint_id))
        osint_obj = result.scalar_one_or_none()
        if osint_obj:
            target_str = f"osint_{osint_id}"
            osint_data = osint_obj.findings or {}
            if not scan_data and osint_obj.target_id:
                target_id = osint_obj.target_id

    if not scan_data and not osint_data:
        raise HTTPException(status_code=400, detail="No scan or OSINT data found")

    if agent_type == "scan_advisor":
        ports = scan_data.get("ports", [])
        risk_score = scan_data.get("risk_score", 0)
        cve_data = scan_data.get("cve_data", [])
        ai_result = await advise_scan(target_str, ports, risk_score, cve_data)
    elif agent_type == "osint_analyst":
        ai_result = await analyze_osint(osint_data)
    elif agent_type == "report_writer":
        ai_result = await write_report(target_str, scan_data, osint_data)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown agent type: {agent_type}")

    analysis = AIAnalysis(
        target_id=target_id,
        scan_id=scan_id,
        osint_id=osint_id,
        agent_type=agent_type,
        prompt=json.dumps({"scan_data": scan_data, "osint_data": osint_data}),
        response=ai_result.get("content", ""),
        model_used=ai_result.get("model", "unknown"),
        tokens_used=ai_result.get("tokens"),
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis


@router.get("/analyses", response_model=list[AIAnalysisResponse])
async def list_analyses(
    skip: int = 0,
    limit: int = 100,
    target_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(AIAnalysis).offset(skip).limit(limit).order_by(AIAnalysis.created_at.desc())
    if target_id:
        query = query.where(AIAnalysis.target_id == target_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.websocket("/ws/chat")
async def ai_chat_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            msg_data = json.loads(data)
            content = msg_data.get("content", "")
            if not content:
                continue
            system_prompt = msg_data.get("system_prompt", "You are a cybersecurity assistant. Be concise and technical.")
            result = await analyze_with_ai(system_prompt, content)
            await websocket.send_text(json.dumps({
                "type": "message",
                "content": result.get("content", ""),
                "model": result.get("model", "unknown"),
            }))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
