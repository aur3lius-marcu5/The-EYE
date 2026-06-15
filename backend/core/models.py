from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from backend.core.database import Base


class Target(Base):
    __tablename__ = "targets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    ip_range = Column(String(255), nullable=True)
    domain = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    passive_only = Column(Integer, default=0)
    auto_pipeline = Column(Integer, default=1)
    max_depth = Column(Integer, default=2)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Scan(Base):
    __tablename__ = "scans"
    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    task_id = Column(String(255), nullable=True)
    status = Column(String(50), default="pending")
    scan_profile = Column(String(50), nullable=False)
    options = Column(JSON, nullable=True)
    ports = Column(JSON, nullable=True)
    risk_score = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    cve_data = Column(JSON, nullable=True)
    raw_output = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    heartbeat_at = Column(DateTime, nullable=True)


class OSINTResult(Base):
    __tablename__ = "osint_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    task_id = Column(String(255), nullable=True)
    status = Column(String(50), default="pending")
    module = Column(String(50), nullable=False)
    source = Column(String(50), nullable=True)
    raw_data = Column(JSON, nullable=True)
    findings = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    heartbeat_at = Column(DateTime, nullable=True)


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    scan_ids = Column(JSON, nullable=True)
    osint_ids = Column(JSON, nullable=True)
    report_type = Column(String(50), nullable=False)
    format = Column(String(10), nullable=False)
    file_path = Column(String(500), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)


class Finding(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    pipeline_run_id = Column(String(255), nullable=True)
    source_tool = Column(String(100), nullable=False)
    finding_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=True)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    profile_name = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")
    stage_results = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=True)
    osint_id = Column(Integer, ForeignKey("osint_results.id"), nullable=True)
    agent_type = Column(String(50), nullable=False)
    prompt = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    model_used = Column(String(255), nullable=True)
    tokens_used = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
