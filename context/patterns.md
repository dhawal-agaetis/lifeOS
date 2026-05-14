# Patterns — LifeOS project

Captured observations about how this project works and how the user prefers to work.
Update this file at end-of-session if new preferences emerge.

---

## Communication style

- Terse and direct. No padding, no filler, no cheerful affirmations.
- British English spelling: "centre" not "center", "colour" not "color", "organised" not "organized".
- No emojis unless explicitly asked.
- Short responses preferred. One sentence per update is enough.
- Instructions are precise and numbered — follow them exactly in the order given.
- Prefers markdown tables and code blocks for reference material.
- Comments in code: why, not what. Never write what the code obviously does.

---

## Technical preferences

- **Language**: Python (backend), TypeScript/React (frontend)
- **Framework**: FastAPI + Next.js. No switching unless the pain is real.
- **DB**: SQLite now, Postgres only when it becomes a bottleneck. Use `db.py` as the single DB access point.
- **AI**: Claude API directly (`claude-sonnet-4-6`). Use prompt caching for every agent system prompt.
- **Agents**: One file, one responsibility. Agents communicate via DB — never call each other directly.
- **Credentials**: Always in `.env`. Never hardcoded. Never committed.
- **Logs**: One log file per agent in `/logs/`. Use Python `logging`, not `print`.
- **No premature abstraction**: three similar lines is better than a helper function. Build for now, not hypothetical futures.
- **Upgrade path philosophy**: feel the pain of the current solution before moving to the next. Don't jump ahead.

---

## Working style

- One session = one task or one feature. Not one day.
- Skills (`/skills/`) are the right place for any repeatable pattern — if something is explained twice, it becomes a skill.
- CLAUDE.md is an index, not a manual. Detail lives in `/skills/`.
- Context files (`/context/`) are tracked in git on `dev`. Always commit them at end of session.
- Never work directly on `main`. All work goes to `dev`. Release = merge dev → main + version tag.
- Git commits: short, lowercase, present tense. Format: `<type>: <description>`. E.g. `feat: add orders table`, `fix: hedwig skip unauthenticated accounts`.
- Tag format: `v<major>.<minor>.<patch>`. Phase complete = major bump. New agent = minor bump.

---

## Project patterns

- **Naming**: Harry Potter universe for most agents (Albus, Dobby, Hedwig, Hermione, Remus). Exceptions: Dwayne (fitness = The Rock), Midas (finance = Greek myth), Jarvis (ops = Iron Man).
- **Routing**: Albus uses `ROUTE:<agent>:<task>` syntax. Always route through Albus, never bypass.
- **Gmail**: Three accounts (personal, agaetis, houseofworktops). Priority order: houseofworktops > agaetis > personal. Each has its own cached Claude prompt with account-specific logic.
- **Orders**: Only houseofworktops emails produce `orders` table entries.
- **DB migrations**: Use `_migrate()` in `db.py` for adding columns to existing installs. Never drop data.
- **Scheduler**: APScheduler in-process. Jobs defined in `jobs.py`. Starts via FastAPI lifespan.
- **Obsidian sync**: Daily notes only. Path from `OBSIDIAN_VAULT_PATH` env var.
- **Windows machine**: Always-on runtime. Tracks `main`. Never commit directly to `main` from Windows.
- **Tests**: `tests/` directory exists but is empty. Writing tests is a pending Phase 1 task.

---

## Things to avoid

- Do not add error handling for scenarios that cannot happen.
- Do not introduce abstractions without a concrete need.
- Do not touch `main` branch directly.
- Do not hardcode credentials, paths, or API keys.
- Do not use `print` — use `logging`.
- Do not skip context updates at end of session.
- Do not commit `.env`, token files, or `lifeos.db`.
