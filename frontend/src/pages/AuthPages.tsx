import { useState, type FormEvent, type ReactNode } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { login, register } from "../api/auth";
import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");

  if (auth.accessToken && auth.user) return <Navigate replace to="/workspace" />;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      const tokens = await login({
        email: String(form.get("email")),
        password: String(form.get("password")),
      });
      auth.setTokens(tokens);
      navigate("/workspace");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Login failed");
    }
  }

  return (
    <AuthLayout title="Welcome back">
      <form className="space-y-4" onSubmit={submit}>
        <AuthField label="Email" name="email" type="email" />
        <AuthField label="Password" name="password" type="password" />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button className="w-full rounded-lg bg-mint px-4 py-3 font-semibold text-slate-950" type="submit">
          Sign in
        </button>
      </form>
      <p className="mt-5 text-sm text-slate-500">
        New to QueryGenius? <Link className="text-mint" to="/register">Create an account</Link>
      </p>
    </AuthLayout>
  );
}

export function RegisterPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");

  if (auth.accessToken && auth.user) return <Navigate replace to="/workspace" />;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      const tokens = await register({
        email: String(form.get("email")),
        password: String(form.get("password")),
        display_name: String(form.get("display_name")),
        organization_name: String(form.get("organization_name")),
      });
      auth.setTokens(tokens);
      navigate("/workspace");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Registration failed");
    }
  }

  return (
    <AuthLayout title="Create your workspace">
      <form className="space-y-4" onSubmit={submit}>
        <AuthField label="Name" name="display_name" />
        <AuthField label="Organization" name="organization_name" />
        <AuthField label="Email" name="email" type="email" />
        <AuthField label="Password" name="password" type="password" />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button className="w-full rounded-lg bg-mint px-4 py-3 font-semibold text-slate-950" type="submit">
          Create account
        </button>
      </form>
      <p className="mt-5 text-sm text-slate-500">
        Already registered? <Link className="text-mint" to="/login">Sign in</Link>
      </p>
    </AuthLayout>
  );
}

function AuthLayout({ title, children }: { title: string; children: ReactNode }) {
  return (
    <main className="grid min-h-screen place-items-center bg-canvas px-6 text-slate-100">
      <section className="w-full max-w-md rounded-2xl border border-white/10 bg-panel p-7">
        <Link className="text-sm font-semibold text-mint" to="/">QueryGenius</Link>
        <h1 className="mt-7 text-3xl font-semibold">{title}</h1>
        <div className="mt-6">{children}</div>
      </section>
    </main>
  );
}

function AuthField({ label, name, type = "text" }: { label: string; name: string; type?: string }) {
  return (
    <label className="block text-sm text-slate-300">
      {label}
      <input
        className="mt-2 w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-3 text-slate-100 outline-none focus:border-mint"
        name={name}
        type={type}
        required
        minLength={type === "password" ? 12 : 2}
      />
    </label>
  );
}
