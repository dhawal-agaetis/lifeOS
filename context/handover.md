# LifeOS — Handover Note
**Date:** 2026-05-14
**Branch:** dev
**Stable tag:** v0.1.0 (on main)

---

## What is LifeOS

A personal operating system. One command centre for all areas of life — professional, personal, health, finance. AI agents handle specific domains. Albus orchestrates everything. The primary interface is WhatsApp, running through OpenClaw on a Windows machine that stays on 24/7. The Mac is the dev machine — all code is written here and pushed to GitHub; Windows pulls and runs.

---

## What has been built

### Infrastructure
- **Backend:** FastAPI (Python), running on `uvicorn`, port 8000
- **Database:** SQLite via SQLAlchemy, file `lifeos.db` in project root
- **Frontend:** Next.js 14 (dark theme), port 3000
- **Scheduler:** APScheduler (background, in-process)
- **Agent interface:** OpenClaw webhook → Albus
- **Dev machine:** MacBook M1, Python `.venv/`, Claude Code
- **Runtime machine:** Windows (not yet configured — setup docs exist)

### Folder structure
```
/lifeos
  /backend
    /agents         albus.py, dobby.py, hedwig.py
    /memory         db.py, schema.py
    /obsidian_sync  writer.py
    /routers        agents.py, tasks.py, emails.py, openclaw.py
    /scheduler      jobs.py
    /tools          gmail.py, gmail_tokens/ (gitignored)
  /frontend
    /app            page.tsx, emails/, tasks/, logs/, layout.tsx, globals.css
  /context          this file
  /docs             windows-setup.md
  /skills           add-agent.md, git-release.md
  /logs             (runtime log files, gitignored)
  /openclaw         README.md
  /obsidian-sync    README.md
  /tests            __init__.py (empty, ready for tests)
  .env              local only, gitignored
  .env.example      template for all required keys
  requirements.txt
  CLAUDE.md
```

### Database schema (5 tables)

| Table | Key columns |
|---|---|
| `agent_logs` | id, agent_name, task, result, status, created_at |
| `messages` | id, source, content, agent_routed_to, response, created_at |
| `tasks` | id, title, description, status, agent, due_at, created_at |
| `emails` | id, gmail_id, **account**, subject, sender, body_preview, parsed_data, processed, created_at |
| `orders` | id, order_id, customer_name, customer_email, product, amount, currency, order_date, raw_email_id, created_at |

`emails.account` was added in a later session — the DB migration (`_migrate()` in `db.py`) handles adding this column on existing installs via `ALTER TABLE`.

### Agents

**Albus** (`backend/agents/albus.py`) — orchestrator
- Receives every WhatsApp message via the OpenClaw webhook
- Uses `claude-sonnet-4-6` with a cached system prompt to decide routing
- Routes via `ROUTE:<agent>:<task>` syntax
- Knows about all three Gmail accounts and their priorities
- "check emails" without context → asks which inbox
- "check orders" → always routes to houseofworktops account
- Logs every message and result to `messages` and `agent_logs` tables

**Dobby** (`backend/agents/dobby.py`) — quick tasks
- Handles fast tasks: reminders, quick answers, lookups
- Saves completed tasks to `tasks` table with status `done`
- Uses `claude-sonnet-4-6` with cached system prompt

**Hedwig** (`backend/agents/hedwig.py`) — Gmail intelligence
- Loops through accounts in priority order: houseofworktops → agaetis → personal
- Each account has its own cached Claude system prompt with account-specific logic:
  - **personal:** general triage, flag urgent items
  - **agaetis:** tag by project, flag deadlines and action items
  - **houseofworktops:** parse order confirmations, flag customer queries
- Saves each email to `emails` table with `account` field set
- When houseofworktops email is an order, writes to `orders` table
- Returns a sectioned digest (one section per inbox) back to Albus
- Skips accounts that haven't been authenticated yet (graceful degradation)

### Gmail tool (`backend/tools/gmail.py`)
- Multi-account OAuth2 via Google API
- `ACCOUNTS` registry maps account key → env var names + token file path
- Token files: `backend/tools/gmail_tokens/{personal,agaetis,houseofworktops}.json` — gitignored
- OAuth credentials built from env vars (no `credentials.json` file needed at runtime after first setup)
- Public API: `get_unread_emails(account)`, `mark_as_read(account, id)`, `send_email(account, to, subject, body)`, `authenticate(account)`, `is_authenticated(account)`
- `TOKEN_DIR.mkdir(exist_ok=True)` — directory is created at import time, no manual setup needed

