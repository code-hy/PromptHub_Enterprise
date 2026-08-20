import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { governanceApi } from "../api";
import type { GovernanceEvaluationIn, GovernanceEvaluationOut } from "../api/types";
import { Badge, Button, Card, Empty, Spinner, StatCard } from "../components/ui";
import { formatTime } from "../lib/format";

const EMPTY_EVAL: GovernanceEvaluationIn = {
  data_classification: "INTERNAL",
  risk_level: "LOW",
  contains_pii: false,
  contains_financial_data: false,
  contains_customer_data: false,
  external_sharing: "PROHIBITED",
  llm_provider: "mock",
};

export default function Governance() {
  const { data: summary, isLoading } = useQuery({ queryKey: ["gov-summary"], queryFn: governanceApi.summary });
  const { data: policies } = useQuery({ queryKey: ["gov-policies"], queryFn: governanceApi.policies });
  const { data: violations } = useQuery({ queryKey: ["gov-violations"], queryFn: governanceApi.violations });

  const [evalIn, setEvalIn] = useState<GovernanceEvaluationIn>(EMPTY_EVAL);
  const [evalOut, setEvalOut] = useState<GovernanceEvaluationOut | null>(null);

  const queryClient = useQueryClient();
  const evaluate = useMutation({
    mutationFn: () => governanceApi.evaluate(evalIn),
    onSuccess: setEvalOut,
  });

  if (isLoading) return <Spinner label="Loading governance…" />;

  const riskDist = (summary?.risk_distribution ?? []).map((r) => ({
    level: String(r.name ?? "unknown"),
    count: Number(r.count ?? 0),
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Governance</h1>
        <p className="text-sm text-slate-500">Policy enforcement, risk posture and compliance checks.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total prompts" value={summary?.total_prompts ?? 0} sub={`${summary?.published ?? 0} published`} />
        <StatCard label="High risk" value={summary?.high_risk ?? 0} sub="need attention" />
        <StatCard label="Awaiting approval" value={summary?.awaiting_approval ?? 0} />
        <StatCard label="Deprecated" value={summary?.deprecated ?? 0} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Risk distribution">
          {riskDist.length === 0 ? (
            <p className="py-4 text-center text-sm text-slate-400">No data.</p>
          ) : (
            <div className="space-y-2">
              {riskDist.map((r) => (
                <div key={r.level} className="flex items-center gap-2 text-sm">
                  <span className="w-20 text-slate-600">{r.level}</span>
                  <div className="h-3 flex-1 overflow-hidden rounded bg-slate-100">
                    <div
                      className={`h-full rounded ${
                        r.level === "HIGH" ? "bg-red-500" : r.level === "MEDIUM" ? "bg-amber-400" : "bg-emerald-400"
                      }`}
                      style={{ width: `${Math.min(100, (r.count / Math.max(1, summary!.total_prompts)) * 100)}%` }}
                    />
                  </div>
                  <span className="w-8 text-right text-slate-500">{r.count}</span>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Violations">
          {!violations || violations.items.length === 0 ? (
            <Empty message="No compliance violations recorded." />
          ) : (
            <ul className="divide-y divide-slate-50">
              {violations.items.map((v) => (
                <li key={v.id} className="py-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-700">{v.policy_id}</span>
                    <Badge color={v.severity === "HIGH" ? "red" : "amber"}>{v.severity}</Badge>
                  </div>
                  <p className="mt-0.5 text-xs text-slate-500">{v.message}</p>
                  <span className="text-[10px] text-slate-400">{formatTime(v.created_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Evaluation sandbox">
          <p className="mb-3 text-xs text-slate-500">Simulate a governance decision for a set of attributes.</p>
          <div className="grid grid-cols-2 gap-3">
            <label className="text-sm">
              <span className="block text-xs font-semibold uppercase text-slate-400">Classification</span>
              <select className={inputCls} value={evalIn.data_classification} onChange={(e) => setEvalIn({ ...evalIn, data_classification: e.target.value })}>
                {["INTERNAL", "RESTRICTED", "CONFIDENTIAL", "PUBLIC", "HIGHLY_RESTRICTED"].map((c) => <option key={c}>{c}</option>)}
              </select>
            </label>
            <label className="text-sm">
              <span className="block text-xs font-semibold uppercase text-slate-400">Risk level</span>
              <select className={inputCls} value={evalIn.risk_level} onChange={(e) => setEvalIn({ ...evalIn, risk_level: e.target.value })}>
                {["LOW", "MEDIUM", "HIGH"].map((c) => <option key={c}>{c}</option>)}
              </select>
            </label>
            <label className="text-sm">
              <span className="block text-xs font-semibold uppercase text-slate-400">External sharing</span>
              <select className={inputCls} value={evalIn.external_sharing} onChange={(e) => setEvalIn({ ...evalIn, external_sharing: e.target.value })}>
                <option>PROHIBITED</option>
                <option>APPROVAL_REQUIRED</option>
                <option>ALLOWED</option>
              </select>
            </label>
            <label className="text-sm">
              <span className="block text-xs font-semibold uppercase text-slate-400">LLM provider</span>
              <select className={inputCls} value={evalIn.llm_provider} onChange={(e) => setEvalIn({ ...evalIn, llm_provider: e.target.value })}>
                {["mock", "ollama", "openai", "azure-openai", "litellm"].map((c) => <option key={c}>{c}</option>)}
              </select>
            </label>
          </div>
          <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-600">
            <Toggle label="Contains PII" checked={evalIn.contains_pii ?? false} onChange={(v) => setEvalIn({ ...evalIn, contains_pii: v })} />
            <Toggle label="Financial data" checked={evalIn.contains_financial_data ?? false} onChange={(v) => setEvalIn({ ...evalIn, contains_financial_data: v })} />
            <Toggle label="Customer data" checked={evalIn.contains_customer_data ?? false} onChange={(v) => setEvalIn({ ...evalIn, contains_customer_data: v })} />
          </div>
          <Button className="mt-4" disabled={evaluate.isPending} onClick={() => evaluate.mutate()}>
            {evaluate.isPending ? "Evaluating…" : "Evaluate"}
          </Button>
          {evalOut && (
            <div className="mt-3 space-y-2">
              <div className={evalOut.approved ? "text-emerald-600" : "text-red-600"}>
                {evalOut.approved ? "✓ Approved" : "✗ Not approved"}
              </div>
              {evalOut.violations.map((v, i) => (
                <div key={i} className="rounded-md bg-red-50 p-2 text-xs text-red-700">
                  <b>{String(v.policy)}</b> — {String(v.message ?? v.rule)}
                </div>
              ))}
              {evalOut.decisions.map((d, i) => (
                <div key={i} className="rounded-md bg-slate-50 p-2 text-xs text-slate-600">
                  {String(d.type ?? d.policy ?? d.policy_name)} → <b>{String(d.label ?? d.decision ?? d.action)}</b>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Active policies" action={
          <Button variant="ghost" className="px-2 py-1 text-xs" onClick={() => queryClient.invalidateQueries({ queryKey: ["gov-policies"] })}>
            Refresh
          </Button>
        }>
          {!policies || policies.length === 0 ? (
            <Empty message="No policies defined." />
          ) : (
            <ul className="divide-y divide-slate-50">
              {policies.map((p) => (
                <li key={p.id} className="py-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-800">{p.name}</span>
                    <Badge color={p.severity === "HIGH" ? "red" : p.severity === "MEDIUM" ? "amber" : "blue"}>{p.severity}</Badge>
                  </div>
                  <p className="mt-0.5 text-xs text-slate-500">{p.description}</p>
                  <pre className="code mt-1 rounded bg-slate-50 p-2 text-[10px] text-slate-500">
                    {JSON.stringify({ condition: p.condition, action: p.action }, null, 1)}
                  </pre>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-center gap-1.5">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      {label}
    </label>
  );
}

const inputCls = "w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:border-brand-500 focus:outline-none";