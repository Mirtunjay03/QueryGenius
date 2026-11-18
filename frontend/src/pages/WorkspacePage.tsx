import { useEffect, useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import {
  createWorkspace,
  listOrganizations,
  listWorkspaces,
  type Organization,
  type Workspace,
} from "../api/auth";
import { useAuth } from "../auth/AuthContext";

export function WorkspacePage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selected, setSelected] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!auth.accessToken) return;
    listOrganizations(auth.accessToken)
      .then((rows) => {
        setOrganizations(rows);
        setSelected(rows[0]?.id ?? "");
      })
      .catch((requestError) =>
        setError(requestError instanceof Error ? requestError.message : "Could not load organizations"),
      );
  }, [auth.accessToken]);

  useEffect(() => {
    if (!auth.accessToken || !selected) return;
    listWorkspaces(auth.accessToken, selected)
      .then(setWorkspaces)
      .catch((requestError) =>
        setError(requestError instanceof Error ? requestError.message : "Could not load workspaces"),
      );
  }, [auth.accessToken, selected]);

  if (!auth.isLoading && !auth.accessToken) return <Navigate replace to="/login" />;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!auth.accessToken || !selected) return;
    const form = new FormData(event.currentTarget);
    try {
      const workspace = await createWorkspace(auth.accessToken, selected, {
        name: String(form.get("name")),
        slug: String(form.get("slug")),
      });
      setWorkspaces((current) => [...current, workspace]);
      event.currentTarget.reset();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not create workspace");
    }
  }

  const organization = organizations.find((row) => row.id === selected);
  const canCreate = organization?.role === "owner" || organization?.role === "admin";

  return (
    <main className="min-h-screen bg-canvas px-6 py-8 text-slate-100">
      <div className="mx-auto max-w-5xl">
        <header className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-mint">QueryGenius</p>
            <h1 className="mt-2 text-3xl font-semibold">Workspaces</h1>
          </div>
          <button
            className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300"
            type="button"
            onClick={() => {
              auth.logout();
              navigate("/login");
            }}
          >
            Sign out
          </button>
        </header>

        {organizations.length > 0 && (
          <button
            className="mt-5 rounded-lg border border-mint/30 px-4 py-2 text-sm text-mint"
            type="button"
            onClick={() => navigate(`/intelligence?workspace=${selected}`)}
          >
            Open schema intelligence
          </button>
        )}

        {organizations.length > 0 && (
          <div className="mt-8 flex gap-3">
            {organizations.map((row) => (
              <button
                className={`rounded-lg border px-4 py-2 text-sm ${row.id === selected ? "border-mint bg-mint/10 text-mint" : "border-white/10 text-slate-400"}`}
                key={row.id}
                type="button"
                onClick={() => setSelected(row.id)}
              >
                {row.name} · {row.role}
              </button>
            ))}
          </div>
        )}

        {error && <p className="mt-5 text-sm text-red-400">{error}</p>}

        <section className="mt-8 grid gap-5 md:grid-cols-2">
          {workspaces.map((workspace) => (
            <article className="rounded-xl border border-white/10 bg-panel p-5" key={workspace.id}>
              <h2 className="font-semibold">{workspace.name}</h2>
              <p className="mt-2 text-sm text-slate-500">{workspace.slug}</p>
            </article>
          ))}
          {workspaces.length === 0 && (
            <p className="rounded-xl border border-dashed border-white/10 p-6 text-sm text-slate-500">
              No workspaces in this organization yet.
            </p>
          )}
        </section>

        {canCreate && (
          <form className="mt-8 rounded-xl border border-white/10 bg-panel p-5" onSubmit={submit}>
            <h2 className="font-semibold">Create workspace</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <input className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-3" name="name" placeholder="Workspace name" required />
              <input className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-3" name="slug" placeholder="sales" pattern="[a-z0-9]+(?:-[a-z0-9]+)*" required />
            </div>
            <button className="mt-4 rounded-lg bg-mint px-4 py-2 text-sm font-semibold text-slate-950" type="submit">
              Create
            </button>
          </form>
        )}
      </div>
    </main>
  );
}
