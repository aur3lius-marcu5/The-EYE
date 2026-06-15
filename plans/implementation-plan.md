# THE EYE — Implementation Plan

## Design Decisions (Confirmed)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend approach | Full rebuild with Vite + Tailwind | Clean slate matching the new gothic direction; existing React app too tightly coupled to the old theme |
| shadcn/ui | Hand-craft all components | shadcn's neutral/clean styling conflicts with the gothic cathedral aesthetic; custom CSS gives full control over gold-crimson-midnight palette, UnifrakturCook fonts, arch corners, parchment noise |
| Celery/Redis | Sync execution by default, optional Celery upgrade | No Redis dependency for simple deployments; documented upgrade path for heavy use |
| AI providers | Groq (2 keys) → OpenRouter (2 keys) → Template fallback | Maximizes free tier usage; template fallback ensures the app works even without an internet connection |
| Database | SQLite default, optional Postgres | Zero-config for pentesters; SQLAlchemy async makes the migration path trivial |
| Task runner | `asyncio.create_subprocess_exec` for scanners, FastAPI background tasks for simple operations | Avoids Celery complexity for single-user deployments; upgrade note included |
| Localization | `react-i18next` from start, English-only v1 | Door open for future locales without a rewrite |

---

## Project Structure

```
THE-EYE/
├── backend/
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Pydantic-settings from .env
│   │   ├── database.py            # SQLAlchemy async engine
│   │   ├── models.py              # All DB models
│   │   └── schemas.py             # Pydantic request/response models
│   ├── scanner/
│   │   ├── __init__.py
│   │   ├── nmap_runner.py         # Async subprocess nmap wrapper
│   │   ├── masscan_runner.py      # Optional masscan for wide scans
│   │   └── fingerprint.py         # Service/OS fingerprinting
│   ├── osint/
│   │   ├── __init__.py
│   │   ├── discovery.py           # Subdomain discovery, DNS, WHOIS
│   │   ├── tech_detect.py         # HTTP header + favicon + CMS detection
│   │   ├── email_recon.py         # Email format + breach + social
│   │   └── ip_enrich.py           # rDNS, ASN, geolocation
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── risk_engine.py         # Risk scoring + prioritization (SSoT)
│   │   ├── cve_lookup.py          # CVE matching from service banners
│   │   └── correlation.py         # Cross-module evidence correlation
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── engine.py              # Orchestrator: agent + provider
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # Fallback chain + per-key round-robin
│   │   │   ├── base.py            # Abstract provider interface
│   │   │   ├── groq.py
│   │   │   ├── openrouter.py
│   │   │   └── template.py        # Template fallback (no LLM)
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── scan_advisor.py    # Scan methodology guidance
│   │   │   ├── osint_analyst.py   # OSINT correlation & prioritization
│   │   │   └── report_writer.py   # Narrative report generation
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── exporter.py            # PDF/HTML/JSON export (autoescape on)
│   │   ├── templates/             # Jinja2 report templates
│   │   └── scheduler.py           # Auto-report scheduling
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── i18n.js                 # react-i18next setup
│       ├── locales/
│       │   └── en.json            # English strings
│       ├── components/
│       │   ├── Sidebar.jsx
│       │   ├── TopBar.jsx
│       │   ├── StatCard.jsx
│       │   ├── ScanTable.jsx
│       │   ├── AiChat.jsx
│       │   ├── QuickActions.jsx
│       │   └── ui/                # Hand-crafted gothic-themed primitives
│       │       ├── Card.jsx
│       │       ├── Badge.jsx
│       │       ├── Button.jsx
│       │       ├── Input.jsx
│       │       └── Modal.jsx
│       ├── pages/
│       │   ├── Sanctum.jsx        # Dashboard
│       │   ├── Vigils.jsx         # Scan list
│       │   ├── VigilDetail.jsx    # Scan detail
│       │   ├── Recon.jsx          # OSINT list
│       │   ├── ReconDetail.jsx    # OSINT detail
│       │   ├── Targets.jsx        # Target management
│       │   └── Scriptorium.jsx    # Reports
│       └── styles/
│           └── gothic.css         # Full gothic theme stylesheet
├── docs/
│   └── design-reference/
│       ├── index.html             # Brutalist blood-red (reference)
│       └── index-gothic.html      # Gothic cathedral (reference)
├── plans/
│   └── implementation-plan.md     # ← this file
└── requirements.txt               # Root-level Python deps (pip install)
```

---

