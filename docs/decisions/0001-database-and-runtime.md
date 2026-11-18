# ADR-0001: Application database and runtime

- **Status:** Accepted for foundation; external connector support remains a separate decision.
- **Date:** 2026-11-14.

## Context

The supplied project specification names PostgreSQL for application persistence and the first analytics adapter. During production planning, the user explicitly selected MySQL and asked for email/password authentication. That later, concrete preference supersedes the earlier PostgreSQL default for the application store.

## Decision

- Build a React + TypeScript/Vite frontend and FastAPI backend as a modular monolith.
- Use SQLAlchemy 2.x and Alembic for application persistence.
- Use MySQL for production application records (identity, organizations, metadata, history); retain SQLite only as a local/demo fixture.
- Record Railway as the deployment default, not as a completed deployment.
- Keep analytics connectors behind a separate adapter and read-only credential boundary. MySQL application persistence does not mean analytics-database connectivity is implemented.

## Consequences

- The original PostgreSQL analytics-first requirement is deferred. Add a dedicated ADR before selecting the first customer analytics adapter.
- Local Phase 1 can use SQLite for fast tests, while Docker Compose provides MySQL for integration.
- Railway account access, MySQL service credentials, encryption key management, and deployment secrets must be configured by the owner.
- The legacy root Flask app remains available during foundation work and must not be presented as the new production service.
