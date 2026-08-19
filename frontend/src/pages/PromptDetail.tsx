import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { executionApi, promptsApi } from "../api";
import type { ExecutionOut, GovernanceEvaluationOut, VersionOut } from "../api/types";
import { Badge, Button, Card, Empty, QualityRing, Spinner, StatusBadge } from "../components/ui";
import { formatTime } from "../lib/format";

const FLOW_ACTIONS = [
  { value: "submit_for_review", label: "Submit for review" },
  { value: "approve", label: "Approve" },
  { value: "reject", label: "Reject" },
  { value: "publish", label: "Publish" },
  { value: "deprecate", label: "Deprecate" },
  { value: "retire", label: "Retire" },
] as const;

export default function PromptDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [execOutput, setExecOutput] = useState<ExecutionOut | null>(null);
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [gov, setGov] = useState<GovernanceEvaluationOut | null>(null);

  const { data: prompt, isLoading, isError } = useQuery({
    queryKey: ["prompt", id],
    queryFn: () => promptsApi.get(id!),
    enabled: !!id,
  });
  const { data: versions } = useQuery({
    queryKey: ["versions", id],
    queryFn: () => promptsApi.versions(id!),
    enabled: !!id,
  });

  const flow = useMutation({
    mutationFn: ({ action, note }: { action: string; note: string }) =>
      promptsApi.flow(id!, { action: action as never, note }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prompt", id] });
      queryClient.invalidateQueries({ queryKey: ["prompts"] });
      queryClient.invalidateQueries({ queryKey: ["gov-summary"] });
    },
  });

  const runExecution = async (useGrounding: boolean) => {
    if (!prompt) return;
    setBusy(true);
    setError("");
    setExecOutput(null);
    try {
      const result = await executionApi.run({
        prompt_id: prompt.id,
        input_data: inputs,
        use_grounding: useGrounding,
      });
      setExecOutput(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Execution failed");
    } finally {
      setBusy(false);
    }
  };

  const checkGovernance = async () => {
    if (!prompt) return;
    try {
      const result = await promptsApi.governance(id!);
      setGov(result as unknown as GovernanceEvaluationOut);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Governance check failed");
    }
  };

  if (isLoading) return <Spinner label="Loading prompt…" />;
  if (isError || !prompt) {
    return (
      <Card>
        <Empty message="Prompt not found." />
        <Link to="/library" className="text-sm text-brand-600 hover:underline">
          ← Back to library
        </Link>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <Link to="/library" className="text-xs text-slate-400 hover:text-brand-600">
            ← Library
          </Link>
          <div className="mt-1 flex items-center gap-3">
            <h1 className="text-2xl font-semibold text-slate-900">{prompt.name}</h1>
            <StatusBadge status={prompt.status} />
            <span className="text-xs text-slate-400">v{prompt.version}</span>
          </div>
          <p className="mt-1 max-w-3xl text-sm text-slate-500">{prompt.description || "No description."}</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <Badge color="blue">{prompt.business_function}</Badge>
            <Badge color="purple">{prompt.application}</Badge>
            <Badge color="slate">{prompt.task}</Badge>
            <Badge color={prompt.risk_level === "HIGH" ? "red" : prompt.risk_level === "MEDIUM" ? "amber" : "green"}>
              {prompt.risk_level} risk
            </Badge>
            <Badge color="slate">{prompt.data_classification}</Badge>
            {prompt.tags.map((t) => (
              <Badge key={t}>{t}</Badge>
            ))}
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <QualityRing score={prompt.quality_score ?? 0} size={56} />
          <span className="text-xs text-slate-400">Quality</span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card title="Prompt template">
            <pre className="code rounded-md bg-slate-50 p-3 text-slate-700">{prompt.prompt_template}</pre>
            {prompt.system_instruction && (
              <>
                <h4 className="mt-3 text-xs font-semibold uppercase text-slate-400">System instruction</h4>
                <p className="mt-1 text-sm text-slate-600">{prompt.system_instruction}</p>
              </>
            )}
          </Card>

          <Card title="Structured attributes">
            <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm md:grid-cols-3">
              <Attr label="Goal" value={prompt.goal} />
              <Attr label="Context" value={prompt.context} />
              <Attr label="Source" value={prompt.source} />
              <Attr label="Expectations" value={prompt.expectations} />
              <Attr label="Audience" value={prompt.audience} />
              <Attr label="Tone" value={prompt.tone} />
              <Attr label="Output format" value={prompt.output_format} />
              <Attr label="Max length" value={prompt.max_length || "—"} />
              <Attr label="Temperature" value={String(prompt.temperature)} />
            </div>
            <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-slate-500">
              {prompt.contains_pii && <Flag>Contains PII</Flag>}
              {prompt.contains_financial_data && <Flag>Financial data</Flag>}
              {prompt.contains_customer_data && <Flag>Customer data</Flag>}
              {prompt.requires_approval && <Flag>Requires approval</Flag>}
              {prompt.require_evidence && <Flag>Requires evidence</Flag>}
              {prompt.avoid_unsupported_claims && <Flag>Avoids unsupported claims</Flag>}
              <span>External sharing: {prompt.external_sharing}</span>
              <span>Owner: {prompt.owner_name || "—"}</span>
            </div>
          </Card>

          <Card title="Versions" action={<span className="text-xs text-slate-400">{versions?.length ?? 0} total</span>}>
            {!versions || versions.length === 0 ? (
              <Empty message="No versions recorded." />
            ) : (
              <ul className="divide-y divide-slate-50">
                {versions.map((v: VersionOut) => (
                  <li key={v.id} className="flex items-center justify-between py-2 text-sm">
                    <div>
                      <span className="font-medium text-slate-800">v{v.version}</span>
                      <span className="ml-2 text-xs text-slate-400">
                        {v.approval_status || "no status"} · {formatTime(v.created_at)}
                      </span>
                    </div>
                    <div className="ml-4 max-w-md truncate text-xs text-slate-400">{v.changes}</div>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>

        <div className="space-y-6">
          <Card title="Test execution">
            {prompt.inputs.length > 0 && (
              <div className="mb-3 space-y-2">
                <h4 className="text-xs font-semibold uppercase text-slate-400">Inputs</h4>
                {prompt.inputs.map((inp) => (
                  <label key={inp.id} className="block text-sm">
                    <span className="mb-0.5 flex items-center justify-between">
                      <span className="font-medium text-slate-700">
                        {inp.name}
                        {inp.required && <span className="text-red-500"> *</span>}
                      </span>
                      <span className="text-[10px] uppercase text-slate-400">{inp.input_type}</span>
                    </span>
                    <textarea
                      rows={2}
                      defaultValue={inp.sample_value}
                      onChange={(e) => setInputs((p) => ({ ...p, [inp.name]: e.target.value }))}
                      className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-brand-500 focus:outline-none"
                      placeholder={inp.description || inp.name}
                    />
                  </label>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <Button disabled={busy} onClick={() => runExecution(false)}>
                Run (mock)
              </Button>
              <Button disabled={busy} variant="secondary" onClick={() => runExecution(true)}>
                Run with grounding
              </Button>
            </div>
            {busy && <Spinner label="Executing…" />}
            {error && <p className="mt-2 rounded-md bg-red-50 p-2 text-xs text-red-600">{error}</p>}
            {execOutput && (
              <div className="mt-3 rounded-md border border-slate-100 p-3">
                <div className="mb-1 flex items-center justify-between">
                  <StatusBadge status={execOutput.status} />
                  <span className="text-xs text-slate-400">
                    {execOutput.provider}/{execOutput.model} · {execOutput.latency_ms} ms · {execOutput.tokens} tok
                  </span>
                </div>
                <pre className="code text-slate-700">{execOutput.output}</pre>
                {execOutput.sources_used.length > 0 && (
                  <div className="mt-2 text-xs text-slate-500">
                    Sources: {execOutput.sources_used.join(", ")}
                  </div>
                )}
              </div>
            )}
          </Card>

          <Card title="Lifecycle">
            <div className="flex flex-wrap gap-2">
              {FLOW_ACTIONS.map((a) => (
                <Button
                  key={a.value}
                  variant="secondary"
                  disabled={flow.isPending}
                  onClick={() => flow.mutate({ action: a.value, note: "" })}
                >
                  {a.label}
                </Button>
              ))}
            </div>
            {flow.isError && <p className="mt-2 text-xs text-red-600">Action failed</p>}
          </Card>

          <Card title="Governance">
            <Button variant="secondary" onClick={checkGovernance}>
              Check against policies
            </Button>
            {gov && (
              <div className="mt-3 space-y-2 text-sm">
                <div className={gov.approved ? "text-emerald-600" : "text-red-600"}>
                  {gov.approved ? "✓ Approved — no violations" : "✗ Violations detected"}
                </div>
                {gov.violations.map((v, i) => (
                  <div key={i} className="rounded-md bg-red-50 p-2 text-xs text-red-700">
                    <b>{String(v.policy)}</b> — {String(v.message)}
                  </div>
                ))}
                {gov.decisions.map((d, i) => (
                  <div key={i} className="rounded-md bg-slate-50 p-2 text-xs text-slate-600">
                    {String(d.type ?? d.policy_name ?? d.policy)} → {String(d.label ?? d.decision ?? d.action)}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

function Attr({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[10px] font-semibold uppercase text-slate-400">{label}</div>
      <div className="truncate text-slate-700" title={value}>
        {value || "—"}
      </div>
    </div>
  );
}

function Flag({ children }: { children: React.ReactNode }) {
  return <span className="inline-flex items-center gap-1 font-medium text-slate-600">• {children}</span>;
}