## Phase 1: Backend Core Infrastructure

### 1.1 Dependencies (`requirements.txt`)
```
fastapi[standard]==0.115.*
sqlalchemy[asyncio]==2.0.*
aiosqlite==0.20.*
pydantic-settings==2.*
python-dotenv==1.*
httpx==0.27.*
python-multipart==0.0.*
jinja2==3.*
weasyprint==62.*
celery==5.*              # optional, only if Redis available
redis==5.*               # optional
uvicorn[standard]==0.30.*
```

### 1.2 Configuration (`backend/core/config.py`)
- Load from `.env` at project root
- `DATABASE_URL` (default: `sqlite+aiosqlite:///./the_eye.db`)
- `GROQ_API_KEY_1`, `GROQ_API_KEY_2`
- `OPENROUTER_API_KEY_1`, `OPENROUTER_API_KEY_2`
- `AI_PROVIDER_PRIORITY` (comma-separated list)
- `NMAP_PATH`, `MASSCAN_PATH` (auto-detect defaults)
- `LOG_LEVEL` (default: INFO)
- `CORS_ORIGINS` (default: `http://localhost:5173`)
- `API_KEY` — auto-generated random key on first run if not set
- `HEARTBEAT_SECONDS` (default: 30) — how often running tasks write heartbeat

### 1.3 Database (`backend/core/database.py`)
- `AsyncEngine` + `async_sessionmaker` for SQLAlchemy
- `Base = declarative_base()`
- `get_db()` async generator for dependency injection
- Auto-create tables on startup

### 1.4 Models (`backend/core/models.py`)

```python
class Target(Base):
    __tablename__ = "targets"
    id: int PK auto
    name: str
    ip_range: str nullable         # CIDR or single IP
    domain: str nullable
    notes: Text nullable
    tags: JSON nullable            # ["web", "critical", ...]
    created_at: datetime
    updated_at: datetime

class Scan(Base):
    __tablename__ = "scans"
    id: int PK auto
    target_id: int FK -> targets.id
    task_id: str nullable          # Celery task ID or internal UUID
    status: str                    # pending | running | completed | failed | interrupted
    scan_profile: str              # quick | standard | deep | stealth
    options: JSON nullable         # custom nmap args
    ports: JSON nullable           # [{"port": 80, "proto": "tcp", "state": "open", "service": "...", "version": "..."}]
    risk_score: float nullable     # cached output from risk_engine (SSoT)
    summary: Text nullable
    cve_data: JSON nullable
    raw_output: Text nullable
    started_at: datetime nullable
    completed_at: datetime nullable
    heartbeat_at: datetime nullable  # periodic liveness timestamp

class OSINTResult(Base):
    __tablename__ = "osint_results"
    id: int PK auto
    target_id: int FK -> targets.id
    task_id: str nullable
    status: str                    # pending | running | completed | failed | interrupted
    module: str                    # discovery | tech_detect | email | ip_enrich
    source: str                    # crtsh | dns | whois | shodan | ...
    raw_data: JSON nullable
    findings: JSON nullable        # normalized findings for frontend
    started_at: datetime nullable
    completed_at: datetime nullable
    heartbeat_at: datetime nullable

class Report(Base):
    __tablename__ = "reports"
    id: int PK auto
    target_id: int FK -> targets.id
    scan_ids: JSON nullable        # [1, 2, 3]
    osint_ids: JSON nullable       # [1, 2]
    report_type: str               # executive | technical | full
    format: str                    # pdf | html | json | csv
    file_path: str
    generated_at: datetime

class AIAnalysis(Base):
    __tablename__ = "ai_analyses"
    id: int PK auto
    target_id: int FK nullable
    scan_id: int FK nullable
    osint_id: int FK nullable
    agent_type: str                # scan_advisor | osint_analyst | report_writer
    prompt: Text
    response: Text
    model_used: str
    tokens_used: JSON nullable     # {prompt: N, completion: N, total: N}
    created_at: datetime
```

### 1.5 Schemas (`backend/core/schemas.py`)
- Pydantic models for all request/response types
- Input validation: `IPv4Address`, `IPv6Address`, `EmailStr`, `HttpUrl`
- Response models with `model_config = ConfigDict(from_attributes=True)`

---

## Phase 2: Scanner Module

### 2.1 Target Validation (`backend/scanner/validate.py`)
- `validate_target(value: str) -> TargetType`:
  - Accepts only valid IPv4/IPv6 addresses, CIDR ranges, or hostnames matching a strict domain regex
  - Rejects anything starting with `-` or containing shell metacharacters — defense in depth, independent of subprocess safety
