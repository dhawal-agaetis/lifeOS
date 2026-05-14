# Handover — 2026-05-14

## Done
- Phase 1 complete: Albus (orchestrator), Dobby (quick tasks), Hedwig (Gmail, multi-account)
- FastAPI backend with 5 routes, SQLite DB with 5 tables (agent_logs, messages, tasks, emails, orders)
- Multi-account Gmail support: personal, agaetis, houseofworktops — each with separate OAuth tokens
- Orders table: houseofworktops order confirmations parsed and stored automatically
- Next.js dashboard (dark theme): /, /emails, /tasks, /logs
- APScheduler: Hedwig runs every 30 min, daily summary at 08:00
- Obsidian sync: daily note writer
- CI: ruff + pytest on push to main
- Git: v0.1.0 tagged on main, dev is the working branch

## In progress
- Nothing active — all Phase 1 code is written, not yet live on Windows

## Start next session with
Windows machine setup:
1. Run Gmail OAuth for each of the three accounts
2. Install and configure OpenClaw, point webhook at `http://localhost:8000/openclaw/message`
3. Set up NSSM services for FastAPI and Next.js (see `/docs/windows-setup.md`)
4. Set `OBSIDIAN_VAULT_PATH` in `.env`
5. Write first real tests in `/tests/`

## Files touched
_(update this section at end of each session)_

---

## Project reference

### How to run locally (Mac)
```bash
# Backend
PYTHONPATH=. .venv/bin/uvicorn backend.main:app --reload
# → http://localhost:8000/health

# Frontend
cd frontend && npm run dev
# → http://localhost:3000
```

### Database schema

| Table | Key columns |
|---|---|
| `agent_logs` | id, agent_name, task, result, status, created_at |
| `messages` | id, source, content, agent_routed_to, response, created_at |
| `tasks` | id, title, description, status, agent, due_at, created_at |
| `emails` | id, gmail_id, account, subject, sender, body_preview, parsed_data, processed, created_at |
| `orders` | id, order_id, customer_name, customer_email, product, amount, currency, order_date, raw_email_id, created_at |

`emails.account` added via `_migrate()` in `db.py` — handles existing installs with `ALTER TABLE`.

### FastAPI routes

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/agents/logs` | Recent agent log entries |
| GET | `/tasks/` | Task list (filterable by status) |
| PATCH | `/tasks/{id}/status` | Update task status |
| GET | `/emails/` | Email list (filterable by processed) |
| POST | `/openclaw/message` | Inbound WhatsApp message from OpenClaw |

### Agents

**Albus** — orchestrator. Receives every WhatsApp message via OpenClaw webhook. Routes via `ROUTE:<agent>:<task>` syntax. Knows all three Gmail accounts and priorities. Uses `claude-sonnet-4-6` with cached system prompt.

**Dobby** — quick tasks. Reminders, fast answers. Saves to `tasks` table with status `done`.

**Hedwig** — Gmail intelligence. Loops accounts in priority order: houseofworktops → agaetis → personal. Account-specific Claude prompts per inbox. houseofworktops orders → `orders` table. Returns sectioned digest back to Albus. Skips unauthenticated accounts gracefully.

### Gmail tool (`backend/tools/gmail.py`)
- Multi-account OAuth2 via Google API
- `ACCOUNTS` registry maps account key → env var names + token file path
- Token files: `backend/tools/gmail_tokens/{personal,agaetis,houseofworktops}.json` — gitignored
- First-time setup per account:
  ```bash
  PYTHONPATH=. .venv/bin/python -c "from backend.tools.gmail import authenticate; authenticate('personal')"
  ```

### Environment variables (see `.env.example` for full list)

| Key | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | All agents |
| `GMAIL_PERSONAL_CLIENT_ID/SECRET` | Personal Gmail OAuth |
| `GMAIL_AGAETIS_CLIENT_ID/SECRET` | Work email OAuth |
| `GMAIL_HOUSEOFWORKTOPS_CLIENT_ID/SECRET` | Shop email OAuth |
| `DATABASE_URL` | SQLite path, e.g. `sqlite:///./lifeos.db` |
| `OBSIDIAN_VAULT_PATH` | Absolute path to Obsidian vault folder |
| `OPENCLAW_WEBHOOK_SECRET` | HMAC secret for OpenClaw webhook validation |

### What still needs doing before Phase 1 is live
1. Gmail OAuth — run `authenticate()` for each account on Windows
2. OpenClaw — install, point webhook, set secret
3. Windows services — NSSM for FastAPI + Next.js, scheduled git pull from `main`
4. Obsidian vault path — set in `.env` on Windows
5. Tests — `tests/` is empty

### Phase 2 agents (not started)
Hermione (research), Remus (content/writing)

### Phase 3 agents (not started)
Dwayne (fitness/Garmin), Midas (finance), Jarvis (ops/automations)
