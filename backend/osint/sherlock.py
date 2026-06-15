import asyncio
import json
import logging
from typing import Any, Optional

from backend.core.tool_check import is_tool_available

logger = logging.getLogger(__name__)


async def run_sherlock(username: str, timeout: int = 60) -> dict[str, Any]:
    if not is_tool_available("sherlock"):
        return {"skipped": True, "reason": "binary_not_found", "username": username}
    try:
        proc = await asyncio.create_subprocess_exec(
            "sherlock", username, "--output", "-", "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        if proc.returncode != 0:
            logger.warning(f"sherlock returned {proc.returncode}: {stderr.decode(errors='replace')[:200]}")
        output = stdout.decode(errors="replace")
        results = []
        for line in output.strip().split("\n"):
            if line.strip():
                try:
                    data = json.loads(line)
                    results.append(data)
                except json.JSONDecodeError:
                    pass
        hits = [r for r in results if r.get("status") == "Claimed"]
        return {
            "username": username,
            "total_sites_checked": len(results),
            "hits": len(hits),
            "profiles": [
                {"site": h.get("site", ""), "url": h.get("url", ""), "username": h.get("username", "")}
                for h in hits[:50]
            ],
        }
    except asyncio.TimeoutError:
        logger.warning(f"sherlock timed out for {username}")
        return {"skipped": True, "reason": "timeout", "username": username}
    except FileNotFoundError:
        return {"skipped": True, "reason": "binary_not_found", "username": username}
    except Exception as e:
        logger.warning(f"sherlock failed for {username}: {e}")
        return {"skipped": True, "reason": str(e), "username": username}
