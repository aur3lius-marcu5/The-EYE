import re
import socket
from typing import Any

import httpx

DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "10minutemail.com",
    "tempmail.com", "throwaway.email", "yopmail.com",
    "sharklasers.com", "trashmail.com", "mailnator.com",
    "temp-mail.org", "fakeinbox.com", "tempmail.net",
    "dispostable.com", "maildrop.cc", "getairmail.com",
    "emailondeck.com", "spamgourmet.com", "mailsac.com",
    "inboxbear.com", "burnermail.io",
}

EMAIL_PATTERNS = [
    "{first}.{last}@{domain}",
    "{first}{last}@{domain}",
    "{f}{last}@{domain}",
    "{first}{l}@{domain}",
    "{first}_{last}@{domain}",
    "{first}-{last}@{domain}",
    "{first}@{domain}",
    "{last}@{domain}",
]


class EmailRecon:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0, verify=False)

    async def guess_emails(self, domain: str, first: str = "", last: str = "") -> list[dict[str, Any]]:
        guesses = []
        for pattern in EMAIL_PATTERNS:
            email = pattern.format(first=first.lower(), last=last.lower(), f=first[:1].lower() if first else "", l=last[:1].lower() if last else "", domain=domain)
            if first or last:
                guesses.append({"email": email, "pattern": pattern, "source": "guess"})
        return guesses

    async def verify_mx(self, domain: str) -> bool:
        try:
            socket.getaddrinfo(f"mail.{domain}", 25)
            return True
        except (socket.gaierror, OSError):
            pass
        try:
            _, _, ips = socket.gethostbyname_ex(domain)
            for ip in ips:
                try:
                    host = socket.gethostbyaddr(ip)
                    if "mx" in host[0].lower() or "mail" in host[0].lower():
                        return True
                except (socket.herror, OSError):
                    pass
        except Exception:
            pass
        return False

    async def check_breach(self, email: str) -> dict[str, Any]:
        return {"email": email, "breached": False, "message": "HIBP API key required for breach lookup"}

    async def is_disposable(self, domain: str) -> bool:
        return domain.lower() in DISPOSABLE_DOMAINS

    async def investigate(self, domain: str, first: str = "", last: str = "") -> dict[str, Any]:
        guessed = await self.guess_emails(domain, first, last)
        has_mx = await self.verify_mx(domain)
        disposable = await self.is_disposable(domain)
        return {
            "domain": domain,
            "has_mx": has_mx,
            "is_disposable": disposable,
            "guessed_emails": guessed,
            "email_count": len(guessed),
        }

    async def close(self):
        await self.client.aclose()
