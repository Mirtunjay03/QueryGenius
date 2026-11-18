# Contributing

## Development setup

1. Copy `.env.example` to `.env` and replace its local-only passwords.
2. With Docker Compose installed, run `docker compose up --build`.
3. Open `http://localhost:5173`, `http://localhost:8000/health/ready`, or `http://localhost:8000/docs`.
4. Backend-only setup: create a Python 3.12 virtual environment, install `backend/requirements-dev.txt`, set `DATABASE_URL` to a local test DB, then run `uvicorn app.main:app --reload` from `backend/`.
5. Frontend-only setup: run `npm ci` and `npm run dev` from `frontend/`.

## Checks

- Backend: `ruff check app tests`, `mypy app`, `pytest`
- Frontend: `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`

Never commit `.env` values. Add tenant authorization and negative security tests with every tenant-owned API. Do not execute SQL before the explicit approval flow and QueryGuard phases are complete.
