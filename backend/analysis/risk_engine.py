from typing import Any

CVSS_WEIGHTS: dict[str, float] = {
    "critical": 10.0,
    "high": 7.5,
    "medium": 5.0,
    "low": 2.5,
}

SERVICE_RISK: dict[str, float] = {
    "ssh": 3.0,
    "telnet": 8.0,
    "ftp": 6.0,
    "smtp": 4.0,
    "mysql": 5.0,
    "mssql": 6.0,
    "postgresql": 5.0,
    "redis": 7.0,
    "mongodb": 6.0,
    "elasticsearch": 6.0,
    "rdp": 7.0,
    "vnc": 8.0,
    "samba": 6.0,
    "nfs": 7.0,
    "snmp": 6.0,
    "docker": 7.0,
    "k8s": 8.0,
}


def calculate_risk_score(ports: list[dict[str, Any]], cve_data: list[dict[str, Any]]) -> float:
    score = 0.0
    for port in ports:
        service = port.get("service", "").lower()
        score += SERVICE_RISK.get(service, 1.0)
        if port.get("state") == "open":
            score += 0.5
        vulns = port.get("vulnerability_hints", [])
        score += len(vulns) * 2.0
    for cve in cve_data:
        severity = cve.get("severity", "").lower()
        score += CVSS_WEIGHTS.get(severity, 5.0)
    return min(round(score, 1), 100.0)


def calculate_osint_risk(findings: dict[str, Any]) -> float:
    score = 0.0
    subdomains = findings.get("discovery", {}).get("subdomain_count", 0)
    score += subdomains * 0.5
    open_ports = findings.get("scan", {}).get("port_count", 0)
    score += open_ports * 1.0
    cms = findings.get("tech_detect", {}).get("cms", [])
    score += len(cms) * 2.0
    email_count = findings.get("email_recon", {}).get("email_count", 0)
    score += email_count * 1.0
    return min(round(score, 1), 100.0)
