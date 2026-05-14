# Architecture Map — LifeOS

Last updated: 2026-05-14

---

## Backend (`/backend`)

| File | Purpose |
|---|---|
| `main.py` | FastAPI app, CORS, router registration, lifespan (init_db + scheduler) |
| `memory/db.py` | SQLAlchemy engine, SessionLocal, init_db(), _migrate() |
| `memory/schema.py` | All ORM models: AgentLog, Message, Task, Email, Order, OrderCustomer, OrderItem |
| `agents/albus.py` | Orchestrator — routes WhatsApp messages via ROUTE:<agent>:<task> |
| `agents/dobby.py` | Quick tasks — reminders, fast answers → tasks table |
| `agents/hedwig.py` | Gmail triage — multi-account, order detection, digest back to Albus |
| `tools/gmail.py` | Google OAuth2, multi-account email fetch, subject-pattern search |
| `tools/gmail_auth.py` | One-time OAuth CLI — takes credentials JSON, saves token file |
| `tools/order_parser.py` | Pure-regex parser for HoW order confirmation emails |
| `routers/agents.py` | GET /agents/logs |
| `routers/tasks.py` | GET /tasks/, PATCH /tasks/{id}/status |
| `routers/emails.py` | GET /emails/ |
| `routers/openclaw.py` | POST /openclaw/message |
| `routers/orders.py` | GET /orders/today, /summary, /all, /{order_id} |
| `scheduler/jobs.py` | APScheduler — Hedwig every 30 min, daily summary at 08:00 |
| `obsidian_sync/` | Daily note writer → Obsidian vault |

## Frontend (`/frontend/app`)

| File | Purpose |
|---|---|
| `layout.tsx` | Root layout, dark theme CSS vars, nav (Overview, Emails, Tasks, Logs, HoW) |
| `page.tsx` | Overview — health status, pending tasks, unread emails, recent agent activity |
| `emails/page.tsx` | Email list, processed/unread status |
| `tasks/page.tsx` | Task list |
| `logs/page.tsx` | Agent log entries |
| `houseofworktops/page.tsx` | HoW dashboard — stats, records, filterable orders table with expandable detail |

## DB Tables

| Table | Written by | Read by |
|---|---|---|
| `agent_logs` | All agents | /agents/logs, logs page |
| `messages` | Albus (openclaw webhook) | — |
| `tasks` | Dobby | /tasks/, tasks page |
| `emails` | Hedwig | /emails/, emails page |
| `orders` | Hedwig (via order_parser) | /orders/* |
| `order_customers` | Hedwig (via order_parser) | /orders/* |
| `order_items` | Hedwig (via order_parser) | /orders/* |

## Data flow — HoW order email

```
Gmail API (houseofworktops inbox)
  → Hedwig.run()
    → is_order_email(subject, sender) == True
      → order_parser.parse_order_email(subject, body, gmail_id)
        → { order, customer, items }
      → _save_order_atomic(db, parsed, 'houseofworktops')
        → orders + order_customers + order_items (single transaction)
      → _save_email(db, raw, ...) → emails table
  → digest returned to Albus
    → Albus sends WhatsApp summary

/orders/* endpoints read from orders + order_customers + order_items
/houseofworktops dashboard polls /orders/* every 5 min
```

## Key conventions

- Credentials: `.env` only, never hardcoded
- Gmail tokens: `backend/tools/gmail_tokens/{account}.json`, gitignored
- Migrations: additive only via `_migrate()` in `db.py` — never drop data
- Logs: one file per agent in `/logs/`, Python `logging` not `print`
- Agents communicate via DB only — never call each other directly
- `order_id` uniqueness enforced in application code (idempotent save check before insert)
