# Skill: Start of Session

Run this at the beginning of every session before doing any work.

## Steps

1. Read `/context/handover.md` — note what was done, what is in progress, and what to start with next.
2. Read `/context/patterns.md` — re-ground in communication style, technical preferences, and project conventions.
3. Summarise in exactly 3 lines:
   - What was last done
   - What is currently pending
   - Suggested next task
4. Ask for confirmation before doing anything. Do not begin work until the user confirms or redirects.

## Example output

```
Last done: Phase 1 complete — Albus, Dobby, Hedwig, SQLite, FastAPI, Next.js all built and tagged v0.1.0.
Pending: Windows machine setup — OAuth, OpenClaw, NSSM services, tests.
Suggested next: Run Gmail authenticate() for each account and verify tokens save correctly.

Confirm to proceed, or tell me what to work on instead.
```

## Notes

- If `handover.md` has no "In progress" entry, the previous session ended cleanly. Start from "Start next session with".
- If `handover.md` "In progress" has items, those take priority over "Start next session with".
- Never skip this step even for small tasks — the patterns file prevents repeated mistakes.
