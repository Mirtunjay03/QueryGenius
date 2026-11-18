# QueryGenius Master Plan

Build QueryGenius as a secure, explainable analytics SaaS with a React/TypeScript SPA, FastAPI modular monolith, MySQL application database, provider-independent AI services, schema-aware retrieval, deterministic QueryGuard, explicit SQL approval, and read-only analytics connectors.

## Governing documents

- Architecture: `docs/architecture/system-design.md`
- Component flow: `docs/architecture/architecture-diagram.md`
- Delivery gates: `docs/roadmap.md`
- Scope truth: `docs/feature-matrix.md`
- Decisions: `docs/decisions/`
- Current execution: `PROJECT_STATUS.md` and `TASK_TRACKER.md`

## Non-negotiable release blockers

1. Tenant and workspace authorization with cross-tenant tests.
2. Encrypted connector secrets and safe connection policy.
3. QueryGuard on the exact approved SQL and real read-only DB credentials.
4. Grounded AI outputs; unavailable providers and unapproved metrics fail explicitly.
5. Migrations, automated checks, and verified deployment.

## Current execution

Complete Phase 0 documentation and Phase 1 foundation before advancing to authentication/tenancy and connectors. Preserve the legacy app until the replacement has parity and a deliberate migration plan.
