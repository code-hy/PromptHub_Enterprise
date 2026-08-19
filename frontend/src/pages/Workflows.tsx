import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { workflowsApi } from "../api";
import type { WorkflowExecutionOut, WorkflowOut } from "../api/types";
import { Badge, Button, Card, Empty, Spinner, StatusBadge } from "../components/ui";

function extractWorkflowInputs(wf: WorkflowOut): string[] {
  const inputs = new Set<string>();
  for (const step of wf.steps) {
    for (const target of Object.values(step.input_mapping)) {
      if (target.startsWith("input.")) {
        inputs.add(target.slice(6));
      }
    }
  }
  return Array.from(inputs);
}

export default function Workflows() {
  const { data: list, isLoading } = useQuery({ queryKey: ["workflows"], queryFn: workflowsApi.list });
  const [running, setRunning] = useState<WorkflowExecutionOut | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [configuring, setConfiguring] = useState<WorkflowOut | null>(null);
  const [inputValues, setInputValues] = useState<Record<string, string>>({});

  const run = useMutation({
    mutationFn: ({ wf, inputs }: { wf: WorkflowOut; inputs: Record<string, string> }) =>
      workflowsApi.run(wf.workflow_id, { input_data: inputs }),
    onMutate: () => setBusyId(configuring?.id ?? null),
    onSuccess: (exec) => {
      setRunning(exec);
      setBusyId(null);
      setConfiguring(null);
      setInputValues({});
    },
    onError: (e) => {
      setError(e instanceof Error ? e.message : "Run failed");
      setBusyId(null);
    },
  });

  if (isLoading) return <Spinner label="Loading workflows…" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Workflows</h1>
        <p className="text-sm text-slate-500">Chain prompts together as repeatable, governed promptbooks.</p>
      </div>

      {error && <p className="rounded-md bg-red-50 p-2 text-sm text-red-600">{error}</p>}

      {running && (
        <Card title={`Run ${running.execution_id}`}>
          <div className="mb-2 flex items-center gap-3">
            <StatusBadge status={running.status} />
            <span className="text-xs text-slate-400">
              {running.workflow_name} · {running.latency_ms} ms
            </span>
          </div>
          <ol className="space-y-2">
            {running.step_results.map((s, i) => (
              <li key={i} className="rounded-md border border-slate-100 p-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-700">
                    {s.sequence}. {s.step_name || s.prompt_name}
                  </span>
                  <StatusBadge status={s.status} />
                </div>
                {s.output && <pre className="code mt-1 max-h-40 overflow-y-auto text-slate-600">{s.output}</pre>}
              </li>
            ))}
          </ol>
          {running.final_output && (
            <div className="mt-3">
              <h4 className="mb-1 text-xs font-semibold uppercase text-slate-400">Final output</h4>
              <pre className="code rounded bg-slate-50 p-2 text-slate-700">{running.final_output}</pre>
            </div>
          )}
        </Card>
      )}

      {configuring && (
        <Card title={`Configure: ${configuring.name}`}>
          <p className="mb-3 text-sm text-slate-500">{configuring.description}</p>
          <div className="space-y-3">
            {extractWorkflowInputs(configuring).map((key) => (
              <div key={key}>
                <label className="mb-1 block text-sm font-medium text-slate-700">{key}</label>
                <textarea
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
                  rows={3}
                  placeholder={`Enter ${key}…`}
                  value={inputValues[key] ?? ""}
                  onChange={(e) => setInputValues((prev) => ({ ...prev, [key]: e.target.value }))}
                />
              </div>
            ))}
          </div>
          <div className="mt-4 flex gap-2">
            <Button
              disabled={busyId === configuring.id}
              onClick={() => run.mutate({ wf: configuring, inputs: inputValues })}
            >
              {busyId === configuring.id ? "Running…" : "Run workflow"}
            </Button>
            <button
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50"
              onClick={() => { setConfiguring(null); setInputValues({}); }}
            >
              Cancel
            </button>
          </div>
        </Card>
      )}

      {!list || list.items.length === 0 ? (
        <Card>
          <Empty message="No workflows defined." />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {list.items.map((wf) => (
            <div key={wf.id} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium text-slate-900">{wf.name}</h3>
                  <p className="mt-0.5 text-sm text-slate-500">{wf.description || "No description."}</p>
                </div>
                <StatusBadge status={wf.status} />
              </div>
              <div className="mt-2 flex flex-wrap gap-1.5">
                <Badge color="blue">{wf.business_function || "GENERIC"}</Badge>
                <span className="text-xs text-slate-400">{wf.steps.length} steps</span>
                <span className="text-xs text-slate-400">
                  saves ~{wf.estimated_manual_minutes - wf.estimated_ai_minutes} min/run
                </span>
              </div>
              <ol className="mt-3 space-y-1">
                {wf.steps.map((s) => (
                  <li key={s.step_id} className="flex items-center gap-2 text-sm">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-brand-50 text-[10px] font-bold text-brand-700">
                      {s.sequence}
                    </span>
                    <Link
                      className="truncate text-slate-700 hover:text-brand-600"
                      to={`/prompts/${s.prompt_id}`}
                      title={s.prompt_name}
                    >
                      {s.name || s.prompt_name}
                    </Link>
                    <span className="ml-auto shrink-0 text-xs text-slate-400">{s.sequence === wf.steps.length ? "→ done" : "→"}</span>
                  </li>
                ))}
              </ol>
              <Button className="mt-3 w-full" onClick={() => { setConfiguring(wf); setInputValues({}); }}>
                Configure & run
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
