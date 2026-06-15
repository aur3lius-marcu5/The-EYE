from typing import Any

from backend.ai.engine import analyze_with_ai

SYSTEM_PROMPT = """You are an experienced penetration testing advisor. Your role is to:
1. Analyze scan results and identify high-risk services
2. Suggest prioritized attack paths based on exposed services
3. Recommend next scanning steps (e.g., deeper port scans, vulnerability scanning)
4. Provide risk assessment with clear reasoning

Be direct and technical. Focus on actionable intelligence."""


async def advise_scan(target: str, ports: list[dict[str, Any]], risk_score: float, cve_data: list[dict[str, Any]]) -> dict[str, Any]:
    open_ports = [p for p in ports if p.get("state") == "open"]
    port_lines = "\n".join(
        f"- Port {p['port']}/{p.get('protocol', 'tcp')}: {p.get('service', 'unknown')} "
        f"{p.get('product', '')} {p.get('version', '')}"
        f"{' [VULNS: ' + ', '.join(p.get('vulnerability_hints', [])) + ']' if p.get('vulnerability_hints') else ''}"
        for p in open_ports[:20]
    ) or "No open ports found."

    cve_lines = "\n".join(
        f"- {c['id']}: {c.get('description', '')} (severity: {c.get('severity', 'unknown')})"
        for c in cve_data[:10]
    ) or "No CVEs matched."

    user_message = f"""Target: {target}
Risk Score: {risk_score}/100
Open Ports ({len(open_ports)}):
{port_lines}

CVEs Found:
{cve_lines}

Provide a risk assessment and recommended next steps."""

    return await analyze_with_ai(SYSTEM_PROMPT, user_message, {
        "target": target,
        "ports": ports,
        "risk_score": risk_score,
        "cve_data": cve_data,
    })
