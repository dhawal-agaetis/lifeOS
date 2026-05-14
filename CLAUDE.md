# LifeOS — CLAUDE.md

## Meta Rules
- If any section of this file exceeds 15 lines, flag it and suggest moving it to /skills
- If I explain the same thing twice in a session, remind me to write it as a skill
- If a task spans more than one session, check if it needs a skill
- Keep this file as an index, not a manual — detail lives in /skills

---

## What is LifeOS
A personal operating system. One command center for all areas of life — professional, personal, health, finance, and everything in between. Agents handle specific domains. Albus orchestrates everything.

---

## Architecture

```
You (WhatsApp)
      ↓
OpenClaw (runs on Windows machine, always on)
      ↓
Albus — orchestrator, routes to specialist agents
   ↓              ↓              ↓
Hedwig          Dobby         (future agents)
(Gmail)      (quick tasks)
      ↓              ↓
      SQLite DB (shared memory layer)
            ↓
      FastAPI Backend
            ↓
      Next.js Dashboard (read-only view)
            ↓
      Obsidian Vault (markdown sync, local)
```

---

## Infrastructure
- **Runtime**: Windows machine (always on) — pulls from GitHub, runs all services
- **Dev environment**: MacBook M1 — all code written here via Claude Code
- **Version control**: Private GitHub repo — M1 pushes, Windows pulls
- **Interface**: WhatsApp → OpenClaw → Albus
- **DB**: SQLite (upgrade to Postgres when needed)
- **Backend**: FastAPI (Python)
- **Frontend**: Next.js (React)
- **Agent layer**: OpenClaw + raw API calls (upgrade to CrewAI/LangGraph when needed)

---

## Structure
```
/lifeos
  CLAUDE.md               ← you are here
  .env                    ← all config, never hardcode
  /backend
    /agents               ← one file per agent
    /tools                ← Gmail, Garmin, Calendar connectors
    /memory               ← shared DB logic
    /scheduler            ← APScheduler jobs
  /frontend               ← Next.js dashboard
  /openclaw               ← OpenClaw config and skills
  /obsidian-sync          ← vault writing logic
  /skills                 ← Claude Code instruction files
  /logs                   ← one log file per agent
  /docs                   ← architecture decisions, notes
```

---

## Agents

| Agent | File | Role | Status |
|---|---|---|---|
| Albus | agents/albus.py | Orchestrator, routes all requests | Phase 1 |
| Dobby | agents/dobby.py | Quick tasks, reminders, fast answers | Phase 1 |
| Hedwig | agents/hedwig.py | Gmail, email triage, order parsing | Phase 1 |
| Hermione | agents/hermione.py | Research, evidence-based decisions | Phase 2 |
| Remus | agents/remus.py | Content, writing, tone | Phase 2 |
| Dwayne | agents/dwayne.py | Fitness, health, Garmin integration | Phase 3 |
| Midas | agents/midas.py | Finance, investments, savings | Phase 3 |
| Jarvis | agents/jarvis.py | Ops, automations, builds automations | Phase 3 |

---

## Git Strategy
- main = stable only, never work directly on it
- dev = active development, all Claude Code work goes here
- feature/<name> = optional, for large isolated changes, branch from dev
- Never push directly to main
- To release: merge dev into main, tag with version number
- Tag format: v<major>.<minor>.<patch>
  - patch = small fix or addition
  - minor = new agent or feature complete
  - major = phase complete or breaking change

## Current Versions
- v0.1.0 — Phase 1 complete (Albus, Dobby, Hedwig, SQLite, FastAPI, Next.js)

---

## Session Rules
- One session per task or feature, not per day
- Start every session: read context/handover.md and context/patterns.md — follow /skills/start-of-session.md
- End every session: follow /skills/end-of-session.md
- Never work directly on main

---

## Skills
- Start of session: /skills/start-of-session.md
- End of session: /skills/end-of-session.md
- New agent: /skills/add-agent.md
- DB changes: /skills/add-db-table.md
- Obsidian notes: /skills/obsidian-note.md
- Debugging an agent: /skills/debug-agent.md
- Git release: /skills/git-release.md

---

## Email Accounts

| Key | Address | Role | Priority |
|---|---|---|---|
| `personal` | gmail.com | General triage, flag urgent items to Albus | Normal |
| `agaetis` | agaetis.tech | Client/project emails, tag by project, flag deadlines & action items | Medium |
| `houseofworktops` | houseofworktops.co.uk | Parse all order confirmations → `orders` table, flag customer queries | **Highest** |

OAuth tokens stored in `/backend/tools/gmail_tokens/{account}.json` — gitignored, never committed.
One Google Cloud project per account. Run `authenticate(account)` once per account for first-time setup.

---

## Conventions
- All logs → /logs/<agent-name>.log
- All DB logic → /backend/memory/db.py
- All credentials → .env (never hardcode)
- Gmail OAuth tokens → /backend/tools/gmail_tokens/ (gitignored, one file per account)
- All agents communicate via shared DB, never directly
- One agent, one responsibility
- Comment why, not what

---

## Upgrade Path
1. SQLite → Postgres (when DB becomes bottleneck)
2. Raw API calls → CrewAI (when orchestration gets complex)
3. CrewAI → LangGraph (when fine-grained control needed)
4. Windows local → cloud VPS (when remote access needed)
5. APScheduler → BullMQ (when many concurrent jobs)

Don't jump ahead. Each step only when you feel the pain of the current one.

---

## Phase 1 Goals
- [ ] Repo structure set up on GitHub
- [ ] Windows machine pulls repo, auto-starts on boot
- [ ] OpenClaw installed and running on Windows
- [ ] Albus responding via WhatsApp
- [ ] Hedwig connected to Gmail, parsing emails
- [ ] Dobby handling quick tasks
- [ ] SQLite DB with shared memory schema
- [ ] FastAPI backend serving basic endpoints
- [ ] Next.js dashboard skeleton running locally
- [ ] Obsidian vault sync writing daily summaries
