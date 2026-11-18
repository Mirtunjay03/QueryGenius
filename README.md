# QueryGenius

**Ask your data. Understand your business.**

QueryGenius is being built as a secure, explainable natural-language analytics SaaS. The supported product architecture is a React + TypeScript frontend and a versioned FastAPI backend. The old root-level Flask app remains as a legacy demo while the replacement is developed; it is not the supported production service.

## Phase 1 status

Phase 0 architecture documents and the Phase 1 application foundation are complete. The foundation provides a responsive React/Vite landing screen, a FastAPI service, SQLAlchemy/Alembic wiring, MySQL-backed Docker Compose configuration, health endpoints, lint/type/test/build checks, and migrations. Query generation, customer database connections, organization isolation, and SQL approval are **not implemented in the new app yet**.

See `PROJECT_STATUS.md`, `docs/feature-matrix.md`, and `docs/roadmap.md` for accurate status.

## Run locally

### Docker Compose (MySQL + Redis + API + frontend)

1. Copy `.env.example` to `.env` and replace the local-only MySQL passwords.
2. From the repository root, run `docker compose up --build`.
3. Open:
   - Frontend: http://localhost:5173
   - API health: http://localhost:8000/health/ready
   - API docs: http://localhost:8000/docs

### Without Docker

Python 3.12+, Node.js 22+, and npm are required. The backend defaults to a local SQLite database for development and tests; production uses the configured MySQL URL.

```powershell
Set-Location D:\QUERYGENIUS\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```powershell
Set-Location D:\QUERYGENIUS\frontend
npm ci
npm run dev
```

## Checks

```powershell
Set-Location D:\QUERYGENIUS\backend
ruff check app tests
mypy app
pytest
alembic upgrade head
```

```powershell
Set-Location D:\QUERYGENIUS\frontend
npm run lint
npm run typecheck
npm test
npm run build
```

## Security and deployment status

- MySQL is the selected application database. Analytics connectors will be separate and read-only; none is available in the new backend yet.
- The new API currently exposes only liveness/readiness checks. No login, organization authorization, SQL generation, or query execution is exposed by this foundation.
- Keep secrets in environment/provider secret settings. Never commit `.env`.
- Docker and Railway configuration are scaffolding, not evidence of a deployed service. A public deployment must wait for tenant authorization, encrypted connector credentials, QueryGuard, read-only analytics access, and passing release checks.

## Documentation

- Architecture: `docs/architecture/`
- Roadmap: `docs/roadmap.md`
- Feature status: `docs/feature-matrix.md`
- Decisions: `docs/decisions/`
- Contributing: `CONTRIBUTING.md`
