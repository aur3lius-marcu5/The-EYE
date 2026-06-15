import asyncio
import logging
import socket
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import async_session
from backend.core.models import Finding, Target
from backend.core.tool_check import is_tool_available
from backend.scanner.nmap_runner import NmapRunner
from backend.scanner.fingerprint import fingerprint_services
from backend.analysis.risk_engine import calculate_risk_score
from backend.analysis.cve_lookup import CVELookup
from backend.osint.discovery import SubdomainEnumerator
from backend.osint.tech_detect import TechDetector
from backend.osint.whois_lookup import whois_lookup
from backend.osint.gravatar import bulk_check as gravatar_bulk_check
from backend.osint.sherlock import run_sherlock
from backend.osint.theharvester import run_theharvester
from backend.ai.agents.scan_advisor import advise_scan

logger = logging.getLogger(__name__)
nmapper = NmapRunner()
cve_lookup_obj = CVELookup()


async def _write_finding(
    target_id: int,
    pipeline_run_id: Optional[str],
    source_tool: str,
    finding_type: str,
    data: Any,
    severity: Optional[str] = None,
):
    async with async_session() as db:
        f = Finding(
            target_id=target_id,
            pipeline_run_id=pipeline_run_id,
            source_tool=source_tool,
            finding_type=finding_type,
            severity=severity,
            data=data if isinstance(data, dict) else {"value": str(data)},
        )
        db.add(f)
        await db.commit()


async def run_subdomain_enum(target_id: int, run_id: Optional[str], target_name: str, profile_args: dict) -> dict:
    logger.info(f"Stage subdomain_enum for {target_name}")
    enumerator = SubdomainEnumerator()
    try:
        result = await enumerator.enumerate(target_name)
        for sub in result.get("subdomains", []):
            await _write_finding(target_id, run_id, "crtsh", "subdomain", {"domain": sub}, "info")
        await _write_finding(target_id, run_id, "crtsh", "subdomain_count", {"count": result["subdomain_count"]}, "info")
        return {"subdomains": result.get("subdomains", []), "count": result["subdomain_count"]}
    finally:
        await enumerator.close()


async def run_dns_resolve(target_id: int, run_id: Optional[str], target_name: str, profile_args: dict) -> dict:
    logger.info(f"Stage dns_resolve for {target_name}")
    ips = []
    try:
        _, _, ips_list = socket.gethostbyname_ex(target_name)
        ips = ips_list
        for ip in ips:
            await _write_finding(target_id, run_id, "dns", "dns_record", {"type": "A", "value": ip}, "info")
    except Exception as e:
        logger.warning(f"DNS resolution failed: {e}")
    await _write_finding(target_id, run_id, "dns", "ip_count", {"count": len(ips)}, "info")
    return {"ips": ips}


async def run_whois(target_id: int, run_id: Optional[str], target_name: str, profile_args: dict) -> dict:
    logger.info(f"Stage whois for {target_name}")
    data = await whois_lookup(target_name)
    if data.get("skipped"):
        await _write_finding(target_id, run_id, "whois", "skipped", data, "info")
    else:
        await _write_finding(target_id, run_id, "whois", "whois_record", data, "info")
    return data


async def run_port_scan(target_id: int, run_id: Optional[str], target_name: str, profile_args: dict) -> dict:
    logger.info(f"Stage port_scan for {target_name}")
    if not is_tool_available("nmap"):
        await _write_finding(target_id, run_id, "nmap", "skipped", {"reason": "binary_not_found"}, "info")
        return {"skipped": True}
    args = profile_args.get("args", ["-sV", "-T4"])
    profile = "standard"
    try:
        nmap_result = await nmapper.run(target_name, profile, {"extra_args": args})
        all_ports = []
        for host in nmap_result.get("hosts", []):
            ports = fingerprint_services(host.get("ports", []))
            all_ports.extend(ports)
        for p in all_ports:
            await _write_finding(
                target_id, run_id, "nmap", "open_port",
                {"port": p["port"], "protocol": p.get("protocol", "tcp"), "service": p.get("service", ""),
                 "product": p.get("product", ""), "version": p.get("version", "")},
                "medium" if p.get("state") == "open" else "info",
            )
        await _write_finding(target_id, run_id, "nmap", "port_count", {"count": len(all_ports)}, "info")
        return {"ports": all_ports, "hosts": nmap_result.get("hosts", [])}
    except RuntimeError as e:
        if "not installed" in str(e):
            await _write_finding(target_id, run_id, "nmap", "skipped", {"reason": "not_installed"}, "info")
            return {"skipped": True}
        raise


async def run_tech_detect(target_id: int, run_id: Optional[str], target_name: str, profile_args: dict) -> dict:
    logger.info(f"Stage tech_detect for {target_name}")
    detector = TechDetector()
    try:
        result = await detector.detect(f"https://{target_name}" if not target_name.startswith("http") else target_name)
        if result.get("cms"):
            for c in result["cms"]:
                await _write_finding(target_id, run_id, "httpx", "cms", {"name": c}, "info")
        if result.get("frameworks"):
            for fw in result["frameworks"]:
                await _write_finding(target_id, run_id, "httpx", "framework", {"name": fw}, "info")
        if result.get("server"):
            await _write_finding(target_id, run_id, "httpx", "server_header", {"value": result["server"]}, "info")
        return result
    finally:
        await detector.close()


