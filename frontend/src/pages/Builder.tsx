import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { assistantApi, catalogApi, promptsApi } from "../api";
import type { AssistantMode, AssistantResponse, PromptCreatePayload, PromptInputIn } from "../api/types";
import { Badge, Button, Card, Spinner, StatusBadge } from "../components/ui";

const EMPTY: PromptCreatePayload = {
  name: "",
  description: "",
  business_function: "GENERIC",
  application: "GENERIC_AI",
  task: "ANALYSE",
  goal: "",
  context: "",
  source: "",
  expectations: "",
  system_instruction: "",
  prompt_template: "",
  audience: "GENERAL",
  tone: "PROFESSIONAL",
  output_format: "FREE_TEXT",
  max_length: "",
  data_classification: "INTERNAL",
  risk_level: "LOW",
  requires_approval: false,
  contains_pii: false,
  contains_financial_data: false,
  contains_customer_data: false,
  external_sharing: "PROHIBITED",
  temperature: 0.2,
  require_evidence: false,
  avoid_unsupported_claims: false,
  ask_clarification_questions: false,
  manual_time_minutes: 30,
  ai_time_minutes: 5,
  tags: [],
  inputs: [],
};

export default function Builder() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEdit = !!id;

  const { data: catalog } = useQuery({ queryKey: ["catalog"], queryFn: catalogApi.get });
  const { data: existing } = useQuery({
    queryKey: ["prompt", id],
    queryFn: () => promptsApi.get(id!),
    enabled: isEdit,
  });

  const [form, setForm] = useState<PromptCreatePayload>(EMPTY);
  const [inputs, setInputs] = useState<PromptInputIn[]>([]);
  const [tags, setTags] = useState<string>("");
  const [assist, setAssist] = useState<AssistantResponse | null>(null);

  useEffect(() => {
    if (existing) {
      setForm({
        ...EMPTY,
        name: existing.name,
        description: existing.description,
        business_function: existing.business_function,
        application: existing.application,
        task: existing.task,
        goal: existing.goal,
        context: existing.context,
        source: existing.source,
        expectations: existing.expectations,
        system_instruction: existing.system_instruction,
        prompt_template: existing.prompt_template,
        audience: existing.audience,
        tone: existing.tone,
        output_format: existing.output_format,
        max_length: existing.max_length,
        data_classification: existing.data_classification,
        risk_level: existing.risk_level,
        requires_approval: existing.requires_approval,
        contains_pii: existing.contains_pii,
        contains_financial_data: existing.contains_financial_data,
        contains_customer_data: existing.contains_customer_data,
        external_sharing: existing.external_sharing,
        temperature: existing.temperature,
        require_evidence: existing.require_evidence,
        avoid_unsupported_claims: existing.avoid_unsupported_claims,
        ask_clarification_questions: existing.ask_clarification_questions,
        manual_time_minutes: existing.manual_time_minutes,
        ai_time_minutes: existing.ai_time_minutes,
        tags: existing.tags,
        inputs: [],
      });
      setInputs(existing.inputs.map((i) => ({
        name: i.name,
        input_type: i.input_type,
        required: i.required,
        description: i.description,
        sample_value: i.sample_value,
      })));
    }
  }, [existing]);

  const save = useMutation({
    mutationFn: () => {
      const payload = { ...form, tags: tags.split(",").map((t) => t.trim()).filter(Boolean), inputs };
      return isEdit ? promptsApi.update(id!, payload) : promptsApi.create(payload);
    },
    onSuccess: (p) => {
      queryClient.invalidateQueries({ queryKey: ["prompts"] });
      queryClient.invalidateQueries({ queryKey: ["prompt", p.prompt_id] });
      navigate(`/prompts/${p.prompt_id}`);
    },
  });

  const assistMut = useMutation({
    mutationFn: ({ mode }: { mode: AssistantMode }) =>
      assistantApi.invoke(mode, {
        prompt: buildPromptText(form, inputs),
        mode,
        business_function: form.business_function,
        task: form.task,
      }),
    onSuccess: setAssist,
  });

  const set = <K extends keyof PromptCreatePayload>(key: K, value: PromptCreatePayload[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const updateInput = (idx: number, patch: Partial<PromptInputIn>) =>
    setInputs((arr) => arr.map((i, n) => (n === idx ? { ...i, ...patch } : i)));

  const promptText = buildPromptText(form, inputs);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">{isEdit ? "Edit prompt" : "New prompt"}</h1>
          {isEdit && existing && (
            <div className="mt-1 flex items-center gap-2 text-xs text-slate-400">
              <span>{existing.prompt_id}</span>
              <StatusBadge status={existing.status} />
              <span>v{existing.version}</span>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          {isEdit && (
            <Button variant="secondary" onClick={() => navigate(`/prompts/${id}`)}>
              Cancel
            </Button>
          )}
          <Button disabled={save.isPending || !form.name.trim()} onClick={() => save.mutate()}>
            {save.isPending ? "Saving…" : isEdit ? "Save changes" : "Create prompt"}
          </Button>
        </div>
      </div>

      {save.isError && <p className="text-sm text-red-600">Save failed — check fields.</p>}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <Card title="Basics">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <Field label="Name *">
                <input className={inputCls} value={form.name} onChange={(e) => set("name", e.target.value)} />
              </Field>
              <Field label="Description">
                <input className={inputCls} value={form.description} onChange={(e) => set("description", e.target.value)} />
              </Field>
              <Field label="Business function">
                <select className={inputCls} value={form.business_function} onChange={(e) => set("business_function", e.target.value)}>
                  {(catalog?.business_functions ?? ["GENERIC"]).map((f) => <option key={f}>{f}</option>)}
                </select>
              </Field>
              <Field label="Application">
                <select className={inputCls} value={form.application} onChange={(e) => set("application", e.target.value)}>
                  {(catalog?.applications ?? ["GENERIC_AI"]).map((a) => <option key={a}>{a}</option>)}
                </select>
              </Field>
              <Field label="Task">
                <select className={inputCls} value={form.task} onChange={(e) => set("task", e.target.value)}>
                  {(catalog?.tasks ?? ["ANALYSE"]).map((t) => <option key={t}>{t}</option>)}
                </select>
              </Field>
              <Field label="Tags (comma separated)">
                <input className={inputCls} value={tags} onChange={(e) => setTags(e.target.value)} placeholder="finance, reporting" />
              </Field>
            </div>
          </Card>

          <Card title="Prompt structure">
            <div className="grid grid-cols-1 gap-3">
              <Field label="Goal">
                <textarea rows={2} className={inputCls} value={form.goal} onChange={(e) => set("goal", e.target.value)} />
              </Field>
              <Field label="Context">
                <textarea rows={2} className={inputCls} value={form.context} onChange={(e) => set("context", e.target.value)} />
              </Field>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <Field label="Source">
                  <textarea rows={2} className={inputCls} value={form.source} onChange={(e) => set("source", e.target.value)} />
                </Field>
                <Field label="Expectations">
                  <textarea rows={2} className={inputCls} value={form.expectations} onChange={(e) => set("expectations", e.target.value)} />
                </Field>
              </div>
              <Field label="System instruction">
                <textarea rows={2} className={inputCls} value={form.system_instruction} onChange={(e) => set("system_instruction", e.target.value)} />
              </Field>
              <Field label="Prompt template *">
                <textarea
                  rows={7}
                  className={`${inputCls} font-mono text-xs`}
                  value={form.prompt_template}
                  onChange={(e) => set("prompt_template", e.target.value)}
                  placeholder="Use {input_name} placeholders, e.g. {topic}"
                />
              </Field>
            </div>
          </Card>

          <Card title="Inputs" action={
            <Button variant="ghost" onClick={() => setInputs((a) => [...a, { name: "", required: true, input_type: "TEXT" }])}>
              + Add input
            </Button>
          }>
            {inputs.length === 0 ? (
              <p className="text-sm text-slate-400">No inputs yet — placeholders like {"{topic}"} in the template are recommended.</p>
            ) : (
              <div className="space-y-2">
                {inputs.map((inp, idx) => (
                  <div key={idx} className="grid grid-cols-12 gap-2">
                    <input
                      className={`${inputCls} col-span-3`}
                      placeholder="name (used in {name})"
                      value={inp.name}
                      onChange={(e) => updateInput(idx, { name: e.target.value })}
                    />
                    <select className={`${inputCls} col-span-2`} value={inp.input_type} onChange={(e) => updateInput(idx, { input_type: e.target.value })}>
                      <option>TEXT</option>
                      <option>NUMBER</option>
                      <option>SELECT</option>
                      <option>MULTILINE</option>
                    </select>
                    <input className={`${inputCls} col-span-4`} placeholder="description" value={inp.description} onChange={(e) => updateInput(idx, { description: e.target.value })} />
                    <input className={`${inputCls} col-span-2`} placeholder="sample" value={inp.sample_value} onChange={(e) => updateInput(idx, { sample_value: e.target.value })} />
                    <label className="col-span-1 flex items-center gap-1 text-xs text-slate-500">
                      <input type="checkbox" checked={inp.required} onChange={(e) => updateInput(idx, { required: e.target.checked })} />
                      req
                    </label>
                    <button className="col-span-1 text-red-500 hover:text-red-700" onClick={() => setInputs((a) => a.filter((_, i) => i !== idx))}>
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        <div className="space-y-6">
          <Card title="Output & tone">
            <div className="grid grid-cols-2 gap-3">
              <Field label="Audience">
                <select className={inputCls} value={form.audience} onChange={(e) => set("audience", e.target.value)}>
                  {(catalog?.audiences ?? ["GENERAL"]).map((a) => <option key={a}>{a}</option>)}
                </select>
              </Field>
              <Field label="Tone">
                <select className={inputCls} value={form.tone} onChange={(e) => set("tone", e.target.value)}>
                  {(catalog?.tones ?? ["PROFESSIONAL"]).map((t) => <option key={t}>{t}</option>)}
                </select>
              </Field>
              <Field label="Output format">
                <select className={inputCls} value={form.output_format} onChange={(e) => set("output_format", e.target.value)}>
                  {(catalog?.output_formats ?? ["FREE_TEXT"]).map((o) => <option key={o}>{o}</option>)}
                </select>
              </Field>
              <Field label="Max length">
                <input className={inputCls} value={form.max_length} onChange={(e) => set("max_length", e.target.value)} placeholder="e.g. 500 words" />
              </Field>
              <Field label="Temperature">
                <input type="number" step="0.1" min="0" max="2" className={inputCls} value={form.temperature} onChange={(e) => set("temperature", Number(e.target.value))} />
              </Field>
              <Field label="Time saved / run (min)">
                <input type="number" className={inputCls} value={form.manual_time_minutes} onChange={(e) => set("manual_time_minutes", Number(e.target.value))} />
              </Field>
            </div>
          </Card>

          <Card title="Governance">
            <div className="grid grid-cols-2 gap-3">
              <Field label="Classification">
                <select className={inputCls} value={form.data_classification} onChange={(e) => set("data_classification", e.target.value)}>
                  {(catalog?.classifications ?? ["INTERNAL"]).map((c) => <option key={c}>{c}</option>)}
                </select>
              </Field>
              <Field label="Risk level">
                <select className={inputCls} value={form.risk_level} onChange={(e) => set("risk_level", e.target.value)}>
                  {(catalog?.risk_levels ?? ["LOW"]).map((r) => <option key={r}>{r}</option>)}
                </select>
              </Field>
              <Field label="External sharing">
                <select className={inputCls} value={form.external_sharing} onChange={(e) => set("external_sharing", e.target.value)}>
                  <option>PROHIBITED</option>
                  <option>APPROVAL_REQUIRED</option>
                  <option>ALLOWED</option>
                </select>
              </Field>
            </div>
            <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-600">
              <Toggle label="Contains PII" checked={form.contains_pii} onChange={(v) => set("contains_pii", v)} />
              <Toggle label="Financial data" checked={form.contains_financial_data} onChange={(v) => set("contains_financial_data", v)} />
              <Toggle label="Customer data" checked={form.contains_customer_data} onChange={(v) => set("contains_customer_data", v)} />
              <Toggle label="Requires approval" checked={form.requires_approval} onChange={(v) => set("requires_approval", v)} />
              <Toggle label="Requires evidence" checked={form.require_evidence} onChange={(v) => set("require_evidence", v)} />
              <Toggle label="No unsupported claims" checked={form.avoid_unsupported_claims} onChange={(v) => set("avoid_unsupported_claims", v)} />
              <Toggle label="Ask clarification" checked={form.ask_clarification_questions} onChange={(v) => set("ask_clarification_questions", v)} />
            </div>
          </Card>

          <Card title="Assistant" action={
            <div className="flex gap-1">
              {(["analyse", "improve", "generate", "explain"] as AssistantMode[]).map((m) => (
                <Button key={m} variant="secondary" className="px-2 py-1 text-xs" disabled={assistMut.isPending || !promptText} onClick={() => assistMut.mutate({ mode: m })}>
                  {m}
                </Button>
              ))}
            </div>
          }>
            {assistMut.isPending ? (
              <Spinner label="Analysing prompt…" />
            ) : assist ? (
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <Badge color={assist.score >= 80 ? "green" : assist.score >= 65 ? "amber" : "red"}>
                    {assist.score}/100 · {assist.rating}
                  </Badge>
                  {assist.recommendations.length > 0 && (
                    <span className="text-xs text-slate-400">{assist.recommendations.length} recommendations</span>
                  )}
                </div>
                {assist.missing.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold uppercase text-slate-400">Missing</div>
                    <ul className="list-disc pl-4 text-xs text-amber-700">
                      {assist.missing.map((m, i) => <li key={i}>{m}</li>)}
                    </ul>
                  </div>
                )}
                {assist.improved_prompt && (
                  <Button variant="secondary" onClick={() => set("prompt_template", assist.improved_prompt)}>
                    Apply improved template
                  </Button>
                )}
                {assist.generated_prompt && (
                  <div>
                    <div className="text-xs font-semibold uppercase text-slate-400">Generated</div>
                    <pre className="code mt-1 rounded bg-slate-50 p-2 text-slate-700">{assist.generated_prompt}</pre>
                  </div>
                )}
                {assist.explanation && <p className="text-xs text-slate-500">{assist.explanation}</p>}
              </div>
            ) : (
              <p className="text-xs text-slate-400">Run the assistant on the current template to get a quality score and suggestions.</p>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

function buildPromptText(form: PromptCreatePayload, inputs: PromptInputIn[]): string {
  const parts = [
    form.goal && `Goal: ${form.goal}`,
    form.context && `Context: ${form.context}`,
    form.source && `Source: ${form.source}`,
    form.expectations && `Expectations: ${form.expectations}`,
  ].filter(Boolean);
  const vars = inputs.filter((i) => i.name).map((i) => i.name).join(", ");
  if (vars) parts.push(`Inputs: ${vars}`);
  if (form.prompt_template) parts.push(form.prompt_template);
  return parts.join("\n\n");
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="mb-0.5 block text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</span>
      {children}
    </label>
  );
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean | undefined; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-center gap-1.5">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      {label}
    </label>
  );
}

const inputCls =
  "w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:border-brand-500 focus:outline-none";