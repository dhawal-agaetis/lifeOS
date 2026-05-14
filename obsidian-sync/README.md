# Obsidian Sync

Vault sync logic lives in `/backend/obsidian_sync/writer.py`.

Set `OBSIDIAN_VAULT_PATH` in `.env` to point to your local vault directory.
Daily notes are written at 08:00 by the APScheduler job.
