import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, Database, ShieldCheck, Sparkles } from "lucide-react";

import { fetchLiveness } from "../api/health";

const pillars = [
  {
    icon: Database,
    title: "Context before queries",
    description: "Use relevant schema and approved business definitions—not guesses.",
  },
  {
    icon: ShieldCheck,
    title: "A deliberate safety gate",
    description: "Review generated SQL before a read-only execution is approved.",
  },
  {
    icon: Sparkles,
    title: "Answers you can inspect",
    description: "Trace results to the query, tables, filters, and metric used.",
  },
];

export function HomePage() {
  const health = useQuery({
    queryKey: ["api-liveness"],
    queryFn: fetchLiveness,
    retry: 1,
    refetchInterval: 30_000,
  });

  const isOnline = health.data?.status === "ok";

  return (
    <main className="min-h-screen overflow-hidden bg-canvas text-slate-100">
      <div className="pointer-events-none absolute -right-36 -top-40 h-[34rem] w-[34rem] rounded-full bg-mint/10 blur-[120px]" />
      <div className="relative mx-auto max-w-7xl px-6 pb-20 pt-7 sm:px-10">
        <header className="flex items-center justify-between">
          <a className="flex items-center gap-3" href="/" aria-label="QueryGenius home">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-mint text-slate-950">
              <Sparkles size={21} aria-hidden="true" />
            </span>
            <span className="text-lg font-semibold tracking-tight">QueryGenius</span>
          </a>
          <div
            className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-slate-300"
            role="status"
            aria-live="polite"
          >
            <span
              className={`h-2 w-2 rounded-full ${isOnline ? "bg-emerald-400" : "bg-amber-400"}`}
            />
            {health.isPending ? "Connecting to API" : isOnline ? "API online" : "API unavailable"}
          </div>
        </header>

        <section className="grid gap-14 pb-20 pt-24 lg:grid-cols-[1.15fr_0.85fr] lg:items-center lg:pb-28 lg:pt-32">
          <div>
            <p className="mb-5 text-xs font-semibold uppercase tracking-[0.22em] text-mint">
              Ask your data. Understand your business.
            </p>
            <h1 className="max-w-3xl text-5xl font-semibold leading-[1.08] tracking-[-0.045em] sm:text-6xl lg:text-7xl">
              Your data.
              <br />
              Your questions.
              <br />
              <span className="text-mint">Clear answers.</span>
            </h1>
            <p className="mt-7 max-w-xl text-lg leading-8 text-slate-400">
              QueryGenius is being built to turn natural-language questions into SQL you can
              inspect, approve, and trust.
            </p>
            <a
              className="mt-9 inline-flex items-center gap-2 rounded-lg bg-mint px-5 py-3 font-semibold text-slate-950 transition hover:bg-emerald-200 focus:outline-none focus:ring-2 focus:ring-mint focus:ring-offset-2 focus:ring-offset-canvas"
              href="/register"
            >
              Create your account
              <ArrowUpRight size={17} aria-hidden="true" />
            </a>
            <p className="mt-3 text-xs text-slate-500">
              Phase 1 foundation · Query workspace is not available yet
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-panel/80 p-6 shadow-2xl shadow-black/20 sm:p-8">
            <div className="mb-7 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-200">A safer analytics workflow</p>
                <p className="mt-1 text-xs text-slate-500">The approval boundary is explicit</p>
              </div>
              <span className="rounded-full border border-mint/20 bg-mint/10 px-3 py-1 text-[11px] font-medium text-mint">
                IN DESIGN
              </span>
            </div>
            <div className="space-y-3">
              {["Ask a business question", "Inspect generated SQL", "Approve a safe query"].map(
                (step, index) => (
                  <div
                    className="flex items-center gap-4 rounded-xl border border-white/[0.07] bg-white/[0.025] p-4"
                    key={step}
                  >
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-white/[0.06] text-xs font-semibold text-mint">
                      0{index + 1}
                    </span>
                    <span className="text-sm text-slate-300">{step}</span>
                  </div>
                ),
              )}
            </div>
            <div className="mt-6 rounded-xl border border-dashed border-white/10 p-4 text-xs leading-5 text-slate-500">
              No database connection or query execution is exposed by this foundation screen.
            </div>
          </div>
        </section>

        <section aria-labelledby="principles-heading" className="border-t border-white/[0.08] pt-10">
          <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Product principles
              </p>
              <h2 id="principles-heading" className="mt-2 text-2xl font-semibold tracking-tight">
                Trust is part of the interface.
              </h2>
            </div>
            <p className="max-w-sm text-sm leading-6 text-slate-500">
              The current release is the application foundation, not a finished analytics product.
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {pillars.map(({ icon: Icon, title, description }) => (
              <article
                className="rounded-xl border border-white/[0.08] bg-white/[0.025] p-5"
                key={title}
              >
                <Icon className="text-mint" size={20} aria-hidden="true" />
                <h3 className="mt-5 font-medium text-slate-200">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-500">{description}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
