import subprocess
import re

class NmapScanner:
    def scan(self, ip: str):
        cmd = ["nmap", "-sS", "-T3", "--top-ports", "1000", ip]

        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout

        ports = []
        services = {}

        for line in output.splitlines():
            match = re.match(r"(\\d+)/tcp\\s+open\\s+(\\S+)", line)
            if match:
                port = int(match.group(1))
                service = match.group(2)
                ports.append(port)
                services[port] = service

        return {
            "alive": len(ports) > 0,
            "ports": ports,
            "services": services
        }