async def run_cve_lookup(target_id: int, run_id: Optional[str], target_name: str, profile_args: dict, stage_inputs: Optional[dict] = None) -> dict:
    logger.info(f"Stage cve_lookup for {target_name}")
    ports = (stage_inputs or {}).get("run_port_scan", {}).get("ports", [])
    cve_data = []
    for p in ports:
        hints = p.get("vulnerability_hints", [])
        for hint in hints:
            cve_data.append({"id": hint, "severity": "medium", "description": ""})
    for cve in cve_data:
        await _write_finding(target_id, run_id, "cve_lookup", "cve", cve, cve.get("severity", "medium"))
    risk = calculate_risk_score(ports, cve_data)
    await _write_finding(target_id, run_id, "risk_engine", "risk_score", {"score": risk}, "medium" if risk > 50 else "low")
    return {"cves": cve_data, "risk_score": risk}


async def run_email_discovery(target_id: int, run_id: Optional[str], target_name: str, profile_args: dict) -> dict:
    logger.info(f"Stage email_discovery for {target_name}")
    emails = []
    try:
        proc = await asyncio.create_subprocess_exec(
            "theHarvester", "-d", target_name, "-b", "pgp",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate(timeout=30)
        output = stdout.decode(errors="replace")
        for line in output.split("\n"):
            if "@" in line and target_name in line:
                email = line.strip()
                if email not in emails:
                    emails.append(email)
    except Exception:
        pass
    common_formats = [f"admin@{target_name}", f"info@{target_name}", f"contact@{target_name}"]
    for fmt in common_formats:
        if fmt not in emails:
            emails.append(fmt)
    for email in emails:
        await _write_finding(target_id, run_id, "email_pattern", "email", {"email": email}, "info")
    await _write_finding(target_id, run_id, "email_pattern", "email_count", {"count": len(emails)}, "info")
    return {"emails": emails}


async def run_gravatar(target_id: int, run_id: Optional[str], target_name: str, profile_args: dict, stage_inputs: Optional[dict] = None) -> dict:
    logger.info(f"Stage gravatar for {target_name}")
    emails = (stage_inputs or {}).get("run_email_discovery", {}).get("emails", [])
    results = await gravatar_bulk_check(emails)
    for r in results:
        if r.get("found"):
            await _write_finding(target_id, run_id, "gravatar", "social_profile", r, "info")
    hits = [r for r in results if r.get("found")]
    await _write_finding(target_id, run_id, "gravatar", "gravatar_count", {"count": len(hits)}, "info")
    return {"gravatar_hits": hits}


async def run_sherlock_stage(target_id: int, run_id: Optional[str], target_name: str, profile_args: dict, stage_inputs: Optional[dict] = None) -> dict:
    logger.info(f"Stage sherlock for {target_name}")
    usernames = (stage_inputs or {}).get("run_email_discovery", {}).get("emails", [])
    if not usernames:
        await _write_finding(target_id, run_id, "sherlock", "skipped", {"reason": "no_usernames"}, "info")
        return {"skipped": True, "reason": "no_usernames"}
    for user in usernames[:5]:
        name = user.split("@")[0]
        result = await run_sherlock(name)
        if not result.get("skipped"):
            await _write_finding(target_id, run_id, "sherlock", "social_scan", result, "info")
    return {"usernames_checked": [u.split("@")[0] for u in usernames[:5]]}


async def run_theharvester_stage(target_id: int, run_id: Optional[str], target_name: str, profile_args: dict, stage_inputs: Optional[dict] = None) -> dict:
    logger.info(f"Stage theHarvester for {target_name}")
    result = await run_theharvester(target_name)
    if not result.get("skipped"):
        if result.get("emails"):
            await _write_finding(target_id, run_id, "theHarvester", "emails", result["emails"], "info")
        if result.get("hosts"):
            await _write_finding(target_id, run_id, "theHarvester", "hosts", result["hosts"], "info")
        if result.get("ips"):
            await _write_finding(target_id, run_id, "theHarvester", "ips", result["ips"], "info")
    return result


async def run_ai_analysis(target_id: int, run_id: Optional[str], target_name: str, profile_args: dict, stage_inputs: Optional[dict] = None) -> dict:
    logger.info(f"Stage ai_analysis for {target_name}")
    inputs = stage_inputs or {}
    ports = inputs.get("run_port_scan", {}).get("ports", [])
    cves = inputs.get("run_cve_lookup", {}).get("cves", [])
    risk = inputs.get("run_cve_lookup", {}).get("risk_score", 0)
    try:
        result = await advise_scan(target_name, ports, risk, cves)
        content = result.get("content", "")
        await _write_finding(target_id, run_id, "ai_router", "ai_analysis", {"summary": content[:500]}, "info")
        return {"analysis": content}
    except Exception as e:
        logger.warning(f"AI analysis failed: {e}")
        await _write_finding(target_id, run_id, "ai_router", "skipped", {"reason": str(e)}, "info")
        return {"skipped": True}


STAGE_REGISTRY = {
    "subdomain_enum": run_subdomain_enum,
    "dns_resolve": run_dns_resolve,
    "whois": run_whois,
    "port_scan": run_port_scan,
    "tech_detect": run_tech_detect,
    "cve_lookup": run_cve_lookup,
    "email_discovery": run_email_discovery,
    "gravatar": run_gravatar,
    "sherlock": run_sherlock_stage,
    "theharvester": run_theharvester_stage,
    "ai_analysis": run_ai_analysis,
}