- Called at Target creation/update AND immediately before constructing the nmap/masscan argument list

### 2.2 Nmap Runner (`backend/scanner/nmap_runner.py`)
- `class NmapRunner` with methods:
  - `run(target, profile, options)` — starts async subprocess
  - `parse_output(xml_output)` — XML parsing via `xml.etree`
  - `progress_callback(percent)` — updates task state + heartbeat
- Profiles:
  - `quick`: `-sn` (ping sweep) then `-sS -sV -T4 --top-ports 100`
  - `standard`: `-sS -sV -T3 --top-ports 1000`
  - `deep`: `-sS -sV -sC -O -T3 -p-`
  - `stealth`: `-sS -T2 --top-ports 1000`
- Error handling: nmap not installed → clear error message, non-zero exit → log + return partial

### 2.3 Masscan Runner (`backend/scanner/masscan_runner.py`)
- Optional module; skipped if masscan not installed
- Wide-range CIDR scanning with rate limiting
- Feeds discovered hosts into individual nmap scans

### 2.4 Fingerprinting (`backend/scanner/fingerprint.py`)
- Service version detection from nmap parsed output
- OS fingerprinting (nmap -O)
- HTTP banner grab for deeper service identification
- Known vulnerability hints (e.g., "Apache 2.4.49" → path traversal)

---

## Phase 3: OSINT Module

### 3.1 Discovery (`backend/osint/discovery.py`)
- `SubdomainEnumerator`:
  - crt.sh certificate transparency (async HTTP)
  - DNS brute-force with built-in wordlist (~1000 common subdomains)
  - VirusTotal API (if key provided in `.env`)
  - AlienVault OTX API (free tier)
- `DNSResolver`: A, AAAA, MX, NS, TXT, SOA, CNAME, SPF, DMARC
- `WHOISLookup`: via `whois` CLI or `python-whois`
- Rate limiting: 1 req/s for external APIs, configurable delays

### 3.2 Tech Detection (`backend/osint/tech_detect.py`)
- HTTP header analysis via `httpx`
- Favicon hash matching (MurmurHash3 against hardcoded known hashes)
- JS/CSS path probes (e.g., `/wp-admin/`, `/assets/version.txt`)
- CMS detection regex patterns
- Framework detection (React, Angular, Vue, Laravel markers in HTML)

### 3.3 Email Recon (`backend/osint/email_recon.py`)
- Email format guesser (common patterns: first.last@, firstl@, etc.)
- Breach lookup via HIBP (if API key provided)
- Social profile search (GitHub, LinkedIn, Twitter via Google dorking)
- Email reputation scoring (disposable domain detection, MX validation)

### 3.4 IP Enrichment (`backend/osint/ip_enrich.py`)
- Reverse DNS lookup (`socket.gethostbyaddr`)
- ASN/ISP via Team Cymru whois server
- Geolocation via `ip-api.com` (free, no key needed, 45 req/min)
- Shodan/Censys (if API keys provided, optional)

---

## Phase 4: AI Layer

### 4.1 Provider Router (`backend/ai/providers/router.py`)

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Groq K1  │──→│ Groq K2  │──→│ OR K1    │──→│ OR K2    │
│ (5/m)    │   │ (5/m)    │   │ (varied) │   │ (varied) │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
                                      │
                                      ▼
                              ┌──────────────┐
                              │ More free    │
                              │ models       │
                              └──────────────┘
                                      │
                                      ▼
                              ┌──────────────┐
                              │ Template     │
                              │ Fallback     │
                              └──────────────┘
```

- `Router.chat(system_prompt, user_message)` → `str`
- Per-key state tracking (in-memory): `key_id`, `last_used_at`, `consecutive_failures`, `rate_limited_until`
- Round-robin between healthy keys within a provider; fall through to next provider only when all keys for current provider are rate-limited or failing
- On HTTP 429, parse `Retry-After` header and set `rate_limited_until` accordingly
- Log every provider/key switch at INFO level

### 4.2 Base Provider (`backend/ai/providers/base.py`)
```python
class BaseProvider(ABC):
    name: str
    api_key: str
    models: list[str]
    rate_limits: dict

    @abstractmethod
    async def chat(self, messages: list[dict], model: str) -> str:
        ...

    def is_available(self) -> bool:
        # Check cooldown, rate limits
        ...
