<div align="center">
  <h1>𓂀 THE EYE</h1>
  <p><strong>Security Intelligence Platform</strong></p>
  <p>Automated recon + OSINT pipeline with AI analysis, gothic cathedral-themed UI</p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.12%2B-blue?style=flat-square&logo=python" alt="Python">
    <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react" alt="React">
    <img src="https://img.shields.io/badge/Tailwind-4-06B6D4?style=flat-square&logo=tailwindcss" alt="Tailwind">
    <img src="https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite" alt="SQLite">
    <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License">
  </p>
</div>

---

## ✠ Overview

THE EYE is a local-first web application for penetration testers. It orchestrates reconnaissance, OSINT discovery, vulnerability correlation, and AI-powered analysis through a unified pipeline system — all presented through a gothic cathedral-themed interface.

**Designed for Kali Linux.** Run entirely offline. No cloud dependencies. No Docker required.

---

## ✠ Features

- **Automated Pipelines** — YAML-defined multi-stage workflows combining scanning, OSINT, and AI analysis with automatic dependency resolution
- **Scanner Integration** — async `nmap` subprocess wrapper with service fingerprinting and CVE matching
- **OSINT Discovery** — subdomain enumeration (crt.sh), WHOIS lookups, technology detection, email discovery, Gravatar profile lookup, Sherlock social search, theHarvester data gathering
- **AI Analysis** — multi-provider orchestration (Groq, OpenRouter) with per-key round-robin and template fallback (works fully offline)
- **Entity Correlation** — cross-target IP/domain/email linkage with automatic target discovery from pipeline results (safety-capped)
- **Risk Engine** — evidence-weighted scoring with configurable severity thresholds
- **Report Generation** — HTML/PDF export via Jinja2 + WeasyPrint
- **Pipeline UI** — stage timeline visualization with live status, start/cancel controls, finding counts
- **Auto-Discovery** — found subdomains, IPs, and hosts are automatically added as targets with depth limits to prevent runaway recursion

---

## ✠ Quick Start

```bash
# One-time setup
git clone https://github.com/aur3lius-marcu5/THE-EYE.git
cd THE-EYE
chmod +x setup.sh start.sh
./setup.sh

# Every session
./start.sh
```

Then open **http://localhost:5173** in a browser.

### Prerequisites (handled by setup.sh)

- Python 3.10+
- Node.js 20+
- nmap, whois, sqlite3
- (Optional) sherlock, theHarvester — stages skip gracefully if missing

---

## ✠ Pipeline System

Pipelines are multi-stage workflows defined in YAML profiles. Each stage runs sequentially with automatic dependency resolution.

### Built-in Profiles

| Profile | Target Type | Stages |
|---------|------------|--------|
| `domain_standard` | domain | subdomain_enum → dns_resolve → whois → port_scan → tech_detect → cve_lookup → email_discovery → gravatar → theharvester → sherlock → ai_analysis |
| `passive_only` | domain | whois → subdomain_enum → dns_resolve → email_discovery → gravatar → theharvester → sherlock → ai_analysis |
| `ip_standard` | ip | ping_sweep → port_scan → cve_lookup → ai_analysis |

### Stage Registry

| Stage | Tool | Description |
|-------|------|-------------|
| `subdomain_enum` | crt.sh API | Certificate transparency subdomain enumeration |
| `dns_resolve` | socket | DNS A-record resolution |
| `whois` | whois | WHOIS record retrieval |
| `port_scan` | nmap | Service scan with version detection |
| `tech_detect` | httpx | HTTP header + favicon technology detection |
| `cve_lookup` | risk engine | CVE matching from service banners |
| `email_discovery` | email patterns | Email format generation from domain |
| `gravatar` | Gravatar API | Gravatar profile lookup |
| `theharvester` | theHarvester | TheHarvester data gathering (optional) |
| `sherlock` | Sherlock | Username search across social networks (optional) |
| `ai_analysis` | LLM router | AI analysis of all accumulated findings |

