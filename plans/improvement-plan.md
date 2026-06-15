# THE EYE — Improvement Plan

Companion document to `implementation-plan.md`. These are refinements and additions to the existing plan, organized by area, not a replacement for it.

---

## 1. Task/Scan Lifecycle Resilience

**Problem:** In-memory task tracking (Phase 7.1) means any server restart during a long-running scan leaves that scan's DB row stuck in `status: running` forever, with no way for the frontend to recover or retry.

**Fix:**
- On FastAPI startup, run a reconciliation pass: any `Scan` or `OSINTResult` row with `status = "running"` and no recent heartbeat gets marked `status = "interrupted"`.
- Add an `interrupted` status value alongside `pending | running | completed | failed`.
- Frontend shows a "Resume / Re-run" action for interrupted scans.
- Optional: periodic heartbeat timestamp written to the row every N seconds while running, so reconciliation can distinguish "just started" from "actually dead."

---

## 2. AI Provider Key & Rate-Limit Management

**Problem:** The 2-key Groq + 2-key OpenRouter fallback chain (`router.py`) is specified at a high level, but doesn't define *how* keys get selected or how rate limits are tracked.

**Fix:**
- Track per-key state in memory (or a small `provider_keys` table): `key_id`, `last_used_at`, `consecutive_failures`, `rate_limited_until`.
- Router logic: round-robin between healthy keys within a provider; only fall through to the next provider when *all* keys for the current provider are rate-limited or failing.
- On HTTP 429, parse `Retry-After` if present and set `rate_limited_until` accordingly instead of blind retry.
- Log every provider/key switch at INFO level so the AI provider log (Phase 9.3) can show fallback patterns over time.

---

## 3. Input Validation at the Scanner Boundary

**Problem:** Phase 9.1/9.2 cover general input validation and subprocess argument-list safety, but don't explicitly guard against malicious target strings reaching nmap as flags (e.g., a target value like `--script=...` or `-oN /etc/...`).

**Fix:**
- Add a dedicated `validate_target(value: str) -> TargetType` function in `scanner/` (or `core/`) that:
  - Accepts only valid IPv4/IPv6 addresses, CIDR ranges, or hostnames matching a strict domain regex.
  - Rejects anything starting with `-` or containing shell metacharacters, regardless of how it's later passed to `subprocess`.
- Call this validator at the point a `Target` is created/updated AND again immediately before constructing the nmap/masscan argument list — defense in depth, since stored data could be edited directly via DB or future API changes.

---

## 4. Output Sanitization for Frontend Rendering

**Problem:** `raw_output`, service banners, and OSINT findings come from untrusted remote hosts and get stored/displayed. A malicious banner (e.g., a service that responds with `<script>...`) could result in stored XSS when rendered.

**Fix:**
- Treat all scan/OSINT string fields as untrusted text on the frontend — render via React's default text interpolation (never `dangerouslySetInnerHTML`) so JSX escaping handles it automatically.
- For the raw output viewer specifically, render inside a `<pre>`/text-only component, not HTML.
- For PDF/HTML report exports (Phase 8), ensure Jinja2 templates use autoescaping (default in Jinja2 for `.html` — just confirm `autoescape=True` is explicit in `exporter.py`'s `Environment` setup).

---

## 5. Risk Score — Single Source of Truth

**Problem:** Both `Scan.risk_score` (model field) and `analysis/risk_engine.py` could end up computing/storing overlapping logic.

**Fix:**
- `risk_engine.py` owns all scoring logic and CVE-weighting.
- `Scan.risk_score` is purely a cached output field, written once by `risk_engine.py` after a scan completes — never computed inline elsewhere (e.g., not duplicated in `report_writer.py` or frontend).
- If risk scoring logic changes later, a single re-score function can recompute and update stored `risk_score` values across historical scans.

---

## 6. Authentication — Right-Size for Single-User

**Problem:** "API key validation on every request" (9.2) may be more complexity than a single-user, local-first tool needs, but shouldn't be dropped entirely if the app could be exposed on a network.

**Fix:**
- Keep the simple shared-secret header approach (already proposed) — it's appropriate. Just make explicit:
  - Default `.env`-generated random key on first run (so it's not left blank/default).
  - Document clearly that this is *not* multi-user auth and the app should not be exposed to untrusted networks without a reverse proxy + real auth.
- Defer JWT/role-based auth to "Future Considerations" as already planned — no change needed there, just flagging it's correctly out of scope for v1.

---

## 7. Localization Scope

**Problem:** "Korean localization (if needed)" appears as a Week 4 line item, but i18n retrofitted onto a finished UI is expensive (every hardcoded string needs extraction).

**Fix — pick one:**
- **Option A (recommended if not firmly required):** Drop from v1 timeline entirely; note as a "Future Consideration."
- **Option B (if required):** Introduce `react-i18next` (or similar) from the start of Phase 6, with all UI strings routed through translation keys from the first component built — even if only English is shipped in v1. This keeps the door open without a rewrite later.

---

## 8. Repo Hygiene

**Problem:** `mock-ui/` (kept for design reference) risks being bundled into builds or bloating the deployed artifact.

**Fix:**
- Add `mock-ui/` to `.gitignore`-equivalent build exclusions (Vite `publicDir`/build config should not reference it).
- Alternatively, move reference mockups to `docs/design-reference/` to make their non-production status unambiguous.

---

## Summary Table

| # | Area | Priority | Effort |
|---|------|----------|--------|
| 1 | Task lifecycle reconciliation on restart | High | Low |
| 2 | AI provider key/rate-limit tracking | High | Medium |
| 3 | Scanner input validation (defense in depth) | High | Low |
| 4 | Frontend/report output sanitization | High | Low |
| 5 | Risk score single source of truth | Medium | Low |
| 6 | Right-sized auth (document, don't expand) | Low | Low |
| 7 | Localization scope decision | Medium | Decision only |
| 8 | Repo hygiene for mock-ui | Low | Trivial |

None of these block the existing Week 1–4 build order — items 1, 3, 4, and 8 can be folded into their corresponding phases as they're built (Phase 7, Phase 2/9, Phase 6/8, and project setup respectively) without adding new weeks.
