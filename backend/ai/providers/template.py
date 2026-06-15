from typing import Any


SCAN_SUMMARY_TEMPLATE = """
=== SCAN ANALYSIS ===
Target: {target}
Profile: {profile}
Ports Found: {port_count}
Risk Score: {risk_score}/100

Key Findings:
{findings}

Recommendations:
{recommendations}
"""

VULN_TEMPLATE = """
=== VULNERABILITY ASSESSMENT ===
Service: {service} {version}
{details}
Severity: {severity}
"""


class TemplateFallback:
    name = "template"

    async def chat(self, messages: list[dict[str, str]], context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        last_msg = messages[-1]["content"] if messages else ""
        if "scan" in last_msg.lower() or context.get("scan_data"):
            return {
                "content": self._generate_scan_response(context),
                "model": "template",
                "tokens": {},
                "provider": "template",
            }
        if "osint" in last_msg.lower() or context.get("osint_data"):
            return {
                "content": self._generate_osint_response(context),
                "model": "template",
                "tokens": {},
                "provider": "template",
            }
        return {
            "content": "Analysis unavailable. Configure AI provider API keys for detailed intelligence.",
            "model": "template",
            "tokens": {},
            "provider": "template",
        }

    def _generate_scan_response(self, context: dict[str, Any]) -> str:
        ports = context.get("ports", [])
        findings = "\n".join(
            f"- Port {p.get('port')}/{p.get('protocol', 'tcp')}: {p.get('service', 'unknown')} "
            f"{p.get('product', '')} {p.get('version', '')}"
            for p in ports[:10]
        ) or "No open ports found."
        recommendations = "\n".join(
            f"- {rec}" for rec in [
                "Review all open ports and close unnecessary ones",
                "Update outdated service versions",
                "Enable firewall rules to restrict access",
                "Run a full vulnerability scan on identified services",
            ]
        )
        return SCAN_SUMMARY_TEMPLATE.format(
            target=context.get("target", "N/A"),
            profile=context.get("profile", "standard"),
            port_count=len(ports),
            risk_score=context.get("risk_score", 0),
            findings=findings,
            recommendations=recommendations,
        )

    def _generate_osint_response(self, context: dict[str, Any]) -> str:
        parts = []
        discovery = context.get("discovery", {})
        if discovery.get("subdomains"):
            parts.append(f"Discovered {len(discovery['subdomains'])} subdomains")
        tech = context.get("tech_detect", {})
        if tech.get("cms"):
            parts.append(f"CMS detected: {', '.join(tech['cms'])}")
        if tech.get("frameworks"):
            parts.append(f"Frameworks: {', '.join(tech['frameworks'])}")
        if not parts:
            parts.append("No significant OSINT findings.")
        return "=== OSINT ANALYSIS ===\n" + "\n".join(parts)
