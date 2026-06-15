import hashlib
import re
from typing import Any, Optional

import httpx

CMS_PATTERNS: dict[str, list[str]] = {
    "WordPress": [
        r"/wp-content/", r"/wp-admin/", r"/wp-includes/",
        r"<meta name=\"generator\" content=\"WordPress",
    ],
    "Drupal": [
        r"/sites/default/", r"Drupal\.", r"SESS[0-9a-f]{32}",
    ],
    "Joomla": [
        r"/components/", r"/modules/", r"/templates/",
        r"<meta name=\"generator\" content=\"Joomla",
    ],
    "Magento": [
        r"/skin/frontend/", r"/media/catalog/",
        r"<meta name=\"generator\" content=\"Magento",
    ],
    "Laravel": [
        r"Laravel", r"_token=", r"laravel_session",
    ],
}

FRAMEWORK_PATTERNS: dict[str, list[str]] = {
    "React": [r"__REACT_DEVTOOLS_GLOBAL_HOOK__", r"react\.js", r"react\.min\.js"],
    "Angular": [r"ng-version", r"angular\.js", r"angular\.min\.js"],
    "Vue": [r"vue\.js", r"vue\.min\.js", r"__VUE_DEVTOOLS_GLOBAL_HOOK__"],
    "Next.js": [r"__NEXT_DATA__", r"/_next/static/"],
    "Nuxt": [r"__NUXT__", r"/_nuxt/"],
    "jQuery": [r"jquery\.js", r"jquery\.min\.js"],
    "Bootstrap": [r"bootstrap\.css", r"bootstrap\.min\.css", r"bootstrap\.js"],
    "Tailwind CSS": [r"tailwindcss", r"\.tw-"],
}


class TechDetector:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0, verify=False, follow_redirects=True)

    async def detect(self, url: str) -> dict[str, Any]:
        result: dict[str, Any] = {
            "url": url,
            "headers": {},
            "cms": [],
            "frameworks": [],
            "favicon_hash": None,
            "server": None,
            "technologies": [],
        }
        try:
            r = await self.client.get(url)
            result["status_code"] = r.status_code
            headers = dict(r.headers)
            result["headers"] = {k.lower(): v for k, v in headers.items()}
            if "server" in headers:
                result["server"] = headers["server"]
            if "x-powered-by" in headers:
                result["technologies"].append(f"X-Powered-By: {headers['x-powered-by']}")
            body = r.text
            result["cms"] = self._detect_cms(body, headers)
            result["frameworks"] = self._detect_frameworks(body)
            favicon_url = self._find_favicon(body, url)
            if favicon_url:
                result["favicon_hash"] = await self._hash_favicon(favicon_url)
            result["title"] = self._extract_title(body)
        except Exception:
            pass
        return result

    def _detect_cms(self, body: str, headers: dict) -> list[str]:
        found = []
        for cms, patterns in CMS_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, body, re.IGNORECASE):
                    found.append(cms)
                    break
        if "x-generator" in headers:
            gen = headers["x-generator"]
            for cms in CMS_PATTERNS:
                if cms.lower() in gen.lower():
                    if cms not in found:
                        found.append(cms)
        return found

    def _detect_frameworks(self, body: str) -> list[str]:
        found = []
        for fw, patterns in FRAMEWORK_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, body, re.IGNORECASE):
                    found.append(fw)
                    break
        return found

    def _find_favicon(self, body: str, base_url: str) -> Optional[str]:
        m = re.search(r'<link[^>]*rel=["\'](?:shortcut )?icon["\'][^>]*href=["\']([^"\']+)["\']', body, re.IGNORECASE)
        if m:
            href = m.group(1)
            if href.startswith("http"):
                return href
            from urllib.parse import urljoin
            return urljoin(base_url, href)
        return None

    async def _hash_favicon(self, url: str) -> Optional[str]:
        try:
            r = await self.client.get(url)
            if r.status_code == 200:
                return hashlib.md5(r.content).hexdigest()
        except Exception:
            pass
        return None

    def _extract_title(self, body: str) -> Optional[str]:
        m = re.search(r'<title[^>]*>(.*?)</title>', body, re.IGNORECASE | re.DOTALL)
        return m.group(1).strip() if m else None

    async def close(self):
        await self.client.aclose()
