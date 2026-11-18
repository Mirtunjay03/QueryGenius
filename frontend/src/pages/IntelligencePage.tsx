import { useEffect, useState, type FormEvent } from "react";
import { Navigate, useSearchParams } from "react-router-dom";

import {
  connectDemoDatabase,
  generateAI,
  listConnections,
  syncConnection,
  testConnection,
  approveQuery,
  executeQuery,
  interpretQuery,
  type Connection,
  type QueryExecution,
  type QueryRequest,
  type SchemaTable,
} from "../api/intelligence";
import { listOrganizations, type Organization } from "../api/auth";
import { useAuth } from "../auth/AuthContext";

export function IntelligencePage() {
  const auth = useAuth();
  const [searchParams] = useSearchParams();
  const workspaceId = searchParams.get("workspace") ?? "";
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [organizationId, setOrganizationId] = useState("");
  const [connections, setConnections] = useState<Connection[]>([]);
  const [tables, setTables] = useState<SchemaTable[]>([]);
  const [error, setError] = useState("");
  const [aiAnswer, setAiAnswer] = useState("");
  const [queryRequest, setQueryRequest] = useState<QueryRequest | null>(null);
  const [execution, setExecution] = useState<QueryExecution | null>(null);

  useEffect(() => {
    if (!auth.accessToken) return;
    listOrganizations(auth.accessToken)
      .then((rows) => {
        setOrganizations(rows);
        setOrganizationId(rows[0]?.id ?? "");
      })
      .catch((requestError) =>
        setError(requestError instanceof Error ? requestError.message : "Could not load organizations"),
      );
  }, [auth.accessToken]);

  useEffect(() => {
    if (!auth.accessToken || !organizationId || !workspaceId) return;
    listConnections(auth.accessToken, organizationId, workspaceId)
      .then(setConnections)
      .catch((requestError) =>
        setError(requestError instanceof Error ? requestError.message : "Could not load connections"),
      );
  }, [auth.accessToken, organizationId, workspaceId]);

  if (!auth.isLoading && !auth.accessToken) return <Navigate replace to="/login" />;

  async function connectDemo() {
    if (!auth.accessToken || !organizationId || !workspaceId) return;
    setError("");
    try {
      const connection = await connectDemoDatabase(auth.accessToken, organizationId, workspaceId);
      const tested = await testConnection(
        auth.accessToken,
        organizationId,
        workspaceId,
        connection.id,
      );
      setConnections([tested]);
      const synced = await syncConnection(
        auth.accessToken,
        organizationId,
        workspaceId,
        tested.id,
      );
      setTables(synced);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Connection failed");
    }
  }

  async function refreshSchema(connectionId: string) {
    if (!auth.accessToken) return;
    try {
      setTables(await syncConnection(auth.accessToken, organizationId, workspaceId, connectionId));
      setError("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Schema refresh failed");
    }
  }

  async function interpret(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!auth.accessToken || !organizationId || !workspaceId || !connections[0]) return;
    const form = new FormData(event.currentTarget);
    setError("");
    setExecution(null);
    try {
      const result = await interpretQuery(
        auth.accessToken,
        organizationId,
        workspaceId,
        connections[0].id,
        String(form.get("question")),
      );
      setQueryRequest(result);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not interpret question");
    }
  }

  async function approveGeneratedSql() {
    if (
      !auth.accessToken ||
      !queryRequest ||
      !queryRequest.generated_sql ||
      !queryRequest.candidate_hash
    ) return;
    try {
      const approved = await approveQuery(
        auth.accessToken,
        organizationId,
        workspaceId,
        queryRequest.id,
        queryRequest.generated_sql,
        queryRequest.candidate_hash,
      );
      setQueryRequest(approved);
      setError("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "SQL approval failed");
    }
  }

  async function executeApprovedSql() {
    if (!auth.accessToken || !queryRequest) return;
    try {
      setExecution(await executeQuery(
        auth.accessToken,
        organizationId,
        workspaceId,
        queryRequest.id,
      ));
      setError("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Safe execution failed");
    }
  }

  async function generate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!auth.accessToken) return;
    const form = new FormData(event.currentTarget);
    try {
      const result = await generateAI(auth.accessToken, String(form.get("prompt")));
      setAiAnswer(`${result.answer}\n\n${result.model} · ${result.input_tokens} in / ${result.output_tokens} out`);
      setError("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "AI generation failed");
    }
  }

  const relationshipCount = tables.reduce((count, table) => count + table.foreign_keys.length, 0);

  return (
    <main className="min-h-screen bg-canvas px-6 py-8 text-slate-100">
      <div className="mx-auto max-w-6xl">
        <p className="text-xs uppercase tracking-[0.18em] text-mint">Schema intelligence</p>
        <h1 className="mt-2 text-3xl font-semibold">Database explorer</h1>

        {organizations.length > 1 && (
          <select
            className="mt-5 rounded-lg border border-white/10 bg-panel px-3 py-2"
            value={organizationId}
            onChange={(event) => setOrganizationId(event.target.value)}
          >
            {organizations.map((organization) => (
              <option key={organization.id} value={organization.id}>{organization.name}</option>
            ))}
          </select>
        )}
        {error && <p className="mt-5 text-sm text-red-400">{error}</p>}

        <section className="mt-6 grid gap-4 md:grid-cols-[280px_1fr]">
          <aside className="rounded-xl border border-white/10 bg-panel p-5">
            <h2 className="font-semibold">Connections</h2>
            <button className="mt-4 w-full rounded-lg bg-mint px-4 py-2 text-sm font-semibold text-slate-950" type="button" onClick={connectDemo}>
              Connect demo database
            </button>
            {connections.map((connection) => (
              <article className="mt-4 rounded-lg border border-white/10 p-3" key={connection.id}>
                <p className="font-medium">{connection.name}</p>
                <p className="mt-1 text-xs text-slate-500">{connection.status} · {connection.dialect}</p>
                <button className="mt-3 text-xs text-mint" type="button" onClick={() => refreshSchema(connection.id)}>
                  Refresh metadata
                </button>
              </article>
            ))}
          </aside>

          <div>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold">Tables ({tables.length}) · Relationships ({relationshipCount})</h2>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {tables.map((table) => (
                <article className="rounded-xl border border-white/10 bg-panel p-5" key={table.id}>
                  <h3 className="font-semibold">{table.schema_name}.{table.table_name}</h3>
                  <div className="mt-4 space-y-2">
                    {table.columns.map((column) => (
                      <div className="flex items-center justify-between rounded-lg bg-white/[0.03] px-3 py-2 text-sm" key={column.name}>
                        <span>{column.primary_key ? "PK " : ""}{column.name}</span>
                        <span className="text-xs text-slate-500">{column.type}{column.nullable ? "" : " · required"}</span>
                      </div>
                    ))}
                  </div>
                  {table.foreign_keys.map((foreignKey, index) => (
                    <p className="mt-3 text-xs text-mint" key={`${foreignKey.referred_table}-${index}`}>
                      → {foreignKey.constrained_columns.join(", ")} references {foreignKey.referred_table}.{foreignKey.referred_columns.join(", ")}
                    </p>
                  ))}
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-8 rounded-xl border border-white/10 bg-panel p-5">
          <h2 className="font-semibold">Text-to-SQL</h2>
          <form className="mt-4" onSubmit={interpret}>
            <input
              className="w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-3"
              name="question"
              placeholder="How many customers are in the demo database?"
              required
              minLength={3}
            />
            <button className="mt-3 rounded-lg bg-mint px-4 py-2 text-sm font-semibold text-slate-950" type="submit">
              Interpret
            </button>
          </form>
          {queryRequest && (
            <div className="mt-5 rounded-lg border border-white/10 p-4">
              <p className="text-sm"><span className="text-slate-500">Intent:</span> {queryRequest.intent}</p>
              {queryRequest.clarification && (
                <p className="mt-3 text-sm text-amber-300">{queryRequest.clarification}</p>
              )}
              {queryRequest.generated_sql && (
                <>
                  <pre className="mt-4 overflow-auto rounded-lg bg-black/20 p-3 text-xs text-mint">{queryRequest.generated_sql}</pre>
                  <p className="mt-3 text-sm text-slate-400">{queryRequest.explanation}</p>
                  {queryRequest.status === "awaiting_approval" && (
                    <button className="mt-4 rounded-lg border border-mint px-4 py-2 text-sm text-mint" type="button" onClick={approveGeneratedSql}>
                      Approve exact SQL
                    </button>
                  )}
                  {queryRequest.status === "approved" && (
                    <button className="mt-4 rounded-lg bg-mint px-4 py-2 text-sm font-semibold text-slate-950" type="button" onClick={executeApprovedSql}>
                      Execute safely
                    </button>
                  )}
                </>
              )}
            </div>
          )}
          {execution && (
            <div className="mt-5 overflow-auto">
              <p className="mb-3 text-xs text-slate-500">{execution.row_count} row(s)</p>
              <table className="w-full text-left text-sm">
                <thead><tr>{execution.columns.map((column) => <th className="border-b border-white/10 px-2 py-2" key={column}>{column}</th>)}</tr></thead>
                <tbody>{execution.rows.map((row, rowIndex) => <tr key={rowIndex}>{row.map((value, columnIndex) => <td className="border-b border-white/[0.05] px-2 py-2" key={columnIndex}>{String(value)}</td>)}</tr>)}</tbody>
              </table>
            </div>
          )}
        </section>

        <section className="mt-8 rounded-xl border border-white/10 bg-panel p-5">
          <h2 className="font-semibold">Provider test</h2>
          <form className="mt-4" onSubmit={generate}>
            <input className="w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-3" name="prompt" placeholder="Ask Gemini for a structured answer" required />
            <button className="mt-3 rounded-lg bg-mint px-4 py-2 text-sm font-semibold text-slate-950" type="submit">Generate</button>
          </form>
          {aiAnswer && <pre className="mt-4 whitespace-pre-wrap text-sm text-slate-300">{aiAnswer}</pre>}
        </section>
      </div>
    </main>
  );
}
