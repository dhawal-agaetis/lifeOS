# Handover — 2026-05-14

## Done
- Phase 1 complete: Albus (orchestrator), Dobby (quick tasks), Hedwig (Gmail, multi-account)
- FastAPI backend with routes, SQLite DB with 7 tables
- Multi-account Gmail support: personal, agaetis, houseofworktops — each with separate OAuth tokens
- Next.js dashboard (dark theme): /, /emails, /tasks, /logs — houseofworktops is light theme
- APScheduler: Hedwig runs every 30 min, daily summary at 08:00
- Obsidian sync: daily note writer
- CI: ruff + pytest on push to main
- **v0.1.0 released 2026-05-14** — tagged on main, all Phase 1 work merged, dev is active branch

### Session — House of Worktops order parsing
- DB schema: replaced single `orders` table with three tables: `orders` (rich fields), `order_customers`, `order_items`
- `backend/tools/order_parser.py`: pure-regex parser, returns `{ order, customer, items }`, never crashes on missing fields
- `backend/agents/hedwig.py`: added `is_order_email(subject, sender)` check; order emails skip Claude and go directly to parser; atomic save via `_save_order_atomic` (rollback on failure, idempotent on duplicate order_id)
- `backend/routers/orders.py`: four endpoints — `/orders/today`, `/orders/summary`, `/orders/all`, `/orders/{order_id}`
- `frontend/app/houseofworktops/page.tsx`: client component — stats bar, record cards, top products; auto-refreshes every 5 min
- Nav updated: "House of Worktops" link added

### Session — Dashboard refresh fix, light theme, Gmail pagination, backfill
- `frontend/app/houseofworktops/page.tsx`: light theme (white/light-grey, dark text, subtle shadows); removed orders table; auto-refresh reduced from 5 min to 60 s; "Last updated: Xs ago" indicator top-right; added status breakdown and top products sections
- `backend/tools/gmail.py`: fixed `_extract_body` — was returning only `text/plain` (stub fallback on HTML-only emails); now falls back to stripped HTML; added `_extract_mime`, `_strip_html`; added `get_all_emails_by_subject_pattern` which paginates all results (no max_results cap)
- `backend/routers/orders.py`: added `POST /orders/backfill` — fetches all historical HoW order emails, parses, inserts new ones (idempotent), returns `{found, new, skipped}`
- Backfill ran: 40 order emails found, 39 new orders inserted, 1 skipped (already in DB); all 40 orders now have full data (date_added, status, grand_total, customer, items)

### Session — Fix order email subject matching (was: 40 found, now: 104)
- Root cause 1: shop system sends subjects with a **double space** before "Order" — `"House of Worktops -  Order 162125"`. Old filter used single-space match so all regular orders were missed; only "Sample Order" (single space) was caught.
- Root cause 2: "How Trade Partners -  Order" pattern was not in the filter at all.
- Root cause 3: backfill Gmail query only searched `"House of Worktops"` — never fetched "How Trade Partners" emails.
- Fix: `backend/agents/hedwig.py` → `is_order_email()` now normalises whitespace with `" ".join(subject.lower().split())` before matching; added "how trade partners - order" as third pattern.
- Fix: `backend/routers/orders.py` → `orders_backfill()` now runs two Gmail queries ("House of Worktops" + "How Trade Partners"), deduped by gmail_id.
- Backfill re-ran: found=107 emails, new=64 orders inserted, skipped=43; DB now has 104 unique orders, £7,211.64 total revenue.

### Session — Gmail OAuth for houseofworktops
- `backend/tools/gmail_auth.py`: new CLI script — takes account name as arg, prompts for credentials JSON path, runs browser OAuth flow, saves token to `gmail_tokens/<account>.json`
- `backend/tools/gmail.py`: refactored — no longer requires env vars once token exists; `_get_service` loads from token file only and auto-refreshes; added `load_gmail_service()`, `get_emails_by_subject_pattern()`, richer email fields (date, snippet, full_body)
- houseofworktops OAuth completed and verified: 5 unread emails fetched, 20 order emails found
- Token saved at `backend/tools/gmail_tokens/houseofworktops.json` (gitignored)

## In progress
- v0.1.0 released — code complete, not yet live on Windows

## Start next session with
**Goal: get OpenClaw + WhatsApp talking to Albus on the Windows machine**

Windows machine setup order:
1. Copy `backend/tools/gmail_tokens/houseofworktops.json` to Windows machine (secure transfer)
2. Run Gmail OAuth for personal and agaetis accounts on Windows: `python tools/gmail_auth.py personal` / `agaetis`
3. Install and configure OpenClaw, point webhook at `http://localhost:8000/openclaw/message`
4. Set up NSSM services for FastAPI and Next.js (see `/docs/windows-setup.md`)
5. Set `OBSIDIAN_VAULT_PATH` in `.env`
6. Run `POST /orders/backfill` on Windows after Gmail OAuth is set up
7. Write first real tests in `/tests/` — order_parser is a good first target (pure functions, no DB)

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
| POST | `/orders/backfill` | Fetch all historical HoW order emails, insert new ones |

### Agents

**Albus** — orchestrator. Receives every WhatsApp message via OpenClaw webhook. Routes via `ROUTE:<agent>:<task>` syntax. Knows all three Gmail accounts and priorities. Uses `claude-sonnet-4-6` with cached system prompt.

**Dobby** — quick tasks. Reminders, fast answers. Saves to `tasks` table with status `done`.

**Hedwig** — Gmail intelligence. Loops accounts in priority order: houseofworktops → agaetis → personal. houseofworktops order emails detected by `is_order_email()`, parsed by `order_parser.py`, saved atomically to 3 tables. Non-order emails go to Claude with account-specific prompts. Returns sectioned digest back to Albus. Skips unauthenticated accounts gracefully.

### Order email detection (Hedwig)
- Whitespace-normalised subject must contain one of (case-insensitive):
  - "house of worktops - order" (covers single and double-space variants)
  - "house of worktops - sample order"
  - "how trade partners - order"
- Sender must contain "noreply"
- Both conditions must be true — is_order_email(subject, sender)
- Note: shop system sends "House of Worktops -  Order" (double space) — normalisation handles this

### Order parser (`backend/tools/order_parser.py`)
- `parse_order_email(subject, body, email_id)` → `{ order, customer, items }`
- Pure regex, no Claude call, no DB access
- All fields default to None on missing — never raises
- Tested against sample Lucy Bachmann order (162972)

### Gmail tool (`backend/tools/gmail.py`)
- Multi-account OAuth2 via Google API
- Token files: `backend/tools/gmail_tokens/{personal,agaetis,houseofworktops}.json` — gitignored
- First-time setup per account (requires downloaded OAuth credentials JSON from Google Cloud Console):
  ```bash
  python backend/tools/gmail_auth.py houseofworktops
  # prompts for path to credentials JSON, opens browser, saves token
  ```
- `load_gmail_service(account)` → authenticated service object
- `get_unread_emails(account, max_results=10)` → list of `{id, subject, sender, date, snippet, body_preview, full_body}`
- `get_emails_by_subject_pattern(account, pattern, max_results=20)` → filtered by subject (first page only)
- `get_all_emails_by_subject_pattern(account, pattern)` → all matching emails, paginated (use for backfill/historical)
- `mark_as_read(account, email_id)`
- Body extraction: tries `text/plain` first; falls back to stripped HTML if text/plain < 200 chars (HoW emails are HTML-only)

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
