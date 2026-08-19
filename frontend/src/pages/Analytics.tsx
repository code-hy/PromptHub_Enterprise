import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { analyticsApi } from "../api";
import { Card, Spinner, StatCard } from "../components/ui";

const PALETTE = ["#3388ff", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444", "#14b8a6", "#f97316"];

export default function Analytics() {
  const { data: o, isLoading } = useQuery({ queryKey: ["analytics-overview"], queryFn: analyticsApi.overview });

  if (isLoading) return <Spinner label="Loading analytics…" />;
  if (!o) return <p className="text-sm text-slate-400">No data.</p>;

  const byDay = (o.executions_by_day ?? []).map((d) => ({
    date: String(d.date ?? "").slice(5, 10) || String(d.date ?? ""),
    executions: Number(d.count ?? 0),
  }));
  const top = (o.top_prompts ?? []).map((p) => ({
    name: String(p.name ?? "").slice(0, 18),
    executions: Number(p.count ?? 0),
  }));
  const byCategory = (o.execution_by_category ?? []).map((c) => ({
    name: String(c.name ?? "other"),
    value: Number(c.count ?? 0),
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Analytics</h1>
        <p className="text-sm text-slate-500">Usage, quality and productivity across the platform.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Executions" value={o.execution_count ?? 0} sub={`${Math.round(o.success_rate ?? 0)}% success`} />
        <StatCard label="Minutes saved" value={Math.round(o.estimated_time_saved_minutes ?? 0)} />
        <StatCard label="Avg latency" value={`${Math.round(o.avg_latency_ms ?? 0)} ms`} sub={`${o.avg_tokens ?? 0} tokens avg`} />
        <StatCard label="Avg rating" value={`${(o.avg_rating ?? 0).toFixed(2)} ★`} sub={`${o.rating_count ?? 0} ratings`} />
      </div>

      <Card title="Executions per day">
        {byDay.length === 0 ? (
          <p className="py-6 text-center text-sm text-slate-400">No daily data.</p>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={byDay}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line type="monotone" dataKey="executions" stroke="#3388ff" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Top prompts by executions">
          {top.length === 0 ? (
            <p className="py-6 text-center text-sm text-slate-400">No data.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={top} layout="vertical" margin={{ left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="executions" fill="#3388ff" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card title="Executions by category">
          {byCategory.length === 0 ? (
            <p className="py-6 text-center text-sm text-slate-400">No data.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={byCategory} dataKey="value" nameKey="name" outerRadius={90} label>
                  {byCategory.map((_, i) => (
                    <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>
    </div>
  );
}