```

### 4.3 Groq Provider (`backend/ai/providers/groq.py`)
- Models: `llama3-70b-8192`, `mixtral-8x7b-32768`, `gemma2-9b-it`
- Rate limit handling: 5 RPM on free tier → cooldown + queue
- Streaming support for frontend WS

### 4.4 OpenRouter Provider (`backend/ai/providers/openrouter.py`)
- Models: `mistralai/mistral-large`, `meta-llama/llama-3-70b-instruct`, `google/gemini-pro`
- Rate limit handling: depends on model, fallback cycling
- Free model priority: `mistralai/mistral-7b-instruct`, `huggingfaceh4/zephyr-7b-beta`

### 4.5 Template Fallback (`backend/ai/providers/template.py`)
- No-LLM fallback that generates responses from structured data using Jinja2 templates
- Covers: scan summary, vulnerability descriptions, next-step recommendations
- Ensures the app is fully functional without any API keys

### 4.6 AI Agents (`backend/ai/agents/`)

**ScanAdvisor**
- System prompt: Experienced penetration tester guiding methodology
- Context: target IP, service list, open ports, OS guess, CVE matches
- Output: risk assessment, prioritized attack paths, suggested next scans

**OSINTAnalyst**
- System prompt: Intelligence analyst correlating OSINT data
- Context: subdomains, DNS records, tech stack, emails, IP enrichment
- Output: prioritized targets, exposed services, recommended focus areas

**ReportWriter**
- System prompt: Technical writer producing structured security reports
- Context: full scan + OSINT data
- Output: executive summary, technical findings, remediation recommendations

### 4.7 WebSocket Integration
- `/ws/ai/chat` — JSON messages: `{type: "message", content: "..."}` → stream AI response
- `/ws/tasks` — `{type: "task_update", task_id: "...", status: "...", progress: 0.5}`

---

## Phase 5: API Endpoints

### 5.1 Target Management
| Method | Route | Handler | Description |
|--------|-------|---------|-------------|
| POST | `/api/targets` | `create_target` | Add a new target (validates input) |
| GET | `/api/targets` | `list_targets` | Paginated, filterable by name/domain/tag |
| GET | `/api/targets/{id}` | `get_target` | Full target details with related scans/OSINT |
| PUT | `/api/targets/{id}` | `update_target` | Update notes, tags, name |
| DELETE | `/api/targets/{id}` | `delete_target` | Cascade-delete scans, OSINT, reports |

### 5.2 Scan Operations
| Method | Route | Handler | Description |
|--------|-------|---------|-------------|
| POST | `/api/scans` | `start_scan` | Accepts target_id, profile, options → returns task_id |
| GET | `/api/scans` | `list_scans` | Paginated, filter by target/status/profile |
| GET | `/api/scans/{id}` | `get_scan` | Full results: ports, services, CVEs, risk score |
| DELETE | `/api/scans/{id}` | `delete_scan` | Remove scan and related AI analyses |
| POST | `/api/scans/{id}/cancel` | `cancel_scan` | Kill running scan subprocess |

### 5.3 OSINT Operations
| Method | Route | Handler | Description |
|--------|-------|---------|-------------|
| POST | `/api/osint` | `start_investigation` | Accepts target_id, modules list → returns task_id |
| GET | `/api/osint` | `list_investigations` | Paginated, filterable |
| GET | `/api/osint/{id}` | `get_investigation` | Full results per module |
| DELETE | `/api/osint/{id}` | `delete_investigation` | Remove investigation |

### 5.4 AI Operations
| Method | Route | Handler | Description |
|--------|-------|---------|-------------|
| POST | `/api/ai/analyze` | `analyze` | Trigger AI analysis on scan/OSINT by ID |
| GET | `/api/ai/analyses` | `list_analyses` | Paginated AI analysis history |
| WS | `/ws/ai/chat` | `ai_chat_ws` | Streaming chat with AI assistant |

### 5.5 Reports
| Method | Route | Handler | Description |
|--------|-------|---------|-------------|
| POST | `/api/reports` | `generate_report` | Accepts target_id, scan_ids, osint_ids, format, type |
| GET | `/api/reports` | `list_reports` | Paginated report list |
| GET | `/api/reports/{id}/download` | `download_report` | Stream file |
| DELETE | `/api/reports/{id}` | `delete_report` | Remove report + file |

### 5.6 Tasks & Status
| Method | Route | Handler | Description |
|--------|-------|---------|-------------|
| GET | `/api/tasks/{id}` | `get_task_status` | Poll task state, progress %, result |
| WS | `/ws/tasks` | `tasks_ws` | Real-time task updates |

---

## Phase 6: Frontend — Gothic UI

### 6.1 Stack
- **Build**: Vite + React 18
- **Styling**: Tailwind CSS v3 (custom gothic config) + hand-crafted `gothic.css`
- **Routing**: React Router v6
- **State**: React Context + `useReducer`
- **Charts**: Recharts (dark-themed, styled with gothic palette)
- **HTTP**: `fetch` + custom hooks (`useApi`, `useTaskStatus`, `useAiChat`)
- **Auth**: Simple API key header sent with every request
- **i18n**: `react-i18next` with English locale, all UI strings routed through translation keys

### 6.2 Tailwind Config (`tailwind.config.js`)
```javascript
module.exports = {
  content: ["./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        midnight:  { 900: "#0a0a0f", 800: "#0f0f1a", 700: "#1a1a2e" },
        gold:      { 400: "#d4a843", 500: "#c9952e", 600: "#a67c2e" },
        crimson:   { 400: "#dc2626", 500: "#b91c1c", 600: "#991b1b" },
        parchment: "#e8dcc8",
        "gold-dim": "#8b7d5e",
        "candle":  "#ffd700",
      },
      fontFamily: {
        display: ["UnifrakturCook", "serif"],
        heading: ["Cinzel", "serif"],
        body:    ["Cormorant Garamond", "serif"],
        mono:    ["JetBrains Mono", "monospace"],
      },
    },
  },
};
```

### 6.3 Page Mapping

| Route | Component | Gothic Name | Content |
|-------|-----------|-------------|---------|
| `/` | `Sanctum.jsx` | Sanctum | Dashboard: stats, quick scan bar, recent vigils list, AI chat sidebar |
| `/vigils` | `Vigils.jsx` | Vigils | Scan history table: target, profile, status, ports, risk score, date, actions |
| `/vigils/:id` | `VigilDetail.jsx` | Vigil Detail | Port/service table, CVE cards, OS fingerprint, AI analysis panel, raw output |
| `/recon` | `Recon.jsx` | Recon | OSINT investigations list |
| `/recon/:id` | `ReconDetail.jsx` | Recon Detail | Subdomains tree, DNS records table, tech stack badges, email findings, IP enrichment |
| `/targets` | `Targets.jsx` | Targets | Target CRUD: name, IP/domain, tags, notes |
| `/reports` | `Scriptorium.jsx` | Scriptorium | Reports list with generate/download actions |

### 6.4 Component Tree
```
App
├── Sidebar (logo, nav items with badges, theme separator)
├── TopBar (page title, target search, quick filters)
└── MainContent
    ├── Sanctum (Dashboard)
    │   ├── StatCard × 4
    │   ├── QuickScan (target input + profile select + start button)
    │   ├── RecentVigils (mini table)
    │   └── AiChat (collapsible sidebar with message history)
    ├── Vigils
    │   ├── ScanTable (sortable, filterable, paginated)
    │   └── ScanFilterBar
    ├── VigilDetail
    │   ├── PortServiceTable
    │   ├── CVECardGrid
    │   ├── RiskScoreGauge (Recharts gauge/radial)
    │   └── AiAnalysisPanel (read-only AI analysis)
    ├── Recon
    │   ├── InvestigationTable
    │   └── InvestigationFilterBar
    ├── ReconDetail
    │   ├── SubdomainTree (expanding nested list)
    │   ├── DNSTable
    │   ├── TechStackBadges (colored badges with icons)
    │   └── AiCorrelationPanel
    ├── Targets
    │   ├── TargetList (cards or table)
    │   └── TargetForm (add/edit modal)
    └── Scriptorium
        ├── ReportTable
        └── ReportGeneratorModal (select target, scans, format)
