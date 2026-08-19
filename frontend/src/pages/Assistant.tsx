import { useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { assistantApi, governanceApi } from "../api";
import type { AssistantMode, AssistantResponse } from "../api/types";
import { Badge, Button, Card } from "../components/ui";

const MODES: { mode: AssistantMode; label: string; hint: string }[] = [
  { mode: "analyse", label: "Analyse", hint: "Score the prompt against the 9-component rubric" },
  { mode: "improve", label: "Improve", hint: "Return a strengthened version of the prompt" },
  { mode: "generate", label: "Generate", hint: "Draft a fresh prompt from your intent" },
  { mode: "explain", label: "Explain", hint: "Explain what the prompt is asking for" },
];

export default function Assistant() {
  const [text, setText] = useState("");
  const [mode, setMode] = useState<AssistantMode>("analyse");
  const [result, setResult] = useState<AssistantResponse | null>(null);
  const [scan, setScan] = useState<{ findings: { severity: string; category: string; detail: string }[]; safe: boolean } | null>(null);
  const textRef = useRef<HTMLTextAreaElement>(null);

  const run = useMutation({
    mutationFn: () => assistantApi.invoke(mode, { prompt: text, mode }),
    onSuccess: setResult,
  });

  const scanPrompt = useMutation({
    mutationFn: () => governanceApi.scan(text),
    onSuccess: setScan,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Prompt Assistant</h1>
        <p className="text-sm text-slate-500">Analyse, improve, generate and explain prompts with the deterministic quality engine.</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Input">
          <div className="mb-3 flex flex-wrap gap-2">
            {MODES.map((m) => (
              <Button
                key={m.mode}
                variant={mode === m.mode ? "primary" : "secondary"}
                onClick={() => setMode(m.mode)}
                title={m.hint}
              >
                {m.label}
              </Button>
            ))}
          </div>
          <textarea
            ref={textRef}
            rows={12}
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-sm focus:border-brand-500 focus:outline-none"
            placeholder="Paste a prompt to analyse, or describe what you want to generate…"
          />
          <div className="mt-3 flex items-center gap-2">
            <Button disabled={run.isPending || !text.trim()} onClick={() => run.mutate()}>
              {run.isPending ? "Running…" : "Run"}
            </Button>
            <Button variant="secondary" disabled={scanPrompt.isPending || !text.trim()} onClick={() => scanPrompt.mutate()}>
              Security scan
            </Button>
          </div>
          {scan && (
            <div className={`mt-3 rounded-md p-2 text-sm ${scan.safe ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
              {scan.safe ? "✓ No security findings" : `${scan.findings.length} finding(s)`}
              {!scan.safe && (
                <ul className="mt-1 list-disc pl-5 text-xs">
                  {scan.findings.map((f, i) => (
                    <li key={i}>
                      [{f.severity}] {f.category}: {f.detail}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </Card>

        <Card title={`Result · ${mode}`}>
          {run.isPending ? (
            <div className="flex items-center gap-2 py-8 text-sm text-slate-500">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
              Analysing…
            </div>
          ) : !result ? (
            <p className="py-8 text-center text-sm text-slate-400">Run the assistant to see the score, breakdown and recommendations.</p>
          ) : (
            <div className="space-y-4 text-sm">
              <div className="flex items-center gap-3">
                <Badge color={result.score >= 80 ? "green" : result.score >= 65 ? "amber" : "red"}>
                  {result.score}/100 · {result.rating}
                </Badge>
              </div>

              {result.breakdown && Object.keys(result.breakdown).length > 0 && (
                <div>
                  <h4 className="mb-1 text-xs font-semibold uppercase text-slate-400">Rubric breakdown</h4>
                  <div className="grid grid-cols-2 gap-1.5">
                    {Object.entries(result.breakdown).map(([comp, v]) => {
                      const score = Number(v.scored ?? 0);
                      const max = Number(v.max ?? score);
                      return (
                        <div key={comp} className="flex items-center justify-between rounded bg-slate-50 px-2 py-1">
                          <span className="capitalize text-slate-600">{comp}</span>
                          <span className={`font-semibold ${score >= max * 0.7 ? "text-emerald-600" : "text-amber-600"}`}>
                            {score}/{max}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {result.missing.length > 0 && (
                <div>
                  <h4 className="mb-1 text-xs font-semibold uppercase text-slate-400">Missing</h4>
                  <ul className="list-disc pl-4 text-amber-700">
                    {result.missing.map((m, i) => <li key={i}>{m}</li>)}
                  </ul>
                </div>
              )}

              {result.present.length > 0 && (
                <div>
                  <h4 className="mb-1 text-xs font-semibold uppercase text-slate-400">Present</h4>
                  <ul className="list-disc pl-4 text-emerald-700">
                    {result.present.map((p, i) => <li key={i}>{p}</li>)}
                  </ul>
                </div>
              )}

              {result.recommendations.length > 0 && (
                <div>
                  <h4 className="mb-1 text-xs font-semibold uppercase text-slate-400">Recommendations</h4>
                  <ul className="list-disc pl-4 text-slate-600">
                    {result.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                </div>
              )}

              {result.improved_prompt && (
                <div>
                  <h4 className="mb-1 text-xs font-semibold uppercase text-slate-400">Improved prompt</h4>
                  <pre className="code rounded bg-slate-50 p-2 text-slate-700">{result.improved_prompt}</pre>
                </div>
              )}

              {result.generated_prompt && (
                <div>
                  <h4 className="mb-1 text-xs font-semibold uppercase text-slate-400">Generated prompt</h4>
                  <pre className="code rounded bg-slate-50 p-2 text-slate-700">{result.generated_prompt}</pre>
                </div>
              )}

              {result.explanation && (
                <div>
                  <h4 className="mb-1 text-xs font-semibold uppercase text-slate-400">Explanation</h4>
                  <p className="text-slate-600">{result.explanation}</p>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}