### Scheduler (`backend/scheduler/jobs.py`)
- Starts automatically on FastAPI startup (via `lifespan`)
- **Hedwig check:** every 30 minutes, all three accounts
- **Daily summary:** every day at 08:00 — queries DB, writes markdown to Obsidian vault

### Obsidian sync (`backend/obsidian_sync/writer.py`)
- `write_daily_note(date, email_summary, tasks_summary, agent_log_summary)`
- Writes to `{OBSIDIAN_VAULT_PATH}/LifeOS/Daily/YYYY-MM-DD.md`
- Template: Date header, ## Emails, ## Tasks, ## Agent Activity

### FastAPI routes
| Method | Path | Description |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/agents/logs` | Recent agent log entries |
| GET | `/tasks/` | Task list (filterable by status) |
| PATCH | `/tasks/{id}/status` | Update task status |
| GET | `/emails/` | Email list (filterable by processed) |
| POST | `/openclaw/message` | Inbound WhatsApp message from OpenClaw |

### Next.js dashboard (`frontend/`)
- Dark theme (CSS variables, Tailwind)
- Server components throughout — data fetched from FastAPI at render time
- Pages: `/` (overview with stat cards + agent activity), `/emails`, `/tasks`, `/logs`
- `API_BASE` env var points to FastAPI (default `http://localhost:8000`)
- No auth — local network only

### CI (`/.github/workflows/ci.yml`)
- Triggers on push/PR to `main`
- Runs `ruff check backend/` and `pytest tests/`

---

## Environment variables required

See `.env.example` for the full list. Key ones:

| Key | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | All three agents use Claude API |
| `GMAIL_PERSONAL_CLIENT_ID/SECRET` | Personal Gmail OAuth |
| `GMAIL_AGAETIS_CLIENT_ID/SECRET` | Work email OAuth |
| `GMAIL_HOUSEOFWORKTOPS_CLIENT_ID/SECRET` | Shop email OAuth |
| `DATABASE_URL` | SQLite path, e.g. `sqlite:///./lifeos.db` |
| `OBSIDIAN_VAULT_PATH` | Absolute path to Obsidian vault folder |
| `OPENCLAW_WEBHOOK_SECRET` | HMAC secret for OpenClaw webhook validation |

---

## Email accounts

| Key | Address | Role | Priority |
|---|---|---|---|
| `personal` | gmail.com | General triage, flag urgent | Normal |
| `agaetis` | agaetis.tech | Client/project, deadlines, action items | Medium |
| `houseofworktops` | houseofworktops.co.uk | Orders → `orders` table, customer queries | **Highest** |

Gmail OAuth setup (one-time per account):
```bash
PYTHONPATH=. .venv/bin/python -c "from backend.tools.gmail import authenticate; authenticate('personal')"
```
Repeat for `agaetis` and `houseofworktops`. Tokens saved to `backend/tools/gmail_tokens/`.

---

## Git / branching

| Branch | Purpose |
|---|---|
| `main` | Stable only. Windows machine tracks this. Never commit directly. |
| `dev` | All active development. This is the working branch. |
| `feature/<name>` | Optional, for large isolated changes. Branch from dev. |

**Current tag:** `v0.1.0` on `main` — Phase 1 complete.

To release: follow `/skills/git-release.md`.

Tag format: `v<major>.<minor>.<patch>`
- patch = small fix or addition
- minor = new agent or feature complete
- major = phase complete or breaking change

---

## What still needs doing before Phase 1 is fully live

1. **Gmail OAuth** — run `authenticate()` for each of the three accounts on the Windows machine (requires Google Cloud project per account, credentials in `.env`)
2. **OpenClaw setup** — install on Windows, point webhook at `http://localhost:8000/openclaw/message`, set `OPENCLAW_WEBHOOK_SECRET`
3. **Windows services** — NSSM services for FastAPI and Next.js, scheduled git pull every 5 min from `main` — see `/docs/windows-setup.md`
4. **Obsidian vault path** — set `OBSIDIAN_VAULT_PATH` in `.env` on Windows
5. **Tests** — `tests/` is empty; no unit or integration tests exist yet

---

## How to run locally (Mac)

```bash
# Backend
PYTHONPATH=. .venv/bin/uvicorn backend.main:app --reload
# → http://localhost:8000/health

# Frontend
cd frontend && npm run dev
# → http://localhost:3000
```

---

## Phase 2 agents (not started)

| Agent | Role |
|---|---|
| Hermione | Research, evidence-based decisions |
| Remus | Content, writing, tone |

Phase 3: Dwayne (fitness/Garmin), Midas (finance), Jarvis (ops/automations).
