import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { analyticsApi, executionApi, governanceApi, promptsApi } from "../api";
import { Badge, Card, Spinner, StatCard, StatusBadge } from "../components/ui";

export default function Dashboard() {
  const { data: overview, isLoading: loadingOv } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: analyticsApi.overview,
  });
  const { data: governance } = useQuery({ queryKey: ["gov-summary"], queryFn: governanceApi.summary });
  const { data: prompts } = useQuery({
    queryKey: ["prompts", { sort: "executions", page_size: 5 }],
    queryFn: () => promptsApi.list({ sort: "executions", page_size: 5 }),
  });
  const { data: executions } = useQuery({
    queryKey: ["executions", { limit: 6 }],
    queryFn: () => executionApi.list({ limit: 6 }),
  });

  if (loadingOv) return <Spinner label="Loading dashboard…" />;

  const top = (overview?.top_prompts ?? []) as Array<Record<string, string | number>>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <p className="text-sm text-slate-500">
          PromptHub Enterprise — library, engineering, testing & governance at a glance.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Prompts" value={overview?.prompt_count ?? 0} sub={`${overview?.published_count ?? 0} published`} />
        <StatCard label="Executions" value={overview?.execution_count ?? 0} sub={`${Math.round(overview?.success_rate ?? 0)}% success`} />
        <StatCard
          label="Minutes saved"
          value={Math.round(overview?.estimated_time_saved_minutes ?? 0)}
          sub={`avg ${Math.round(overview?.avg_latency_ms ?? 0)} ms / run`}
        />
        <StatCard
          label="Avg rating"
          value={`${(overview?.avg_rating ?? 0).toFixed(2)} ★`}
          sub={`${overview?.rating_count ?? 0} ratings`}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Top prompts by execution" action={<Link className="text-xs font-medium text-brand-600 hover:underline" to="/analytics">View analytics →</Link>}>
          {top.length === 0 ? (
            <p className="py-6 text-sm text-slate-400">No execution data yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-400">
                  <th className="py-2">Prompt</th>
                  <th className="py-2">Executions</th>
                  <th className="py-2">Min saved</th>
                </tr>
              </thead>
              <tbody>
                {top.slice(0, 6).map((p) => (
                  <tr key={String(p.prompt_id ?? p.name)} className="border-b border-slate-50 last:border-0">
                    <td className="py-2">
                      <Link className="font-medium text-slate-800 hover:text-brand-600" to={`/prompts/${p.prompt_id}`}>
                        {String(p.name)}
                      </Link>
                      <div className="text-xs text-slate-400">{String(p.task ?? "")}</div>
                    </td>
                    <td className="py-2">{String(p.count ?? 0)}</td>
                    <td className="py-2">{Math.round(Number(p.time_saved ?? 0))}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        <Card title="Governance posture" action={<Link className="text-xs font-medium text-brand-600 hover:underline" to="/governance">Open governance →</Link>}>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg border border-slate-100 p-3">
              <div className="text-xs text-slate-400">High risk</div>
              <div className="text-2xl font-semibold text-red-600">{governance?.high_risk ?? 0}</div>
            </div>
            <div className="rounded-lg border border-slate-100 p-3">
              <div className="text-xs text-slate-400">Awaiting approval</div>
              <div className="text-2xl font-semibold text-amber-600">{governance?.awaiting_approval ?? 0}</div>
            </div>
            <div className="rounded-lg border border-slate-100 p-3">
              <div className="text-xs text-slate-400">Missing owner</div>
              <div className="text-2xl font-semibold text-slate-700">{governance?.missing_owner ?? 0}</div>
            </div>
            <div className="rounded-lg border border-slate-100 p-3">
              <div className="text-xs text-slate-400">Deprecated</div>
              <div className="text-2xl font-semibold text-slate-700">{governance?.deprecated ?? 0}</div>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Recently executed" action={<Link className="text-xs font-medium text-brand-600 hover:underline" to="/workflows">Workflows →</Link>}>
          {!executions?.items || executions.items.length === 0 ? (
            <p className="py-6 text-sm text-slate-400">No executions yet.</p>
          ) : (
            <ul className="divide-y divide-slate-50">
              {executions.items.slice(0, 6).map((e) => (
                <li key={e.execution_id} className="flex items-center justify-between py-2 text-sm">
                  <div>
                    <Link className="font-medium text-slate-800 hover:text-brand-600" to={`/prompts/${e.prompt_id}`}>
                      #{e.prompt_id}
                    </Link>
                    <span className="ml-2 text-xs text-slate-400">{e.execution_id}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-400">{e.latency_ms} ms</span>
                    <StatusBadge status={e.status} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="Highest quality prompts" action={<Link className="text-xs font-medium text-brand-600 hover:underline" to="/library">Browse library →</Link>}>
          {!prompts?.items || prompts.items.length === 0 ? (
            <p className="py-6 text-sm text-slate-400">No prompts yet.</p>
          ) : (
            <div className="space-y-2">
              {prompts.items.map((p) => (
                <div key={p.prompt_id} className="flex items-center justify-between rounded-md border border-slate-100 p-2">
                  <div className="min-w-0">
                    <Link className="block truncate text-sm font-medium text-slate-800 hover:text-brand-600" to={`/prompts/${p.prompt_id}`}>
                      {p.name}
                    </Link>
                    <Badge color="slate">{p.task}</Badge>
                  </div>
                  <span className="text-xs text-slate-400">{p.rating_avg} ★</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}