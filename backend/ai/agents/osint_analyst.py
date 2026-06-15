from typing import Any

from backend.ai.engine import analyze_with_ai

SYSTEM_PROMPT = """You are an OSINT intelligence analyst. Your role is to:
1. Correlate findings across OSINT modules (subdomains, DNS, tech stack, emails)
2. Identify high-value targets and exposed infrastructure
3. Suggest reconnaissance next steps
4. Prioritize findings by potential impact

Be concise and actionable. Focus on what matters for the engagement."""


async def analyze_osint(osint_data: dict[str, Any]) -> dict[str, Any]:
    discovery = osint_data.get("discovery", {})
    tech = osint_data.get("tech_detect", {})
    email = osint_data.get("email_recon", {})

    subdomain_count = discovery.get("subdomain_count", 0)
    subdomains = discovery.get("subdomains", [])[:10]
    dns_records = discovery.get("dns_records", {})
    cms = tech.get("cms", [])
    frameworks = tech.get("frameworks", [])
    server = tech.get("server", "unknown")
    emails = email.get("guessed_emails", [])[:5]

    user_message = f"""Subdomains ({subdomain_count}): {', '.join(subdomains[:10]) if subdomains else 'None'}
DNS Records: {', '.join(f'{k}: {v}' for k, v in dns_records.items()) if dns_records else 'None'}
CMS: {', '.join(cms) if cms else 'None detected'}
Frameworks: {', '.join(frameworks) if frameworks else 'None detected'}
Server: {server}
Emails: {', '.join(e['email'] for e in emails) if emails else 'None found'}

Provide intelligence assessment and recommended next recon steps."""

    return await analyze_with_ai(SYSTEM_PROMPT, user_message, {"osint_data": osint_data})
