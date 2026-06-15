import hashlib
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


async def check_gravatar(email: str) -> dict[str, Any]:
    hash_str = hashlib.md5(email.lower().encode()).hexdigest()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"https://www.gravatar.com/{hash_str}.json")
            if r.status_code == 200:
                data = r.json()
                entry = data.get("entry", [{}])[0]
                return {
                    "email": email,
                    "hash": hash_str,
                    "found": True,
                    "display_name": entry.get("displayName", ""),
                    "profile_url": entry.get("profileUrl", ""),
                    "avatar_url": entry.get("thumbnailUrl", ""),
                    "preferred_username": entry.get("preferredUsername", ""),
                }
    except Exception as e:
        logger.debug(f"Gravatar check failed for {email}: {e}")
    return {"email": email, "hash": hash_str, "found": False}


async def bulk_check(emails: list[str], max_check: int = 10) -> list[dict[str, Any]]:
    results = []
    for email in emails[:max_check]:
        result = await check_gravatar(email)
        results.append(result)
    return results
