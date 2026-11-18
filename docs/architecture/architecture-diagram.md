# Architecture Diagram

```mermaid
flowchart TB
  subgraph Client
    Web[React SPA]
  end
  subgraph Application["FastAPI modular monolith"]
    API[Versioned REST API]
    Identity[Identity / organization RBAC]
    Workspace[Workspace and connection services]
    Intelligence[Question understanding]
    Retrieval[Schema + approved metric retrieval]
    Provider[Provider-independent LLM adapter]
    Guard[QueryGuard / SQLGlot]
    Cost[Query risk and plan advisor]
    Approval[Approval boundary]
    Execute[Read-only execution adapter]
    Lineage[Lineage, history, feedback]
  end
  subgraph Infrastructure
    MySQL[(MySQL application DB)]
    Redis[(Redis)]
    Worker[Background worker]
  end
  subgraph External
    LLM[Gemini or configured provider]
    Data[(Organization analytics DB)]
  end
  Web --> API
  API --> Identity
  API --> Workspace
  Workspace --> MySQL
  API --> Intelligence
  Intelligence --> Retrieval
  Retrieval --> MySQL
  Intelligence --> Provider
  Provider --> LLM
  Provider --> Guard
  Guard --> Cost
  Cost --> Approval
  Approval --> Execute
  Execute --> Data
  Execute --> Lineage
  Lineage --> MySQL
  Worker --> Redis
  Worker --> MySQL
  Worker --> Data
```

**Critical invariant:** no path from the LLM/provider directly to the analytics database exists. Only the read-only executor can open an analytics connection, and it accepts SQL that was validated and approved.
