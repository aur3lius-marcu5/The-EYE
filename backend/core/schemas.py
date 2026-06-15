from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class TargetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    ip_range: Optional[str] = None
    domain: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    passive_only: Optional[bool] = None
    auto_pipeline: Optional[bool] = None
    max_depth: Optional[int] = None


class TargetUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    passive_only: Optional[bool] = None
    auto_pipeline: Optional[bool] = None
    max_depth: Optional[int] = None


class TargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    ip_range: Optional[str] = None
    domain: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    passive_only: bool = False
    auto_pipeline: bool = True
    max_depth: int = 2
    created_at: datetime
    updated_at: datetime


class ScanCreate(BaseModel):
    target_id: int
    scan_profile: str = Field(default="standard", pattern=r"^(quick|standard|deep|stealth)$")
    options: Optional[dict[str, Any]] = None


class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    target_id: int
    task_id: Optional[str] = None
    status: str
    scan_profile: str
    options: Optional[dict[str, Any]] = None
    ports: Optional[list[dict[str, Any]]] = None
    risk_score: Optional[float] = None
    summary: Optional[str] = None
    cve_data: Optional[dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class OSINTCreate(BaseModel):
    target_id: int
    modules: list[str] = Field(default=["discovery", "tech_detect", "email_recon", "ip_enrich"])


class OSINTResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    target_id: int
    task_id: Optional[str] = None
    status: str
    module: str
    source: Optional[str] = None
    findings: Optional[dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AIAnalyzeRequest(BaseModel):
    target_id: Optional[int] = None
    scan_id: Optional[int] = None
    osint_id: Optional[int] = None
    agent_type: str = Field(default="scan_advisor", pattern=r"^(scan_advisor|osint_analyst|report_writer)$")


class AIAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    agent_type: str
    prompt: Optional[str] = None
    response: Optional[str] = None
    model_used: Optional[str] = None
    created_at: datetime


class ReportCreate(BaseModel):
    target_id: int
    scan_ids: Optional[list[int]] = None
    osint_ids: Optional[list[int]] = None
    report_type: str = Field(default="technical", pattern=r"^(executive|technical|full)$")
    format: str = Field(default="html", pattern=r"^(html|pdf|json|csv)$")


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    target_id: int
    report_type: str
    format: str
    file_path: str
    generated_at: datetime


class FindingCreate(BaseModel):
    target_id: int
    pipeline_run_id: Optional[str] = None
    source_tool: str = Field(..., min_length=1, max_length=100)
    finding_type: str = Field(..., min_length=1, max_length=100)
    severity: Optional[str] = Field(None, pattern=r"^(info|low|medium|high|critical)$")
    data: Optional[dict[str, Any]] = None


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    target_id: int
    pipeline_run_id: Optional[str] = None
    source_tool: str
    finding_type: str
    severity: Optional[str] = None
    data: Optional[dict[str, Any]] = None
    created_at: datetime


class PipelineRunCreate(BaseModel):
    target_id: int
    profile_name: str = "domain_standard"


class PipelineRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    target_id: int
    target_name: Optional[str] = None
    profile_name: str
    status: str
    stage_results: Optional[list[dict[str, Any]]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: Optional[float] = None
    detail: Optional[str] = None