```

### 6.5 Gothic CSS Theme (`src/styles/gothic.css`)
Key design tokens carried over from the mockup:
- Background: `#0a0a0f` (midnight)
- Cards: `#0f0f1a` with gold 1px border and arch-corner decoration
- Text: `#e8dcc8` (parchment) body, gold headings
- Accent: `#c9952e` gold, `#b91c1c` crimson for badges
- Font stack: `UnifrakturCook` headings, `Cinzel` subheadings, `Cormorant Garamond` body
- Parchment noise texture: base64 SVG overlay with `mix-blend-mode: overlay`
- Candlelight glow: `box-shadow: 0 0 15px rgba(201, 149, 46, 0.3)` on cards
- Arch corners: CSS `clip-path` on card containers
- ✠ decorative element: `::before` pseudo-elements on section headers

### 6.6 Output Safety
- All scan/OSINT string fields rendered via React's default text interpolation (never `dangerouslySetInnerHTML`) — stored XSS from malicious service banners is automatically escaped
- Raw output viewer uses `<pre>` / text-only component

---

## Phase 7: Async Task Execution & Lifecycle

### 7.1 Default Mode (No Redis/Celery)
- Scanner runner: `asyncio.create_subprocess_exec` with `asyncio.create_task`
- OSINT runner: `httpx.AsyncClient` parallel requests
- Task tracking: in-memory dict `{task_id: {"status": ..., "progress": ..., "result": ...}}`
- WebSocket push: in-memory dict of connected WS clients per task ID
- Periodic heartbeat timestamp (`heartbeat_at`) written to DB row every N seconds while running

