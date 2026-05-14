# Handover — 2026-05-14

## Done
- Phase 1 complete: Albus (orchestrator), Dobby (quick tasks), Hedwig (Gmail, multi-account)
- FastAPI backend with routes, SQLite DB with 7 tables
- Multi-account Gmail support: personal, agaetis, houseofworktops — each with separate OAuth tokens
- Next.js dashboard (dark theme): /, /emails, /tasks, /logs, /houseofworktops
- APScheduler: Hedwig runs every 30 min, daily summary at 08:00
- Obsidian sync: daily note writer
- CI: ruff + pytest on push to main
- Git: v0.1.0 tagged on main, dev is the working branch

### This session — House of Worktops order parsing
- DB schema: replaced single `orders` table with three tables: `orders` (rich fields), `order_customers`, `order_items`
- `backend/tools/order_parser.py`: pure-regex parser, returns `{ order, customer, items }`, never crashes on missing fields
- `backend/agents/hedwig.py`: added `is_order_email(subject, sender)` check; order emails skip Claude and go directly to parser; atomic save via `_save_order_atomic` (rollback on failure, idempotent on duplicate order_id)
- `backend/routers/orders.py`: four endpoints — `/orders/today`, `/orders/summary`, `/orders/all`, `/orders/{order_id}`
- `frontend/app/houseofworktops/page.tsx`: client component — stats bar, record cards, filterable+sortable orders table with expandable rows showing full detail, auto-refreshes every 5 min
- Nav updated: "House of Worktops" link added

## In progress
- Nothing active — all code written, not yet live on Windows

## Start next session with
Windows machine setup:
1. Run Gmail OAuth for each of the three accounts
2. Install and configure OpenClaw, point webhook at `http://localhost:8000/openclaw/message`
3. Set up NSSM services for FastAPI and Next.js (see `/docs/windows-setup.md`)
4. Set `OBSIDIAN_VAULT_PATH` in `.env`
5. Write first real tests in `/tests/` — order_parser is a good first target (pure functions, no DB)

## Files touched this session
- `backend/memory/schema.py` — replaced Order model; added OrderCustomer, OrderItem
- `backend/memory/db.py` — added migration columns for new orders fields + _add_column helper
- `backend/tools/order_parser.py` — new file
- `backend/agents/hedwig.py` — added is_order_email, _save_order_atomic; updated run loop
- `backend/routers/orders.py` — new file
- `backend/main.py` — registered orders router
- `frontend/app/houseofworktops/page.tsx` — new file
- `frontend/app/layout.tsx` — added House of Worktops nav link

---

## Project reference

### How to run locally (Mac)
```bash
# Backend
cd /Users/dhawalm/Downloads/lifeOS
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
| `orders` | id, order_id (unique), date_added, status, subtotal, vat, grand_total, comments, deliver_by, is_business_customer, raw_email_id, source_email, created_at |
| `order_customers` | id, order_id (FK), name, email, postcode, phone |
| `order_items` | id, order_id (FK), product_name, product_sku, quantity, unit_price, line_total |

`emails.account` added via `_migrate()` — handles existing installs with `ALTER TABLE`.
`orders` new columns added via `_migrate()` — old installs get new columns added, old columns remain.

### FastAPI routes

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/agents/logs` | Recent agent log entries |
| GET | `/tasks/` | Task list (filterable by status) |
| PATCH | `/tasks/{id}/status` | Update task status |
| GET | `/emails/` | Email list (filterable by processed) |
| POST | `/openclaw/message` | Inbound WhatsApp message from OpenClaw |
| GET | `/orders/today` | Today's orders count + revenue |
| GET | `/orders/summary` | All-time stats, records, top products |
| GET | `/orders/all` | Paginated list with customer + items nested |
| GET | `/orders/{order_id}` | Full order detail |

### Agents

**Albus** — orchestrator. Receives every WhatsApp message via OpenClaw webhook. Routes via `ROUTE:<agent>:<task>` syntax. Knows all three Gmail accounts and priorities. Uses `claude-sonnet-4-6` with cached system prompt.

**Dobby** — quick tasks. Reminders, fast answers. Saves to `tasks` table with status `done`.

**Hedwig** — Gmail intelligence. Loops accounts in priority order: houseofworktops → agaetis → personal. houseofworktops order emails detected by `is_order_email()`, parsed by `order_parser.py`, saved atomically to 3 tables. Non-order emails go to Claude with account-specific prompts. Returns sectioned digest back to Albus. Skips unauthenticated accounts gracefully.

### Order email detection (Hedwig)
- Subject must contain "House of Worktops - Order" or "House of Worktops - Sample Order" (case-insensitive)
- Sender must contain "noreply"
- Both conditions must be true — is_order_email(subject, sender)

### Order parser (`backend/tools/order_parser.py`)
- `parse_order_email(subject, body, email_id)` → `{ order, customer, items }`
- Pure regex, no Claude call, no DB access
- All fields default to None on missing — never raises
- Tested against sample Lucy Bachmann order (162972)

### Gmail tool (`backend/tools/gmail.py`)
- Multi-account OAuth2 via Google API
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
5. Tests — `tests/` is empty; `order_parser.py` is the best first target

### Phase 2 agents (not started)
Hermione (research), Remus (content/writing)

### Phase 3 agents (not started)
Dwayne (fitness/Garmin), Midas (finance), Jarvis (ops/automations)
