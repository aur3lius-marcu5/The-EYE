from typing import Any, Optional

import httpx

KNOWN_CVES: dict[str, list[dict[str, str]]] = {
    "Apache 2.4.49": [
        {"id": "CVE-2021-41773", "severity": "critical", "description": "Path traversal and file disclosure"},
        {"id": "CVE-2021-42013", "severity": "critical", "description": "Path traversal with CGI bypass"},
    ],
    "OpenSSH 7.2p1": [
        {"id": "CVE-2016-6210", "severity": "medium", "description": "User enumeration via timing"},
    ],
    "nginx 1.20.0": [
        {"id": "CVE-2021-23017", "severity": "medium", "description": "DNS resolver use-after-free"},
    ],
    "vsftpd 2.3.4": [
        {"id": "CVE-2011-2523", "severity": "critical", "description": "Backdoor command execution"},
    ],
    "ProFTPD 1.3.5": [
        {"id": "CVE-2015-3306", "severity": "high", "description": "File copy RCE via mod_copy"},
    ],
    "Samba 3.5.0": [
        {"id": "CVE-2017-7494", "severity": "critical", "description": "Remote code execution via SMB"},
    ],
}


class CVELookup:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0, verify=False)

    async def lookup(self, service: str, version: str = "") -> list[dict[str, str]]:
        key = f"{service} {version}".strip() if version else service
        local = KNOWN_CVES.get(key, [])
        if local:
            return local
        try:
            query = f"{service} {version}".strip()
            r = await self.client.get(f"https://cve.circl.lu/api/search/{query}")
            if r.status_code == 200:
                data = r.json()
                return [
                    {"id": cve.get("id", ""), "severity": cve.get("cvss", "unknown"), "description": cve.get("summary", "")[:200]}
                    for cve in data.get("data", [])[:5]
                ]
        except Exception:
            pass
        return []

    async def search_product(self, product: str, version: str = "") -> list[dict[str, str]]:
        key = f"{product} {version}".strip() if version else product
        local = KNOWN_CVES.get(key, [])
        if local:
            return local
        return []

    async def close(self):
        await self.client.aclose()