### Auto-Discovery

After a pipeline completes, discovered subdomains, IPs, and hosts are automatically registered as new targets with `tags=["discovered"]` and `max_depth=1`. Capped at 50 by default to prevent runaway recursion.

---

## ✠ Configuration

Edit `.env` in the project root:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./the_eye.db` | Database connection string |
| `GROQ_API_KEY_1` | — | Primary Groq API key |
| `GROQ_API_KEY_2` | — | Secondary Groq key (round-robin) |
| `OPENROUTER_API_KEY_1` | — | Primary OpenRouter key |
| `OPENROUTER_API_KEY_2` | — | Secondary OpenRouter key |
| `AI_PROVIDER_PRIORITY` | `groq,openrouter,template` | Fallback chain for AI provider |
| `CORS_ORIGINS` | `http://localhost:5173` | Frontend dev server origin |
| `PIPELINE_MAX_NEW_TARGETS` | `50` | Max auto-discovered targets |
| `HEARTBEAT_SECONDS` | `30` | Scan heartbeat interval |

> **No API keys required.** The template fallback generates structured English output without any network calls.

---

## ✠ AI Integration

THE EYE supports a fallback chain:

1. **Groq** — free tier, up to 30 req/min per key
2. **OpenRouter** — community models, credit-based
3. **Template** — no network; generates structured English output from a Jinja2 template

Three agent roles:
- **Scan Advisor** — recommends nmap flags, priority ports, methodology
- **OSINT Analyst** — correlates findings, suggests research paths
- **Report Writer** — produces narrative security assessment from all sources

---

## ✠ Project Structure

```
THE-EYE/
├── backend/
│   ├── main.py                 # FastAPI entry point + lifespan hooks
│   ├── core/                   # Config, database, models, schemas, tool checker
│   ├── scanner/                # Nmap runner, service fingerprinting
│   ├── osint/                  # Discovery, tech detect, WHOIS, Gravatar, Sherlock, theHarvester
│   ├── analysis/               # Risk engine, CVE lookup, entity correlation
│   ├── ai/                     # Provider router (Groq/OpenRouter/Template) + agents
│   ├── pipeline/               # Runner, stage registry, YAML profiles
│   ├── routes/                 # FastAPI endpoint modules
│   └── reporting/              # PDF/HTML export + Jinja2 templates
├── frontend/
│   ├── src/
│   │   ├── pages/              # Sanctum, Vigils, Recon, Targets, Pipeline, Scriptorium
│   │   ├── components/         # Sidebar, AiChat, StageTimeline, Card, Badge
│   │   ├── styles/gothic.css   # Tailwind v4 + gothic theme utilities
│   │   └── locales/en.json     # i18n translations
│   └── vite.config.js
├── setup.sh                    # One-time environment setup
├── start.sh                    # Launch backend + frontend
├── requirements.txt            # Python dependencies
└── plans/                      # Implementation plan, improvement docs
```

---

## ✠ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), SQLite |
| Frontend | Vite, React 19, Tailwind CSS v4, react-i18next |
| AI | Groq API, OpenRouter API, template fallback (zero LLM dependency) |
| Scanners | nmap (subprocess), optional masscan / sherlock / theHarvester |
| PDF | WeasyPrint |

---

## ✠ Design

The UI follows a gothic cathedral aesthetic:

- **Gold** (`#c9952e`) — sacred/authoritative elements
- **Crimson** (`#a82424`) — danger/alerts/critical findings
- **Midnight** (`#0a0a1a` → `#1a1a2e`) — deep backgrounds
- **Parchment** (`#e8dcc8`) — body text
- **UnifrakturCook** — headings (gothic blackletter)
- **Cinzel** — display/uppercase text
- **Cormorant Garamond** — body text

---

## ✠ License

MIT
