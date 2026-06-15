# THE EYE — Automation & OSINT Expansion Plan

Companion document to `implementation-plan.md` and `improvement-plan.md`. This document covers turning the tool from a "scan launcher" into an automated recon + OSINT pipeline.

---

## 1. Recon Pipeline Engine

**Goal:** Chain stages automatically so one action ("Run Full Recon") produces a complete picture, not a series of manual clicks.

**`recon_pipeline.py`** — orchestrates stages based on target type:

- **Domain target:**
  Subdomain enumeration → DNS resolution → port scan on resolved IPs → service/version detection → CVE lookup → web tech fingerprinting on HTTP(S) ports → screenshot/cert grab → AI risk analysis → report
- **IP/CIDR target:**
  Host discovery (ping sweep) → port scan per live host → service detection → CVE lookup → AI analysis

Each stage's output becomes the next stage's input automatically (e.g., discovered subdomains become new `Target` rows that auto-queue for port scanning).

### Pipeline profiles (config, not code)

Define pipelines as YAML/JSON "recon profiles" listing ordered stages, tool, and flags:

```yaml
profile: standard
target_type: domain
stages:
  - id: subdomain_enum
    tool: crtsh
  - id: dns_resolve
    tool: dnsx
    depends_on: [subdomain_enum]
  - id: port_scan
    tool: nmap
    args: ["-sV", "-T4"]
    depends_on: [dns_resolve]
  - id: cve_lookup
    tool: risk_engine
    depends_on: [port_scan]
  - id: ai_analysis
    tool: ai_router
    depends_on: [cve_lookup]
```

This lets new tools be added as plugins without touching pipeline code — each stage just needs a registered input/output contract.

### Auto-chaining via task queue

Each stage runs as its own background task (existing Phase 7 infra). On completion, it enqueues dependent stages automatically rather than requiring the user to manually trigger the next scan.

### Auto-discovery → new targets

When subdomain enum / DNS resolution finds new hosts:
- Auto-create `Target` records flagged `discovered_by: <pipeline_run_id>`
- Optionally auto-queue them through the same pipeline
- **Safety caps required:** max recursion depth, max new targets per run — to prevent runaway scanning from a single seed domain

### Scheduling / continuous recon (optional, v1.1+)

- "Recurring" flag per target → re-run pipeline on a schedule (cron-like)
- Diff results vs. previous run: new open ports, new subdomains, cert changes, new findings
- Basis for a lightweight attack-surface-monitoring mode

---

## 2. Unified Findings Model

**Problem:** Per-tool result tables become hard to correlate and feed into risk scoring/AI analysis as one coherent picture.

**Fix — add a normalized `Finding` table:**

```python
class Finding(Base):
    __tablename__ = "findings"

    id: int
    target_id: int = ForeignKey("targets.id")
    pipeline_run_id: int | None = ForeignKey("pipeline_runs.id")
    source_tool: str          # "nmap", "sherlock", "theharvester", "crtsh", etc.
    finding_type: str         # "open_port", "subdomain", "social_profile", "breach", "dns_record", ...
    severity: str | None      # "info" | "low" | "medium" | "high" | "critical"
    data: JSON                # tool-specific structured payload
    created_at: datetime
```

All recon AND OSINT results land here. `risk_engine.py` and AI analysis consume `Finding` rows generically rather than per-tool-specific tables — new tools just need to map their output into this shape.

---

## 3. OSINT Pipeline

**Goal:** Given a domain, email, or username, automate the same "aggregate everything" process OSINT investigators do manually.

### `osint_pipeline.py` — input-type-driven stages

#### Domain input
- **WHOIS lookup** — registrar, creation date, registrant org (if not privacy-protected)
- **Certificate transparency** (crt.sh) — subdomains + cert history (shared with recon subdomain enum)
- **DNS records** — MX (mail provider), TXT (SPF/DMARC presence — relevant to email spoofing risk), NS
- **Tech fingerprinting** — via httpx response headers/HTML (Wappalyzer-style)
- **Breach/leak domain association** — optional, HaveIBeenPwned domain search (requires paid API key)

#### Email input
- **Format + MX validation** — confirms domain accepts mail
- **Breach check** — HaveIBeenPwned per-email (API key) or local breach corpus as a no-key fallback
- **Email pattern discovery** — given a domain, infer common patterns (`first.last@`, `finitial+last@`) — theHarvester automates much of this via search engines + PGP key servers
- **Gravatar check** — email hash → public profile existence (low effort, often skipped manually)

