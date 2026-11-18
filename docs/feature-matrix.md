# Feature Matrix

Status definitions: **Legacy demo** means present only in the old root Flask app; **Phase 1** means the new supported foundation; **Not started** means no implementation claim.

| Capability | Status | Notes |
|---|---|---|
| React + TypeScript app | Phase 1 | Foundation complete; product workflows remain future phases |
| FastAPI `/api/v1` service | Phase 1 | Health/config foundation complete |
| MySQL application persistence | Phase 1 | User-selected application DB; Alembic migrations |
| Authentication and tenant isolation | Not started in new app | Legacy login is not the target auth architecture |
| External database connectors | Phase 3 | PostgreSQL adapter and demo SQLite connector; credentials encrypted and tenant-scoped |
| Schema synchronization/retrieval | Phase 3 | Table, column, and foreign-key synchronization with refresh and explorer UI |
| Gemini provider abstraction | Phase 4 | Gemini REST provider with structured JSON validation, prompt versions, token usage, and safe API-key handling |
| Text-to-SQL and SQL explanation | Phase 5 | Grounded demo query plans, ambiguity clarification, relevant schema allowlists, explanations |
| SQL approval and read-only execution | Phase 6 | SQLGlot AST validation, exact approval hash, 100-row limit, 5-second guard, SQLite query-only mode |
| Natural-language SQL | Legacy demo only | Heuristic/demo implementation, not a market-ready model |
| SQL AST guard | Legacy demo only | Must be rebuilt against connection-specific schemas and dialects |
| SQL approval before execution | Not started in new app | Legacy route executes immediately and is not the target workflow |
| Metric approval/versioning | Legacy demo only | Financial estimates remain explicitly unapproved |
| Query history and lineage | Legacy demo only | New tenant-scoped schema is planned |
| Insights and charting | Legacy demo only | No production grounding/evaluation claim |
| Redis/background jobs | Not started | Foundation only until data ingestion phase |
| Docker/CI | Partial legacy configuration | Phase 1 will replace/extend with multi-app checks |
| Public deployment | Not started | No provider project or credentials available |
