import logging
from collections import defaultdict
from typing import Any

from sqlalchemy import select, func

from backend.core.database import async_session
from backend.core.models import Finding, PipelineRun, Target

logger = logging.getLogger(__name__)


async def correlate_all() -> dict[str, Any]:
    async with async_session() as db:
        targets_result = await db.execute(select(Target))
        targets = targets_result.scalars().all()

        findings_result = await db.execute(
            select(Finding).where(Finding.finding_type.notin_(["skipped", "gravatar_count"]))
        )
        findings = findings_result.scalars().all()

    ip_to_targets: dict[str, list[int]] = defaultdict(list)
    domain_to_targets: dict[str, list[int]] = defaultdict(list)
    email_to_targets: dict[str, list[int]] = defaultdict(list)

    for t in targets:
        if t.ip_range:
            ip_to_targets[t.ip_range].append(t.id)
        if t.domain:
            domain_to_targets[t.domain].append(t.id)

    for f in findings:
        payload = f.data or {}
        if f.finding_type == "whois_record":
            if payload.get("name_servers"):
                for _ns in payload["name_servers"]:
                    pass
        elif f.finding_type in ("ip", "resolved_ip"):
            ip_val = payload.get("ip") or payload.get("value", "")
            if ip_val:
                ip_to_targets[ip_val].append(f.target_id)
        elif f.finding_type == "subdomain":
            sd = payload.get("subdomain", "")
            if sd:
                domain_to_targets[sd].append(f.target_id)
        elif f.finding_type in ("email", "social_profile"):
            em = payload.get("email", "")
            if em:
                email_to_targets[em].append(f.target_id)

    correlations: dict[str, Any] = {
        "shared_ips": [],
        "shared_domains": [],
        "shared_emails": [],
    }

    for ip, tids in ip_to_targets.items():
        unique = list(set(tids))
        if len(unique) > 1:
            correlations["shared_ips"].append({"value": ip, "target_ids": unique, "count": len(unique)})

    for domain, tids in domain_to_targets.items():
        unique = list(set(tids))
        if len(unique) > 1:
            correlations["shared_domains"].append({"value": domain, "target_ids": unique, "count": len(unique)})

    for email, tids in email_to_targets.items():
        unique = list(set(tids))
        if len(unique) > 1:
            correlations["shared_emails"].append({"value": email, "target_ids": unique, "count": len(unique)})

    correlations["total_correlations"] = (
        len(correlations["shared_ips"])
        + len(correlations["shared_domains"])
        + len(correlations["shared_emails"])
    )

    return correlations


async def get_dashboard_stats() -> dict[str, Any]:
    async with async_session() as db:
        target_count = (await db.execute(select(func.count(Target.id)))).scalar() or 0
        targets_result = await db.execute(select(Target))
        discovered_count = sum(1 for t in targets_result.scalars() if t.tags and "discovered" in (t.tags if isinstance(t.tags, list) else []))

        pr_count = (await db.execute(select(func.count(PipelineRun.id)))).scalar() or 0
        pr_completed = (await db.execute(
            select(func.count(PipelineRun.id)).where(PipelineRun.status == "completed")
        )).scalar() or 0
        pr_running = (await db.execute(
            select(func.count(PipelineRun.id)).where(PipelineRun.status == "running")
        )).scalar() or 0

    return {
        "total_targets": target_count,
        "discovered_targets": discovered_count,
        "total_pipeline_runs": pr_count,
        "completed_runs": pr_completed,
        "running_runs": pr_running,
    }
