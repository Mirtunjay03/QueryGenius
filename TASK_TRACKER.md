# Task Tracker

| Task | Phase | Status | Blocker/acceptance |
|---|---:|---|---|
| Architecture and data-flow docs | 0 | Complete | Trust boundaries and legacy split documented |
| Stack decision / ADR | 0 | Complete | MySQL, FastAPI, React/Vite decisions recorded |
| React/Vite frontend foundation | 1 | Complete | Typecheck, lint, tests, and production build pass |
| FastAPI backend foundation | 1 | Complete | Health, settings, DB session, tests pass |
| SQLAlchemy and Alembic | 1 | Complete | SQLite bootstrap migration applies cleanly |
| Local infrastructure and CI | 1 | Partial | Compose is configured; Docker validation is environment-blocked |
| Authentication and tenant isolation | 2 | Implemented | Registration/login, refresh tokens, org/workspace RBAC, cross-tenant tests |
| External DB connectors/schema sync | 3 | Implemented | PostgreSQL demo adapter, encrypted credentials, sync/FK metadata; real customer DB verification remains owner-controlled |
| AI provider abstraction | 4 | Implemented | Gemini structured JSON, provider switch, token tracking; real Gemini verification requires an owner API key |
| Text-to-SQL and clarification | 5 | Implemented | Demo intent/metric grounding, schema allowlists, SQL explanation, ambiguity clarification |
| QueryGuard and safe execution | 6 | Implemented | SQLGlot AST validation, read-only execution, exact approval revalidation, limits and security tests |
| Production deployment | 12 | Blocked | Requires owner-managed Railway project, database, and secrets |
