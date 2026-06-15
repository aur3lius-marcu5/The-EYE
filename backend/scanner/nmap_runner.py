import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Callable, Optional

from backend.scanner.validate import validate_target, TargetType


NMAP_PROFILES = {
    "quick": ["-sn", "-sS", "-sV", "-T4", "--top-ports", "100"],
    "standard": ["-sS", "-sV", "-T3", "--top-ports", "1000"],
    "deep": ["-sS", "-sV", "-sC", "-O", "-T3", "-p-"],
    "stealth": ["-sS", "-T2", "--top-ports", "1000"],
}


class NmapRunner:
    def __init__(self, nmap_path: str = "nmap"):
        self.nmap_path = nmap_path

    async def run(
        self,
        target: str,
        profile: str = "standard",
        options: Optional[dict[str, Any]] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> dict[str, Any]:
        validate_target(target)
        profile_args = NMAP_PROFILES.get(profile, NMAP_PROFILES["standard"]).copy()
        if options and options.get("extra_args"):
            profile_args.extend(options["extra_args"])
        if options and options.get("ports"):
            profile_args = [a for a in profile_args if a not in ("--top-ports", "100", "1000")]
            profile_args.extend(["-p", options["ports"]])
        args = [self.nmap_path] + profile_args + ["-oX", "-", target]
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            error_msg = stderr.decode().strip() if stderr else "nmap returned non-zero exit code"
            if "not found" in error_msg or "not recognized" in error_msg:
                raise RuntimeError("nmap is not installed or not found in PATH")
            raise RuntimeError(f"nmap scan failed: {error_msg}")
        return parse_nmap_output(stdout.decode())


def parse_nmap_output(xml_output: str) -> dict[str, Any]:
    root = ET.fromstring(xml_output)
    result: dict[str, Any] = {
        "hosts": [],
        "raw": xml_output,
    }
    for host in root.findall(".//host"):
        host_info: dict[str, Any] = {"ports": []}
        addr = host.find("address")
        if addr is not None:
            host_info["ip"] = addr.get("addr", "")
        os_elem = host.find("os/osmatch")
        if os_elem is not None:
            host_info["os"] = os_elem.get("name", "")
        for port in host.findall(".//port"):
            port_info: dict[str, Any] = {
                "port": int(port.get("portid", 0)),
                "protocol": port.get("protocol", "tcp"),
            }
            state = port.find("state")
            if state is not None:
                port_info["state"] = state.get("state", "")
            service = port.find("service")
            if service is not None:
                port_info["service"] = service.get("name", "")
                port_info["product"] = service.get("product", "")
                port_info["version"] = service.get("version", "")
            host_info["ports"].append(port_info)
        result["hosts"].append(host_info)
    result["port_count"] = sum(len(h["ports"]) for h in result["hosts"])
    return result
