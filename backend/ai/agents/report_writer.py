from typing import Any

from backend.ai.engine import analyze_with_ai

SYSTEM_PROMPT = """You are a technical report writer specializing in security assessments. Your role is to:
1. Produce clear, structured executive summaries from scan and OSINT data
2. Highlight critical findings with business impact context
3. Provide remediation recommendations
4. Maintain professional, authoritative tone suitable for client delivery"""


async def write_report(target: str, scan_data: dict[str, Any], osint_data: dict[str, Any]) -> dict[str, Any]:
    ports = scan_data.get("ports", [])
    risk_score = scan_data.get("risk_score", 0)
    open_ports = [p for p in ports if p.get("state") == "open"]

    discovery = osint_data.get("discovery", {})
    tech = osint_data.get("tech_detect", {})

    user_message = f"""Target: {target}
Risk Score: {risk_score}/100
Open Ports: {len(open_ports)}
Services: {', '.join(set(p.get('service', '') for p in open_ports if p.get('service')))}
Subdomains: {discovery.get('subdomain_count', 0)}
Tech Stack: {', '.join(tech.get('cms', []) + tech.get('frameworks', [])) or 'Unknown'}

Generate an executive summary and technical findings report."""

    return await analyze_with_ai(SYSTEM_PROMPT, user_message, {
        "scan_data": scan_data,
        "osint_data": osint_data,
        "target": target,
    })
