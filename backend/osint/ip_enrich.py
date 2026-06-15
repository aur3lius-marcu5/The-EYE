import asyncio
import socket
from typing import Any, Optional

import httpx


class IPEnricher:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0, verify=False)

    async def reverse_dns(self, ip: str) -> Optional[str]:
        try:
            host, _, _ = socket.gethostbyaddr(ip)
            return host
        except (socket.herror, OSError):
            return None

    async def geo_location(self, ip: str) -> dict[str, Any]:
        try:
            r = await self.client.get(f"http://ip-api.com/json/{ip}")
            if r.status_code == 200:
                data = r.json()
                if data.get("status") == "success":
                    return data
        except Exception:
            pass
        return {}

    async def enrich(self, ip: str) -> dict[str, Any]:
        rdns = await self.reverse_dns(ip)
        geo = await self.geo_location(ip)
        return {
            "ip": ip,
            "reverse_dns": rdns,
            "country": geo.get("country", ""),
            "country_code": geo.get("countryCode", ""),
            "region": geo.get("regionName", ""),
            "city": geo.get("city", ""),
            "isp": geo.get("isp", ""),
            "org": geo.get("org", ""),
            "as": geo.get("as", ""),
            "lat": geo.get("lat"),
            "lon": geo.get("lon"),
        }

    async def close(self):
        await self.client.aclose()
