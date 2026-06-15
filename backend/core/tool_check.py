import asyncio
import shutil
from typing import Optional

TOOL_AVAILABLE: dict[str, bool] = {}
TOOL_CHECK_INTERVAL = 300


async def check_tool(name: str, check_args: Optional[list[str]] = None) -> bool:
    if shutil.which(name):
        if check_args:
            proc = await asyncio.create_subprocess_exec(
                name, *check_args,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            rc = await proc.wait()
            return rc == 0
        return True
    return False


async def refresh_tool_availability():
    TOOL_AVAILABLE["nmap"] = await check_tool("nmap", ["--version"])
    TOOL_AVAILABLE["masscan"] = await check_tool("masscan", ["--version"])
    TOOL_AVAILABLE["whois"] = await check_tool("whois", ["--version"])
    TOOL_AVAILABLE["sherlock"] = await check_tool("sherlock", ["--version"])
    TOOL_AVAILABLE["theharvester"] = await check_tool("theHarvester", ["-h"])


def is_tool_available(name: str) -> bool:
    return TOOL_AVAILABLE.get(name, False)