#### Username input
- **Cross-platform existence sweep** — Sherlock / WhatsMyName style check against 300+ sites, JSON output, subprocess-friendly like nmap
- **Profile metadata pull** — for each hit, optionally fetch public display name/bio/avatar where allowed without auth

### Entity correlation (cross-referencing)

Domain → emails found → usernames found → social profiles found should all link back to one "entity profile" view. Since `Finding` rows all reference `target_id`, an entity can be represented as a group of related targets (domain + its discovered emails/usernames), with a combined view in the UI.

---

## 4. Tooling Summary

| Stage | Tool | Binary/API | Notes |
|---|---|---|---|
| Subdomain enum | crt.sh | HTTPS API (no binary) | Zero-install, also feeds recon |
| Subdomain enum (deeper) | subfinder / amass | Binary | Optional v1.1 |
| DNS resolution | dnsx or stdlib resolver | Binary or library | A/AAAA/MX/TXT/NS |
| HTTP probing | httpx | Binary | Live host + tech detection |
| Screenshots | gowitness | Binary | v1.1 plugin |
| Vuln matching | nmap `--script vuln` / nuclei | Binary | CVE-aware scanning |
| Domain/email/username OSINT | theHarvester | Binary, scriptable | Aggregates many sources in one run |
| Username sweep | Sherlock / WhatsMyName | Binary, JSON output | Subprocess like nmap |
| Breach check | HaveIBeenPwned API | Requires key | Graceful degrade if missing |
| Gravatar | Gravatar hash API | HTTPS, no key | Easy win |

**Recommended v1 scope (zero/low-install):** crt.sh + DNS resolve + nmap + CVE lookup + AI analysis (recon side), plus WHOIS + crt.sh + DNS TXT/MX + Gravatar + email pattern check (OSINT side) — all HTTP/library calls, no extra binaries.

**v1.1 plugins:** subfinder/amass, httpx, nuclei, gowitness, theHarvester, Sherlock, HIBP — each added as a registered pipeline stage once the `Finding` model and stage interface are proven.

---

## 5. Graceful Degradation for Missing Keys/Tools

Same pattern as the AI provider fallback chain (Groq → OpenRouter → Template):

- If HIBP key not configured → skip breach check stage, log `Finding` with `finding_type: "info"`, `data: {"status": "skipped", "reason": "no_api_key"}` so the report shows "not checked" rather than silently omitting it.
- If a binary (Sherlock, subfinder, etc.) isn't installed → pipeline stage marks itself `unavailable` at startup (binary existence check), and is skipped/grayed out in the UI rather than failing the whole pipeline run.

---

## 6. UI: Pipeline Run View

- Single **"Run Full Recon"** button per target → kicks off the full chain (recon + OSINT stages relevant to that target type)
- Live-updating stage timeline (gothic theme — a "ritual" progress visualization fits well: each stage as a sigil/node that lights up on completion)
- Each completed stage shows discovered count (e.g., "12 subdomains found → 12 new targets queued")
- Entity correlation view: domain → linked emails/usernames/social profiles as a graph or grouped list

---

## 7. Safety / Scope Controls

- **Max pipeline depth** — limit auto-discovery recursion (e.g., subdomain → new target → its subdomains stops at depth 2)
- **Max new targets per run** — hard cap to prevent runaway scope expansion from one seed
- **Active vs. passive stage flagging** — mark stages as passive (WHOIS, crt.sh, DNS, breach APIs) vs. active (nmap, ffuf, directory brute-force) so users can run "passive-only" OSINT without touching the target's infrastructure — relevant for engagements with strict scope rules
- **Per-target pipeline opt-out** — ability to exclude specific auto-discovered targets from auto-queuing (e.g., out-of-scope subdomains)

---

## Summary Table

| # | Area | Priority | Effort |
|---|------|----------|--------|
| 1 | Recon pipeline engine + profiles | High | Medium-High |
| 2 | Unified `Finding` model | High | Medium |
| 3 | OSINT pipeline (domain/email/username) | High | Medium |
| 4 | Tooling integration (v1 zero-install set) | High | Low-Medium |
| 4b | Tooling integration (v1.1 plugins) | Medium | Medium (per tool) |
| 5 | Graceful degradation for missing keys/tools | Medium | Low |
| 6 | Pipeline run view UI | Medium | Medium |
| 7 | Safety/scope controls (depth caps, passive/active) | High | Low-Medium |

**Suggested build order:** `Finding` model first (everything else writes to it) → pipeline engine with v1 zero-install stages → OSINT pipeline (shares crt.sh/DNS with recon) → safety caps → pipeline run UI → v1.1 plugin tools incrementally.
