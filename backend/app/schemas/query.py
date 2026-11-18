from pydantic import BaseModel, ConfigDict, Field


class QueryInterpretRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)


class QueryRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question: str
    intent: str
    metric: str | None
    generated_sql: str | None
    explanation: str
    clarification: str | None
    candidate_hash: str | None
    status: str


class QueryApprovalRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=10_000)
    candidate_hash: str = Field(min_length=64, max_length=64)


class QueryExecutionRead(BaseModel):
    id: str
    columns: list[str]
    rows: list[list[object]]
    row_count: int
