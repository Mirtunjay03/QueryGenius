# Project Status

**As of:** 2026-11-18

## Current state

- A legacy Flask demo exists at the repository root. It uses bundled SQLite data and is not market-ready.
- Legacy hardening added read-only SQLite access, row/time limits, a basic login, and MySQL-compatible account/history storage, but it does not satisfy the target multi-tenant SaaS architecture.
- The React/FastAPI foundation is implemented and its local backend, frontend build, and migration checks pass.
- Phase 2 auth/tenant isolation and Phase 3 database intelligence are implemented.
- Phase 4 Gemini abstraction is implemented; real provider calls require `GEMINI_API_KEY`.
- Phase 5 text-to-SQL demo grounding and clarification are implemented.
- Phase 6 SQLGlot validation, exact-SQL approval, read-only SQLite execution, limits, and security tests are implemented.
- No customer analytics connector, tenant isolation, AI query pipeline, or public deployment is complete yet.
- Node.js 22.9.0, npm 10.8.3, and Python 3.12.7 are available. Docker is unavailable in this environment.
- The user selected MySQL for the application database, email/password identity, and requested recommended hosting defaults (Railway). No Railway project/credentials are available.

## In progress

- Phase 2 authentication and tenant isolation are implemented, with authorization and cross-tenant tests.
- PostgreSQL credentials and Gemini deployment credentials remain owner-controlled and unavailable.

## Verification policy

Record only commands that were actually run. Compose/PostgreSQL-or-MySQL service checks cannot be completed locally until Docker or a reachable database is available. Use SQLite only for isolated unit tests; do not treat that as production DB verification.

## Next

1. Implement registration/login and organization/workspace authorization.
2. Add tenant-scoped models, migrations, and cross-tenant tests.
3. Add the read-only analytics connector contract and demo adapter.
4. Continue only after tenant isolation acceptance is met.
