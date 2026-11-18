from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConnectionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    dialect: str = Field(pattern=r"^(postgresql|sqlite_demo)$")
    credentials: dict[str, str] = Field(default_factory=dict)


class ConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    dialect: str
    status: str
    last_tested_at: datetime | None
    last_synced_at: datetime | None
    last_error: str | None


class ColumnRead(BaseModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool
    default: str | None


class ForeignKeyRead(BaseModel):
    name: str | None = None
    constrained_columns: list[str]
    referred_schema: str | None = None
    referred_table: str
    referred_columns: list[str]


class TableRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    schema_name: str
    table_name: str
    columns: list[ColumnRead]
    foreign_keys: list[ForeignKeyRead]
    synced_at: datetime


class AIRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=4000)
    prompt_version: str = "v1"


class AIResponse(BaseModel):
    provider: str
    model: str
    prompt_version: str
    answer: str
    input_tokens: int
    output_tokens: int
