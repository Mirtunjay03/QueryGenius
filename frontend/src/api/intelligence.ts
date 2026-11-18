export interface Connection {
  id: string;
  name: string;
  dialect: string;
  status: string;
  last_tested_at: string | null;
  last_synced_at: string | null;
  last_error: string | null;
}

export interface Column {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  default: string | null;
}

export interface ForeignKey {
  name: string | null;
  constrained_columns: string[];
  referred_schema: string | null;
  referred_table: string;
  referred_columns: string[];
}

export interface SchemaTable {
  id: string;
  schema_name: string;
  table_name: string;
  columns: Column[];
  foreign_keys: ForeignKey[];
  synced_at: string;
}

async function request<T>(path: string, token: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...init.headers,
    },
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // Keep the status-based fallback.
    }
    throw new Error(detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function connectDemoDatabase(
  token: string,
  organizationId: string,
  workspaceId: string,
) {
  return request<Connection>(
    `/api/v1/organizations/${organizationId}/workspaces/${workspaceId}/connections`,
    token,
    {
      method: "POST",
      body: JSON.stringify({
        name: "Demo Analytics",
        dialect: "sqlite_demo",
        credentials: {},
      }),
    },
  );
}

export function listConnections(
  token: string,
  organizationId: string,
  workspaceId: string,
) {
  return request<Connection[]>(
    `/api/v1/organizations/${organizationId}/workspaces/${workspaceId}/connections`,
    token,
  );
}

export function testConnection(
  token: string,
  organizationId: string,
  workspaceId: string,
  connectionId: string,
) {
  return request<Connection>(
    `/api/v1/organizations/${organizationId}/workspaces/${workspaceId}/connections/${connectionId}/test`,
    token,
    { method: "POST" },
  );
}

export function syncConnection(
  token: string,
  organizationId: string,
  workspaceId: string,
  connectionId: string,
) {
  return request<SchemaTable[]>(
    `/api/v1/organizations/${organizationId}/workspaces/${workspaceId}/connections/${connectionId}/sync`,
    token,
    { method: "POST" },
  );
}

export function generateAI(token: string, prompt: string) {
  return request<{
    provider: string;
    model: string;
    prompt_version: string;
    answer: string;
    input_tokens: number;
    output_tokens: number;
  }>("/api/v1/ai/generate", token, {
    method: "POST",
    body: JSON.stringify({ prompt, prompt_version: "v1" }),
  });
}

export interface QueryRequest {
  id: string;
  question: string;
  intent: string;
  metric: string | null;
  generated_sql: string | null;
  explanation: string;
  clarification: string | null;
  candidate_hash: string | null;
  status: string;
}

export interface QueryExecution {
  id: string;
  columns: string[];
  rows: Array<Array<string | number | boolean | null>>;
  row_count: number;
}

export function interpretQuery(
  token: string,
  organizationId: string,
  workspaceId: string,
  connectionId: string,
  question: string,
) {
  return request<QueryRequest>(
    `/api/v1/queries/organizations/${organizationId}/workspaces/${workspaceId}/connections/${connectionId}/interpret`,
    token,
    {
      method: "POST",
      body: JSON.stringify({ question }),
    },
  );
}

export function approveQuery(
  token: string,
  organizationId: string,
  workspaceId: string,
  requestId: string,
  sql: string,
  candidateHash: string,
) {
  return request<QueryRequest>(
    `/api/v1/queries/organizations/${organizationId}/workspaces/${workspaceId}/requests/${requestId}/approve`,
    token,
    {
      method: "POST",
      body: JSON.stringify({ sql, candidate_hash: candidateHash }),
    },
  );
}

export function executeQuery(
  token: string,
  organizationId: string,
  workspaceId: string,
  requestId: string,
) {
  return request<QueryExecution>(
    `/api/v1/queries/organizations/${organizationId}/workspaces/${workspaceId}/requests/${requestId}/execute`,
    token,
    { method: "POST" },
  );
}
