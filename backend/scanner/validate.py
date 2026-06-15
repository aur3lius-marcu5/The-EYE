import re
from enum import Enum
from ipaddress import ip_address, ip_network


class TargetType(Enum):
    IP = "ip"
    CIDR = "cidr"
    DOMAIN = "domain"


DOMAIN_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)


def validate_target(value: str) -> TargetType:
    value = value.strip()
    if not value:
        raise ValueError("Target value cannot be empty")
    if value.startswith("-"):
        raise ValueError(f"Target value cannot start with '-': {value}")
    if any(c in value for c in ("|", ";", "&", "`", "$", "(", ")", "{", "}", "<", ">", "\n", "\r")):
        raise ValueError(f"Target contains shell metacharacters: {value}")
    try:
        ip_address(value)
        return TargetType.IP
    except ValueError:
        pass
    try:
        ip_network(value, strict=False)
        return TargetType.CIDR
    except ValueError:
        pass
    if DOMAIN_RE.match(value):
        return TargetType.DOMAIN
    raise ValueError(f"Invalid target format: {value}")
