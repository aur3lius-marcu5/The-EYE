import asyncio
import logging
from typing import Any, Optional

from backend.core.tool_check import is_tool_available

logger = logging.getLogger(__name__)


async def whois_lookup(domain: str) -> dict[str, Any]:
    if not is_tool_available("whois"):
        return {"skipped": True, "reason": "binary_not_found"}
    try:
        proc = await asyncio.create_subprocess_exec(
            "whois", domain,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode(errors="replace")[:2000]
    except FileNotFoundError:
        return {"skipped": True, "reason": "binary_not_found"}
    except Exception as e:
        logger.warning(f"whois failed for {domain}: {e}")
        return {"skipped": True, "reason": str(e)}

    data: dict[str, Any] = {"raw": output[:500]}
    for line in output.split("\n"):
        l = line.lower()
        if "registrar:" in l and "registrar" not in data:
            data["registrar"] = line.split(":", 1)[1].strip()
        elif "creation date:" in l and "creation_date" not in data:
            data["creation_date"] = line.split(":", 1)[1].strip()
        elif "registry expiry date:" in l and "expiry_date" not in data:
            data["expiry_date"] = line.split(":", 1)[1].strip()
        elif "registrant name:" in l and "registrant_name" not in data:
            data["registrant_name"] = line.split(":", 1)[1].strip()
        elif "registrant organization:" in l and "registrant_org" not in data:
            data["registrant_org"] = line.split(":", 1)[1].strip()
        elif "name server:" in l:
            ns = line.split(":", 1)[1].strip()
            data.setdefault("name_servers", []).append(ns)
    return data