### 7.2 Reconciliation on Startup
- On FastAPI startup, run a reconciliation pass:
  - Any `Scan` or `OSINTResult` row with `status = "running"` and no recent heartbeat (`heartbeat_at < now - N seconds`) gets marked `status = "interrupted"`
- Frontend shows a "Resume / Re-run" action for interrupted scans

### 7.3 Optional Celery Upgrade
When Redis is available, set `CELERY_BROKER_URL=redis://localhost:6379/0`:
- Tasks move to `tasks.py` with `@celery_app.task(bind=True)`
- Task state stored in Redis, persists across restarts
- Frontend polls `/api/tasks/{id}` or listens to WS

### 7.4 Progress Reporting
```python
# In scanner loop:
task_state = {"status": "running", "progress": percent, "detail": f"Scanning port {port}/1024"}
# Push to in-memory dict (sync mode) or Celery backend (async mode)
```

---

## Phase 8: Reporting & Exports

### 8.1 Report Templates (`backend/reporting/templates/`)
- `executive_report.html` — gothic-themed executive summary with AI narrative
- `technical_report.html` — detailed findings with port tables, CVE details, raw data
- `osint_report.html` — domain map, DNS records, tech stack, email findings

### 8.2 Export Formats
- HTML (full styled gothic theme)
- PDF via WeasyPrint (same HTML template, print-styled)
- JSON (raw data dump)
- CSV (port table, CVE table)

### 8.3 Jinja2 Autoescaping
- Explicit `autoescape=True` in `exporter.py`'s `Environment` setup — prevents stored XSS in report output

### 8.4 Auto-Generation
- Configurable: generate technical report + AI analysis after every scan
- Scheduler: optional daily/weekly report for recurring targets

### 8.5 Risk Score — Single Source of Truth
- `backend/analysis/risk_engine.py` owns all scoring logic and CVE-weighting
- `Scan.risk_score` is purely a cached output field, written once by `risk_engine.py` after scan completes — never computed inline elsewhere
- If scoring changes later, a single re-score function can recompute across historical scans

---

## Phase 9: Polish & Edge Cases

### 9.1 Error Handling
- nmap/masscan not installed → `HTTP 400` with clear installation instructions
- OSINT source timeout → log warning, continue with partial results
- AI provider outage → template fallback, log error, no crash
- Invalid target input (IP format, domain format) → `HTTP 422` with specific error
- Large scan output → chunked response, paginate port results

### 9.2 Security
- API key validation on every request (simple header check); `.env`-generated random key on first run
- App should NOT be exposed to untrusted networks without a reverse proxy + real auth
- No shell injection: use `subprocess` with argument list, not shell string
- File paths: sanitize user input, use `pathlib`
- Rate limiting on `/api/ai/analyze` (configurable RPM)

### 9.3 Logging
- Structured JSON logging throughout
- Log level configurable via `LOG_LEVEL` env var
- Separate log file for AI provider calls (token usage, latency, failures, fallback patterns)

### 9.4 Testing
- Backend: `pytest` + `pytest-asyncio` + httpx test client
- Scanner module: mock nmap XML output
- AI module: mock HTTP responses for providers
- Frontend: Vitest for unit tests

---

## Future Considerations (Not in v1.0)
- Multi-user with authentication (JWT login, role-based access)
- Agent-based scanning (long-running distributed nmap across multiple hosts)
- Grafana dashboard integration for live metrics
- Plugin system for community OSINT modules
- Desktop app via Tauri (wraps the local web app in a native window)
- Additional locales (i18n framework ready, translations needed)
