# LifeOS — Phase 1 Build Plan
# Hand this to Claude Code to begin

## Context
Building LifeOS — a personal operating system with AI agents.
Read CLAUDE.md first before doing anything.
Tech stack: Python (FastAPI) backend, Next.js frontend, SQLite DB, OpenClaw for agent interface, WhatsApp as primary input.

---

## Step 1 — Repo structure
Scaffold the full folder structure exactly as defined in CLAUDE.md.
Create placeholder files (README.md or __init__.py) in each folder so the structure is visible in GitHub.
Create a root .env.example with all required keys (no real values):

```
# Anthropic
ANTHROPIC_API_KEY=

# Gmail
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REDIRECT_URI=

# OpenClaw
OPENCLAW_WEBHOOK_SECRET=

# DB
DATABASE_URL=sqlite:///./lifeos.db

# Obsidian
OBSIDIAN_VAULT_PATH=

# WhatsApp (via OpenClaw)
WHATSAPP_NUMBER=
```

---

## Step 2 — Shared DB layer
Create `/backend/memory/db.py`:
- SQLite connection using SQLAlchemy
- `get_db()` function for use across all agents
- Base model class

Create initial schema `/backend/memory/schema.py` with these tables:

```
agent_logs
  id, agent_name, task, result, status, created_at

messages
  id, source (whatsapp/dashboard), content, agent_routed_to, response, created_at

tasks
  id, title, description, status (pending/done/failed), agent, due_at, created_at

emails
  id, gmail_id, subject, sender, body_preview, parsed_data (JSON), processed, created_at
```

Run migrations on startup.

---

## Step 3 — FastAPI backend skeleton
Create `/backend/main.py`:
- FastAPI app with CORS enabled
- Health check endpoint: GET /health
- Mount routers for: /agents, /tasks, /emails, /logs

Create basic routers (empty endpoints for now, flesh out in later steps):
- `/backend/routers/agents.py`
- `/backend/routers/tasks.py`
- `/backend/routers/emails.py`

---

## Step 4 — Albus (orchestrator agent)
Create `/backend/agents/albus.py`:
- Receives a message string
- Uses Claude API (claude-sonnet-4-20250514) to decide which agent should handle it
- Routes to correct agent based on decision
- Returns response
- Logs everything to agent_logs table

System prompt for Albus:
```
You are Albus, the orchestrating intelligence of LifeOS — a personal operating system. 
You have a top-level view of the user's life across all domains.
Your job is to understand what the user needs and route them to the right specialist agent, or handle simple responses yourself.

Available agents:
- Dobby: quick tasks, reminders, simple lookups, fast answers
- Hedwig: anything related to email, Gmail, orders, inbox

If you can answer simply and quickly yourself, do so.
If the task needs a specialist, respond with: ROUTE:<agent_name>:<task>
Always be wise, warm, and concise.
```

---

## Step 5 — Dobby (quick tasks agent)
Create `/backend/agents/dobby.py`:
- Receives a task string from Albus
- Uses Claude API for fast, simple responses
- Handles: reminders, quick questions, simple lookups
- Saves result to agent_logs and tasks tables

System prompt for Dobby:
```
You are Dobby, a quick and efficient personal assistant in LifeOS.
You handle fast, simple tasks: reminders, quick answers, lookups, notes.
Be brief, accurate, and fast. No waffle.
```

---

## Step 6 — Hedwig (Gmail agent)
Create `/backend/agents/hedwig.py` and `/backend/tools/gmail.py`:

Gmail tool:
- OAuth2 authentication flow (save tokens to .env or local file)
- `get_unread_emails(max_results=10)` — fetch unread emails
- `mark_as_read(email_id)` 
- `send_email(to, subject, body)`

Hedwig agent:
- Fetches unread emails on demand or schedule
- Parses subject, sender, body preview
- Saves to emails table
- Flags anything that looks like an order confirmation
- Returns summary to Albus

---

## Step 7 — OpenClaw webhook endpoint
Create `/backend/routers/openclaw.py`:
- POST /openclaw/message — receives incoming WhatsApp message from OpenClaw
- Validates webhook secret from .env
- Passes message content to Albus
- Returns Albus response to OpenClaw (which sends it back via WhatsApp)

---

## Step 8 — APScheduler
Create `/backend/scheduler/jobs.py`:
- Run Hedwig every 30 minutes to check Gmail
- Run a daily summary job at 08:00 that writes to Obsidian vault

---

## Step 9 — Obsidian sync
Create `/backend/obsidian_sync/writer.py`:
- `write_daily_note(date, content)` — writes a markdown file to OBSIDIAN_VAULT_PATH
- Daily note template:

```markdown
# Daily Summary — {{date}}

## Emails
{{email_summary}}

## Tasks
{{tasks_summary}}

## Agent Activity
{{agent_log_summary}}
```

---

## Step 10 — Next.js dashboard skeleton
Create `/frontend` with a basic Next.js app:
- Dark theme, clean and minimal
- Pages: / (overview), /emails, /tasks, /logs
- Each page fetches from FastAPI backend
- No auth for now (local network only)
- Show: recent messages to Albus, task list, email summaries, agent logs

---

## Step 11 — Windows deployment setup
Create `/docs/windows-setup.md` with instructions for:
- Installing Python, Node.js, Git on Windows
- Cloning the repo
- Setting up .env from .env.example
- Running FastAPI with uvicorn as a Windows Service using NSSM
- Running Next.js build as a Windows Service
- Setting up a scheduled Git pull every 5 minutes to pick up M1 Mac changes

---

## Step 12 — GitHub Actions (optional but recommended)
Create `.github/workflows/ci.yml`:
- On push to main: run Python tests, lint with ruff
- Keep it simple for now

---

## Done when:
- [ ] Folder structure exists on GitHub
- [ ] FastAPI runs locally with /health returning 200
- [ ] SQLite DB creates tables on startup
- [ ] Albus routes a test message correctly
- [ ] Dobby responds to a simple task
- [ ] Hedwig fetches emails from Gmail
- [ ] OpenClaw webhook receives a message and returns a response
- [ ] Obsidian sync writes a test daily note to vault
- [ ] Next.js dashboard runs and shows data
- [ ] Windows setup docs written
