import ipaddress
import logging
from typing import Any

from sqlalchemy import select, func

from backend.core.database import async_session
from backend.core.models import Target
from backend.core.config import settings

logger = logging.getLogger(__name__)

MAX_DISCOVERED_TARGETS = settings.pipeline_max_new_targets
DEFAULT_MAX_DEPTH = 1


def _is_ip(s: str) -> bool:
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False


async def _get_global_discovered_count() -> int:
    async with async_session() as db:
        result = await db.execute(select(Target))
        return sum(1 for t in result.scalars() if t.tags and "discovered" in (t.tags if isinstance(t.tags, list) else []))


async def discover_from_pipeline_results(
    origin_target_id: int,
    stage_inputs: dict[str, Any],
) -> list[dict]:
    global_count = await _get_global_discovered_count()
    if global_count >= MAX_DISCOVERED_TARGETS:
        logger.info(f"Global auto-discovery cap ({MAX_DISCOVERED_TARGETS}) already reached, skipping")
        return []

    discovered: list[dict] = []
    existing_ips: set[str] = set()
    existing_domains: set[str] = set()

    async with async_session() as db:
        result = await db.execute(select(Target))
        for t in result.scalars().all():
            if t.domain:
                existing_domains.add(t.domain.lower())
            if t.ip_range:
                existing_ips.add(t.ip_range)

    candidates: list[str] = []

    subdomains = stage_inputs.get("subdomain_enum", {}).get("subdomains", [])
    candidates.extend(subdomains)

    theharvester_data = stage_inputs.get("theharvester", {})
    candidates.extend(theharvester_data.get("hosts", []))
    candidates.extend(theharvester_data.get("ips", []))

    resolved = stage_inputs.get("dns_resolve", {}).get("resolved_ips", [])
    for ip in resolved:
        if isinstance(ip, dict):
            ip_val = ip.get("ip", "")
        else:
            ip_val = str(ip)
        if ip_val:
            candidates.append(ip_val)

    port_scan_data = stage_inputs.get("port_scan", {})
    live_hosts = port_scan_data.get("hosts", [])
    for host in live_hosts:
        if isinstance(host, dict):
            h = host.get("host", "")
            if h:
                candidates.append(h)

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or not isinstance(candidate, str):
            continue
        c = candidate.strip().lower()
        if c in seen:
            continue
        seen.add(c)

        if _is_ip(c) and c not in existing_ips:
            tags = ["discovered"]
            discovered.append({"ip_range": c, "name": c, "domain": None, "tags": tags, "max_depth": DEFAULT_MAX_DEPTH})
            existing_ips.add(c)
        elif not _is_ip(c) and c not in existing_domains:
            tags = ["discovered"]
            discovered.append({"ip_range": None, "name": c, "domain": c, "tags": tags, "max_depth": DEFAULT_MAX_DEPTH})
            existing_domains.add(c)

        if len(discovered) >= MAX_DISCOVERED_TARGETS:
            logger.info(f"Reached auto-discovery cap of {MAX_DISCOVERED_TARGETS}")
            break

    return discovered


async def save_discovered_targets(
    origin_target_id: int,
    discovered: list[dict],
) -> list[int]:
    new_ids: list[int] = []
    async with async_session() as db:
        for item in discovered:
            target = Target(
                name=item["name"],
                ip_range=item.get("ip_range"),
                domain=item.get("domain"),
                tags=item.get("tags"),
                passive_only=1,
                auto_pipeline=0,
                max_depth=item.get("max_depth", DEFAULT_MAX_DEPTH),
            )
            db.add(target)
            await db.flush()
            new_ids.append(target.id)
        await db.commit()
    logger.info(f"Auto-discovered {len(new_ids)} new targets from pipeline on target {origin_target_id}")
    return new_ids
