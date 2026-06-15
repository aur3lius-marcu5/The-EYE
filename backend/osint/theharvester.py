import asyncio
import json
import logging
import os
import tempfile
from typing import Any, Optional

from backend.core.tool_check import is_tool_available

logger = logging.getLogger(__name__)


async def run_theharvester(domain: str, sources: str = "pgp", timeout: int = 60) -> dict[str, Any]:
    if not is_tool_available("theHarvester"):
        return {"skipped": True, "reason": "binary_not_found", "domain": domain}
    tmp_file = os.path.join(tempfile.gettempdir(), f"theharvester_{domain.replace('.', '_')}.json")
    try:
        proc = await asyncio.create_subprocess_exec(
            "theHarvester", "-d", domain, "-b", sources, "-f", tmp_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"theHarvester timed out for {domain}")
        return {"skipped": True, "reason": "timeout", "domain": domain}
    except FileNotFoundError:
        return {"skipped": True, "reason": "binary_not_found", "domain": domain}
    except Exception as e:
        logger.warning(f"theHarvester failed for {domain}: {e}")
        return {"skipped": True, "reason": str(e), "domain": domain}

    result: dict[str, Any] = {"domain": domain, "source": sources, "hosts": [], "emails": [], "ips": []}
    if os.path.exists(tmp_file):
        try:
            with open(tmp_file) as f:
                data = json.load(f)
            result["hosts"] = data.get("hosts", [])
            result["emails"] = data.get("emails", [])
            result["ips"] = data.get("ips", [])
            os.remove(tmp_file)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to parse theHarvester output: {e}")
    return result
