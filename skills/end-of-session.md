# Skill: End of Session

Run this before closing every session.

## Steps

1. Summarise what was done this session in bullet points — one line per logical change.
2. Update `/context/handover.md`:
   - Replace `## Done` with what was completed this session (plus anything already there that's still relevant).
   - Update `## In progress` — anything started but not finished, or empty if session ended cleanly.
   - Update `## Start next session with` — the clearest next action based on what was just done.
   - Update `## Files touched` — list every file created or modified this session.
3. If new preferences, conventions, or patterns emerged this session, update `/context/patterns.md`.
4. Stage and commit only the context files:
   ```bash
   git add context/handover.md context/patterns.md
   git commit -m "context: handover $(date +%Y-%m-%d)"
   ```
   Branch must be `dev`. Never commit context changes to `main`.
5. Output the summary to the user so they can see what was captured.

## Notes

- If you wrote a new skill this session, add it to the Skills table in `CLAUDE.md` and include `CLAUDE.md` in the commit.
- If a new preference came up more than once in the session, it belongs in `patterns.md` — not just memory.
- The commit message is always `context: handover YYYY-MM-DD`. No variation.
- If there is nothing to commit (context unchanged), say so — do not create an empty commit.
