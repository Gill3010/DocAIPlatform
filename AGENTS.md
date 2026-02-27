# AGENTS.md

## Cursor Cloud specific instructions

### Architecture Overview
DocAI Platform is a SaaS document conversion and AI-assisted editing app. The core services are:

| Service | Directory | Port | Stack |
|---|---|---|---|
| Backend API | `backend/` | 8000 | Python 3.12 + FastAPI + SQLite (aiosqlite) |
| Frontend | `frontend/` | 5173 | React 19 + TypeScript + Vite 7 |
| Collaboration (optional) | `backend-collab/` | 3001 | Node.js + Yjs WebSocket |

### Starting Services

**Backend** (must start first):
```bash
cd /workspace/backend && source venv/bin/activate && \
  uvicorn main:app --host 0.0.0.0 --port 8000 &
```
Health check: `curl http://localhost:8000/health` returns `{"status":"healthy"}`.

**Frontend** (Vite dev server):
```bash
cd /workspace/frontend && npx vite --host 0.0.0.0 --port 5173 &
```

**Collaboration server** (optional, only for real-time co-editing):
```bash
node /workspace/backend-collab/dist/server.js &
```

### Database & Migrations
SQLite is embedded at `backend/sql_app.db`; no external DB needed. On first setup, create it:
```bash
cd /workspace/backend && source venv/bin/activate && python -c "
from app.core.database import engine, Base
from app.models import *
import asyncio
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
"
```
Then run all `backend/migrate_*.py` scripts. They are idempotent.

### Backend `.env` Gotchas
- Copy `backend/.env.example` to `backend/.env` before starting.
- Set `USE_ECS_CONVERTER=false` for local development (avoids AWS ECS dependency).
- All optional integrations (OpenAI, PayPal, Google/Facebook OAuth, Resend, Turnstile) work without keys; features degrade gracefully.

### Lint / Test / Build
See `README.md` for standard commands. Notable caveats:
- **Frontend lint**: `npx eslint .` (from `frontend/`). Pre-existing lint errors exist in the codebase (57 errors, mostly `@typescript-eslint/no-explicit-any`).
- **Frontend tests**: `npx vitest run` (from `frontend/`). 1 pre-existing test failure in `FileDropZone.test.tsx`.
- **Backend tests**: `pytest` (from `backend/`, with venv activated). 4 auth tests fail due to a SQLAlchemy mapper conflict in `test_conversion_service.py`. Use `pytest --ignore=tests/test_conversion_service.py` to collect cleanly, though 4 auth tests still fail with mapper errors at import time.
- **Frontend install**: Use `npm install --legacy-peer-deps` (TipTap peer dependency conflict).
- **Collab build**: `npm run build` in `backend-collab/` compiles TypeScript to `dist/`.

### System Dependencies
For local document conversions (PDF/OCR), these system packages are required:
`python3.12-venv`, `build-essential`, `ghostscript`, `tesseract-ocr`, `libreoffice-writer`, `pandoc`.
