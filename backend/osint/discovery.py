import asyncio
import json
import socket
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

BUILTIN_SUBDOMAINS = [
    "www", "mail", "webmail", "admin", "blog", "dev", "test",
    "api", "app", "stage", "beta", "vpn", "remote", "portal",
    "intranet", "jenkins", "gitlab", "jira", "confluence",
    "docs", "wiki", "status", "statuspage", "help", "support",
    "cdn", "static", "assets", "img", "images", "css", "js",
    "ftp", "sftp", "smtp", "imap", "pop3", "ns1", "ns2",
    "ns3", "mx1", "mx2", "owa", "exchange", "autodiscover",
    "lyncdiscover", "sip", "meet", "conference",
    "calendar", "drive", "cloud", "files", "sharepoint",
    "moodle", "blackboard", "canvas", "cpanel", "whm",
    "phpmyadmin", "phpadmin", "pma", "webmin", "server",
    "monitor", "grafana", "prometheus", "kibana", "elastic",
    "k8s", "kubernetes", "docker", "registry", "nexus",
    "artifactory", "sonar", "sonarqube", "swagger", "api-docs",
    "redmine", "trello", "slack", "chat", "rocketchat",
    "mattermost", "discourse", "forum", "community",
    "shop", "store", "cart", "checkout", "payment",
    "secure", "ssl", "cert", "ca", "pki",
    "radius", "ldap", "ad", "dc", "domain",
    "print", "printer", "scan", "scanner",
    "backup", "backups", "archive", "logs", "log",
    "db", "database", "mysql", "pgsql", "mongodb", "redis",
    "memcache", "rabbitmq", "kafka", "zookeeper",
    "ansible", "puppet", "chef", "salt", "saltstack",
    "terraform", "packer", "vagrant",
    "phone", "mobile", "m", "i", "amp", "mobi",
    "partner", "partners", "vendor", "vendors",
    "reseller", "affiliate", "affiliates",
    "news", "newsletter", "media", "video", "tv",
    "radio", "stream", "streaming", "live",
    "download", "downloads", "upload", "uploads",
    "proxy", "gateway", "router", "switch", "firewall",
    "wifi", "wireless", "ap", "accesspoint",
    "noc", "netops", "network", "ops",
    "hr", "humanresources", "payroll", "benefits",
    "legal", "compliance", "audit", "risk",
    "analytics", "metrics", "stats", "statistics",
    "data", "datascience", "ml", "ai", "bot",
    "iot", "sensor", "sensors", "device", "devices",
    "api-gateway", "api-gw", "gw", "edge",
    "sandbox", "playground", "demo", "trial",
    "training", "learn", "academy", "edu", "education",
    "research", "labs", "lab", "innovation",
    "patches", "update", "updates", "upgrade",
    "feedback", "survey", "surveys", "vote",
    "jobs", "career", "careers", "recruit",
    "press", "pr", "newsroom", "media-kit",
    "investors", "ir", "investor", "financial",
    "corp", "corporate", "company", "about",
    "office", "offices", "location", "locations",
    "contact", "contacts", "support", "helpdesk",
    "service", "services", "solutions",
    "platform", "product", "products", "feature",
    "changelog", "releases", "release", "roadmap",
    "terms", "privacy", "security", "gdpr",
    "sitemap", "robots", "crossdomain",
    "graphql", "grpc", "rest", "soap", "xmlrpc",
    "ws", "websocket", "sse", "events",
    "auth", "oauth", "saml", "oidc", "sso",
    "idp", "identity", "login", "signin", "signup",
    "register", "registration", "activate",
    "password", "reset", "forgot", "recover",
    "profile", "account", "accounts", "settings",
    "dashboard", "home", "index", "default",
    "landing", "landing-page", "lp",
    "campaign", "campaigns", "marketing",
    "go", "redirect", "redirects", "link",
    "short", "shortener", "tiny", "tinyurl",
    "internal", "external", "public", "private",
    "production", "prod", "staging", "dev",
    "qa", "quality", "uat", "testing",
    "monolith", "soa", "microservice", "service",
]

DNS_RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME", "SPF", "DMARC"]


class SubdomainEnumerator:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0, verify=False)

    async def crtsh(self, domain: str) -> list[str]:
        try:
            r = await self.client.get(f"https://crt.sh/?q=%25.{domain}&output=json")
            if r.status_code != 200:
                return []
            entries = r.json()
            subdomains = set()
            for entry in entries:
                name = entry.get("name_value", "")
                for n in name.split("\n"):
                    n = n.strip().lower()
                    if n.endswith(f".{domain}") and n != domain:
                        subdomains.add(n)
            return list(subdomains)
        except Exception:
            return []

    async def dns_bruteforce(self, domain: str) -> list[str]:
        found = []
        for sub in BUILTIN_SUBDOMAINS:
            fqdn = f"{sub}.{domain}"
            try:
                socket.getaddrinfo(fqdn, 80, socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
                found.append(fqdn)
            except (socket.gaierror, OSError):
                pass
            await asyncio.sleep(0)
        return found

    async def resolve_dns(self, domain: str) -> dict[str, list[str]]:
        records: dict[str, list[str]] = {}
        for rtype in DNS_RECORD_TYPES:
            try:
                _, _, result_list = socket.gethostbyname_ex(domain)
                if result_list:
                    records[rtype] = result_list
            except (socket.gaierror, OSError):
                pass
        try:
            txt_records = []
            _, _, result_list = socket.gethostbyname_ex(domain)
            for ip in result_list:
                try:
                    host = socket.gethostbyaddr(ip)
                    txt_records.append(f"PTR: {host[0]}")
                except (socket.herror, OSError):
                    pass
            if txt_records:
                records["PTR"] = txt_records
        except Exception:
            pass
        return records

    async def enumerate(self, domain: str) -> dict[str, Any]:
        crtsh_results, brute_results = await asyncio.gather(
            self.crtsh(domain),
            self.dns_bruteforce(domain),
        )
        all_subdomains = list(set(crtsh_results + brute_results))
        all_subdomains.sort()
        dns_records = await self.resolve_dns(domain)
        return {
            "domain": domain,
            "subdomains": all_subdomains,
            "subdomain_count": len(all_subdomains),
            "dns_records": dns_records,
            "sources": {
                "crtsh": len(crtsh_results),
                "dns_bruteforce": len(brute_results),
            },
        }

    async def close(self):
        await self.client.aclose()
