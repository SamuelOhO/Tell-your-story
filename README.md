# Tell Your Story
[![CI](https://github.com/SamuelOhO/Tell-your-story/actions/workflows/ci.yml/badge.svg)](https://github.com/SamuelOhO/Tell-your-story/actions/workflows/ci.yml)

## Quick Start

### 1. Backend (Terminal A)
```powershell
.\venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload
```

Backend URL: `http://localhost:8000`

### 2. Frontend (Terminal B)
```powershell
cd frontend
npm run dev
```

Frontend URL: `http://localhost:5173`

## Initial Setup

### 1. Backend
```powershell
python -m venv venv
.\venv\Scripts\python -m pip install --upgrade pip
.\venv\Scripts\pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

### 2. Frontend
```powershell
cd frontend
npm install
Copy-Item .env.example .env
```

If `npm install` hangs in a cloud-sync or non-ASCII path, copy the project to an ASCII path (example: `C:\tmp`) and run again.

### 3. Frontend Path Workaround Script
```powershell
.\scripts\dev-frontend.ps1
```

## Environment Guide (DEV/PROD)

### Backend `.env` (DEV)
```env
APP_ENV=dev
LOG_LEVEL=INFO
UPSTAGE_API_KEY=
OPENAI_API_KEY=
OPENAI_BASE_URL=
LLM_MODEL=solar-pro2
ALLOWED_ORIGINS=http://localhost:5173
MAX_HISTORY_TURNS=12
DB_PATH=backend/data/tell_your_story.db
SUMMARY_UPDATE_EVERY=6
```

### Backend `.env` (PROD Example)
```env
APP_ENV=prod
LOG_LEVEL=INFO
UPSTAGE_API_KEY=***secret***
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.upstage.ai/v1
LLM_MODEL=solar-pro2
ALLOWED_ORIGINS=https://your-domain.com
MAX_HISTORY_TURNS=12
DB_PATH=/var/app/data/tell_your_story.db
SUMMARY_UPDATE_EVERY=6
```

### Frontend `.env` (DEV)
```env
VITE_APP_ENV=development
VITE_API_BASE_URL=http://localhost:8000
```

### Frontend `.env` (PROD)
```env
VITE_APP_ENV=production
VITE_API_BASE_URL=https://api.your-domain.com
```

### Backend Config Keys
| Key | Required | Default | Description |
| --- | --- | --- | --- |
| `APP_ENV` | Y | `dev` | Runtime environment (`dev`/`prod`/`test`) |
| `LOG_LEVEL` | Y | `INFO` | Log level (`DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`) |
| `UPSTAGE_API_KEY` | N | empty | LLM/STT/TTS provider key |
| `OPENAI_API_KEY` | N | empty | OpenAI-compatible provider key (fallback) |
| `OPENAI_BASE_URL` | N | empty | OpenAI-compatible endpoint URL |
| `LLM_MODEL` | Y | `solar-pro2` | Model name for interview, summary, draft |
| `ALLOWED_ORIGINS` | Y | `http://localhost:5173` | CORS origins (comma-separated) |
| `MAX_HISTORY_TURNS` | Y | `12` | Number of recent turns to send to LLM (`1..100`) |
| `DB_PATH` | Y | `backend/data/tell_your_story.db` | SQLite DB file path |
| `SUMMARY_UPDATE_EVERY` | Y | `6` | Summary update interval (`1..100`) |

Invalid configuration now fails fast during application startup with clear error messages.

## SQLite Operations

### DB health check
```powershell
.\scripts\check-db.ps1
```

Optional custom path:
```powershell
.\scripts\check-db.ps1 -DbPath "backend/data/tell_your_story.db"
```

### DB backup
```powershell
.\scripts\backup-db.ps1
```

Optional custom backup directory:
```powershell
.\scripts\backup-db.ps1 -BackupDir "backups"
```

### DB restore (from backup file)
```powershell
.\scripts\backup-db.ps1 -RestoreFrom "backups/tell_your_story_20260226_120000.db"
```

PostgreSQL migration strategy is documented in `docs/DB_MIGRATION_PLAN.md`.

## Current Features
- Session-based interview flow (`/interview/start`, `/interview/chat`, `/interview/session/{id}`)
- Session summary memory updates (`SUMMARY_UPDATE_EVERY`)
- STT/TTS APIs (`/interview/stt`, `/interview/tts`)
- Draft generation and latest draft fetch (`/interview/draft`, `/interview/draft/latest/{id}`)
- Health endpoint (`/health`) with app/db status (`ok` or `degraded`)

## Observability
- Standard API request logs: method, path, status code, duration, request id.
- Error type logs: `validation`, `auth`, `provider`, `db`.

## CI Troubleshooting
- `pytest` import errors for `backend`: run tests from repository root and use `python -m pytest -q tests`.
- local pytest hangs because of third-party plugins: set `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` before test run.
- frontend install issues in non-ASCII path: use `.\scripts\dev-frontend.ps1` or install in an ASCII path.
- CI workflow uses Ubuntu runner path + `frontend/package-lock.json` to avoid local Windows path issues.

### Local CI-equivalent check
```powershell
.\scripts\verify-local.ps1
```

Backend only:
```powershell
.\scripts\verify-local.ps1 -SkipFrontend
```
