# LifeOS — Windows Setup Guide

This machine runs all LifeOS services 24/7. Follow these steps once after setting up the Windows machine.

---

## 1. Prerequisites

Install these in order:

1. **Git** — https://git-scm.com/download/win
2. **Python 3.11+** — https://www.python.org/downloads/ (tick "Add to PATH")
3. **Node.js 20 LTS** — https://nodejs.org/
4. **NSSM** (Non-Sucking Service Manager) — https://nssm.cc/download
   - Extract `nssm.exe` to `C:\nssm\`
   - Add `C:\nssm\` to your system PATH

---

## 2. Clone the repo

Open PowerShell as Administrator:

```powershell
cd C:\
git clone https://github.com/<your-username>/lifeos.git
cd lifeos
```

---

## 3. Configure environment

```powershell
copy .env.example .env
notepad .env
```

Fill in all values. Key ones:

| Key | Value |
|-----|-------|
| `ANTHROPIC_API_KEY` | From console.anthropic.com |
| `DATABASE_URL` | `sqlite:///C:/lifeos/lifeos.db` |
| `OBSIDIAN_VAULT_PATH` | Path to your Obsidian vault folder |
| `OPENCLAW_WEBHOOK_SECRET` | Any strong random string |

---

## 4. Python backend

```powershell
cd C:\lifeos
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Test it runs:
```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000
# Visit http://localhost:8000/health — should return {"status": "ok"}
# Ctrl+C to stop
```

---

## 5. Install FastAPI as a Windows Service (NSSM)

```powershell
nssm install LifeOS-API "C:\lifeos\.venv\Scripts\uvicorn.exe"
nssm set LifeOS-API AppParameters "backend.main:app --host 0.0.0.0 --port 8000"
nssm set LifeOS-API AppDirectory "C:\lifeos"
nssm set LifeOS-API AppEnvironmentExtra "PYTHONPATH=C:\lifeos"
nssm set LifeOS-API AppStdout "C:\lifeos\logs\api.log"
nssm set LifeOS-API AppStderr "C:\lifeos\logs\api-error.log"
nssm start LifeOS-API
```

---

## 6. Next.js dashboard

```powershell
cd C:\lifeos\frontend
npm install
npm run build
```

Test it:
```powershell
npm start
# Visit http://localhost:3000
# Ctrl+C to stop
```

Install as a service:
```powershell
nssm install LifeOS-Dashboard "C:\Program Files\nodejs\node.exe"
nssm set LifeOS-Dashboard AppParameters "C:\lifeos\frontend\node_modules\.bin\next start"
nssm set LifeOS-Dashboard AppDirectory "C:\lifeos\frontend"
nssm set LifeOS-Dashboard AppStdout "C:\lifeos\logs\dashboard.log"
nssm start LifeOS-Dashboard
```

---

## 7. Auto-pull from GitHub (every 5 minutes)

Create `C:\lifeos\scripts\pull.ps1`:

```powershell
cd C:\lifeos
git pull origin main
```

Open Task Scheduler → Create Basic Task:
- **Name**: LifeOS Git Pull
- **Trigger**: Daily, repeat every 5 minutes indefinitely
- **Action**: Start a program → `powershell.exe`
- **Arguments**: `-File C:\lifeos\scripts\pull.ps1`

---

## 8. Gmail OAuth setup (one-time)

Run this once on the Windows machine (needs a browser):

```powershell
cd C:\lifeos
.venv\Scripts\Activate.ps1
python -c "from backend.tools.gmail import _get_service; _get_service()"
```

This opens a browser, you log in to Google, and a `token.json` is saved. After that, Hedwig runs headlessly.

**Prerequisite**: Download `credentials.json` from Google Cloud Console (OAuth 2.0 Client ID, Desktop app) and place it in `C:\lifeos\`.

---

## 9. Verify everything

| Check | Expected |
|-------|----------|
| `http://localhost:8000/health` | `{"status": "ok"}` |
| `http://localhost:8000/tasks/` | `[]` (or task list) |
| `http://localhost:3000` | Dashboard loads |
| Services panel | LifeOS-API and LifeOS-Dashboard running |
| Task Scheduler | LifeOS Git Pull active |

---

## Troubleshooting

- **Service won't start**: Check logs in `C:\lifeos\logs\`
- **Python imports fail**: Make sure `PYTHONPATH=C:\lifeos` is set in the NSSM service environment
- **Gmail auth fails**: Re-run the one-time OAuth step and ensure `credentials.json` is present

---

## Branch and deployment notes

The Windows machine tracks **main only** — the stable branch.

- The scheduled git pull (`C:\lifeos\scripts\pull.ps1`) always pulls from `main`
- Changes on `dev` do **not** reach Windows until a release is cut
- To deploy new code: follow `/skills/git-release.md` on the Mac, then Windows will pick it up on its next scheduled pull

Update `pull.ps1` to make the branch explicit:

```powershell
cd C:\lifeos
git pull origin main
```
