# Development Roadmap

Work is phase-gated. A phase is not complete until its acceptance checks pass; security and data-isolation failures block release.

| Phase | Scope | Release gate |
|---|---|---|
| 0 | Architecture, decisions, feature/status inventory | Docs agree with selected stack and known legacy state |
| 1 | React/Vite, FastAPI, SQLAlchemy, Alembic, MySQL, health, local compose, CI | Frontend/backend start, migration and DB health work, tests/build pass |
| 2 | Registration/login, token lifecycle, organizations, workspaces, RBAC | Unauthorized and cross-organization tests pass |
| 3 | Read-only analytics connectors, encrypted credentials, schema sync/explorer | Demo connector syncs; bad connections and secret exposure tests pass |
| 4 | Provider abstraction, Gemini, structured outputs, prompts, bounded failures | Real provider can be configured; invalid/unavailable responses fail explicitly |
| 5 | Query intent, retrieval, ambiguity, SQL generation/explanation | Demo benchmark passes without guessed metric definitions |
| 6 | QueryGuard, SQL approval, read-only execution | Destructive, out-of-scope, over-limit, and over-time queries are rejected |
| 7 | Results, pagination, chart suggestions, safe exports | Actual query result UI and export tests pass |
| 8 | Metric workflow, approval, versioning | Generated formulas match approved versions |
| 9 | Grounded insights, saved queries, feedback, lineage | Tenant-scoped history and grounded-summary tests pass |
| 10 | Incremental sync, jobs/retries, optional vector retrieval, monitoring | Repeated sync is idempotent and recoverable |
| 11 | Security, integration/E2E/load tests, dependency checks | Release blockers closed and performance measured |
| 12 | Production deployment, migration runbook, demo and portfolio docs | Deployment and health verified in the owner's account |

## Current execution

- Phase 0: architecture and decision docs are complete.
- Phase 1: React/FastAPI foundation and migrations are complete.
- Phase 2: authentication, organizations, workspaces, and tenant authorization are implemented.
- Later phases are not represented as implemented until code and tests exist.
