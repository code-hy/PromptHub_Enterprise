import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { catalogApi, promptsApi } from "../api";
import type { PromptSummary } from "../api/types";
import { Badge, Card, Empty, Spinner, StatusBadge } from "../components/ui";

const PAGE_SIZE = 12;

export default function Library() {
  const location = useLocation();
  const [params, setParams] = useSearchParams();
  const [search, setSearch] = useState(params.get("q") ?? "");
  const page = Number(new URLSearchParams(location.search).get("page") ?? 1);

  const filters = useMemo(
    () => ({
      search: search.trim(),
      business_function: params.get("business_function") ?? undefined,
      application: params.get("application") ?? undefined,
      task: params.get("task") ?? undefined,
      status: params.get("status") ?? undefined,
      risk_level: params.get("risk_level") ?? undefined,
      sort: params.get("sort") ?? "updated",
      page,
      page_size: PAGE_SIZE,
    }),
    [search, params, page],
  );

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["prompts", filters],
    queryFn: () => promptsApi.list(filters),
  });
  const { data: catalog } = useQuery({ queryKey: ["catalog"], queryFn: catalogApi.get });

  const setFilter = (key: string, value: string | undefined) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "page") next.set("page", "1");
    setParams(next);
  };

  const totalPages = Math.max(1, Math.ceil((data?.total ?? 0) / PAGE_SIZE));

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Prompt Library</h1>
          <p className="text-sm text-slate-500">{data?.total ?? 0} prompts</p>
        </div>
        <Link
          to="/builder"
          className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
        >
          + New prompt
        </Link>
      </div>

      <div className="flex flex-wrap gap-2">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") setFilter("page", undefined);
          }}
          placeholder="Search prompts…"
          className="min-w-56 flex-1 rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-brand-500 focus:outline-none"
        />
        <select
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          value={params.get("business_function") ?? ""}
          onChange={(e) => setFilter("business_function", e.target.value || undefined)}
        >
          <option value="">All functions</option>
          {(catalog?.business_functions ?? []).map((f) => (
            <option key={f}>{f}</option>
          ))}
        </select>
        <select
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          value={params.get("task") ?? ""}
          onChange={(e) => setFilter("task", e.target.value || undefined)}
        >
          <option value="">All tasks</option>
          {(catalog?.tasks ?? []).map((t) => (
            <option key={t}>{t}</option>
          ))}
        </select>
        <select
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          value={params.get("status") ?? ""}
          onChange={(e) => setFilter("status", e.target.value || undefined)}
        >
          <option value="">All statuses</option>
          {(catalog?.statuses ?? []).map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
        <select
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          value={params.get("risk_level") ?? ""}
          onChange={(e) => setFilter("risk_level", e.target.value || undefined)}
        >
          <option value="">All risk</option>
          {(catalog?.risk_levels ?? []).map((r) => (
            <option key={r}>{r}</option>
          ))}
        </select>
        <select
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          value={params.get("sort") ?? "updated"}
          onChange={(e) => setFilter("sort", e.target.value)}
        >
          <option value="updated">Recently updated</option>
          <option value="rating">Top rated</option>
          <option value="executions">Most used</option>
          <option value="name">Name A–Z</option>
        </select>
      </div>

      {isLoading ? (
        <Spinner label="Loading library…" />
      ) : !data || data.items.length === 0 ? (
        <Card>
          <Empty message="No prompts match your filters." />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {data.items.map((p) => (
            <PromptCard key={p.prompt_id} prompt={p} />
          ))}
        </div>
      )}

      {isFetching && !isLoading && <div className="text-xs text-slate-400">Updating…</div>}

      {totalPages > 1 && (
        <div className="flex items-center gap-2">
          <button
            disabled={page <= 1}
            onClick={() => setFilter("page", String(page - 1))}
            className="rounded-md border border-slate-300 px-3 py-1 text-sm disabled:opacity-40"
          >
            ← Prev
          </button>
          <span className="text-sm text-slate-500">
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setFilter("page", String(page + 1))}
            className="rounded-md border border-slate-300 px-3 py-1 text-sm disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}

function PromptCard({ prompt }: { prompt: PromptSummary }) {
  return (
    <Link
      to={`/prompts/${prompt.prompt_id}`}
      className="group flex flex-col rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
    >
      <div className="mb-1 flex items-start justify-between gap-2">
        <h3 className="font-medium text-slate-900 group-hover:text-brand-700">{prompt.name}</h3>
        <StatusBadge status={prompt.status} />
      </div>
      <p className="mb-3 line-clamp-2 text-sm text-slate-500">
        {prompt.description || "No description provided."}
      </p>
      <div className="mt-auto flex flex-wrap items-center gap-1.5">
        <Badge color="blue">{prompt.task}</Badge>
        <Badge color="purple">{prompt.business_function}</Badge>
        <span className="ml-auto flex items-center gap-2 text-xs text-slate-400">
          <span
            title={`Quality ${prompt.rating_avg}`}
            className={`font-semibold ${
              prompt.rating_avg >= 4 ? "text-emerald-600" : prompt.rating_avg >= 3 ? "text-amber-600" : "text-red-500"
            }`}
          >
            {prompt.rating_avg ? `${prompt.rating_avg.toFixed(1)} ★` : "—"}
          </span>
          <span>{prompt.execution_count ?? 0} runs</span>
        </span>
      </div>
    </Link>
  );
}