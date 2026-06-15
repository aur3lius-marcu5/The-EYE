import csv
import json
import io
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader("backend.reporting", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_html(target: str, scan_data: dict[str, Any], osint_data: dict[str, Any], ai_analysis: str = "") -> str:
    template = env.get_template("report.html")
    return template.render(
        target=target,
        scan_data=scan_data,
        osint_data=osint_data,
        ai_analysis=ai_analysis,
    )


def export_json(target: str, scan_data: dict[str, Any], osint_data: dict[str, Any]) -> str:
    return json.dumps({
        "target": target,
        "scan": scan_data,
        "osint": osint_data,
    }, indent=2)


def export_csv(ports: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Port", "Protocol", "State", "Service", "Product", "Version"])
    for port in ports:
        writer.writerow([
            port.get("port", ""),
            port.get("protocol", "tcp"),
            port.get("state", ""),
            port.get("service", ""),
            port.get("product", ""),
            port.get("version", ""),
        ])
    return output.getvalue()
