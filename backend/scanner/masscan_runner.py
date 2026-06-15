import asyncio
import json
from typing import Any, Optional

from backend.scanner.validate import validate_target


class MasscanRunner:
    def __init__(self, masscan_path: str = "masscan"):
        self.masscan_path = masscan_path

    async def run(
        self,
        target: str,
        rate: int = 1000,
        ports: str = "1-65535",
    ) -> list[dict[str, Any]]:
        validate_target(target)
        args = [
            self.masscan_path,
            target,
            "-p", ports,
            "--rate", str(rate),
            "--output-format", "json",
            "--output-file", "-",
        ]
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            error_msg = stderr.decode().strip() if stderr else "masscan returned non-zero exit code"
            if "not found" in error_msg:
                raise RuntimeError("masscan is not installed or not found in PATH")
            raise RuntimeError(f"masscan scan failed: {error_msg}")
        hosts: list[dict[str, Any]] = []
        for line in stdout.decode().strip().split("\n"):
            if line.strip():
                try:
                    hosts.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return hosts
