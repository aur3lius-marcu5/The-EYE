from typing import Any

VULNERABILITY_HINTS: dict[str, list[str]] = {
    "Apache 2.4.49": ["CVE-2021-41773", "CVE-2021-42013"],
    "Apache 2.4.50": ["CVE-2021-42013"],
    "OpenSSH 7.2p1": ["CVE-2016-6210"],
    "OpenSSH 7.2": ["CVE-2016-6210"],
    "nginx 1.20.0": ["CVE-2021-23017"],
    "Microsoft IIS 8.5": ["CVE-2023-36411"],
    "Microsoft IIS 10.0": ["CVE-2023-36411"],
    "vsftpd 2.3.4": ["CVE-2011-2523"],
    "ProFTPD 1.3.5": ["CVE-2015-3306"],
    "Samba 3.5.0": ["CVE-2017-7494"],
}


def fingerprint_services(ports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for port in ports:
        service = port.get("service", "")
        product = port.get("product", "")
        version = port.get("version", "")
        key = f"{product} {version}".strip() if product and version else None
        if key and key in VULNERABILITY_HINTS:
            port["vulnerability_hints"] = VULNERABILITY_HINTS[key]
        elif f"{service} {version}".strip() in VULNERABILITY_HINTS:
            port["vulnerability_hints"] = VULNERABILITY_HINTS[f"{service} {version}".strip()]
        else:
            port["vulnerability_hints"] = []
    return ports
