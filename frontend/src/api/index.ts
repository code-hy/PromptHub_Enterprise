import { api } from "./client";
import type {
  AnalyticsOverview,
  AssistantMode,
  AssistantRequest,
  AssistantResponse,
  AuditListResponse,
  AuditEventOut,
  Catalog,
  ExecutionOut,
  ExecutionRequest,
  ExecutionListResponse,
  GovernanceEvaluationIn,
  GovernanceEvaluationOut,
  GovernanceSummary,
  PolicyIn,
  PolicyOut,
  PromptCreatePayload,
  PromptDetail,
  PromptFlowAction,
  PromptListResponse,
  UserSummary,
  UserCreatePayload,
  UserUpdatePayload,
  VersionOut,
  WorkflowExecutionOut,
  WorkflowListResponse,
  WorkflowOut,
  WorkflowRunRequest,
} from "./types";

export const catalogApi = {
  get: () => api.get<Catalog>("/catalog"),
};

export const promptsApi = {
  list: (params?: Record<string, string | number | boolean | undefined>) =>
    api.get<PromptListResponse>("/prompts" + toQuery(params)),
  get: (ref: string) => api.get<PromptDetail>(`/prompts/${ref}`),
  create: (data: PromptCreatePayload) => api.post<PromptDetail>("/prompts", data),
  update: (ref: string, data: Omit<PromptCreatePayload, "name"> & { name?: string }) =>
    api.put<PromptDetail>(`/prompts/${ref}`, data),
  delete: (ref: string) => api.del<{ ok: boolean }>(`/prompts/${ref}`),
  clone: (ref: string, name?: string) => api.post<PromptDetail>(`/prompts/${ref}/clone`, name ? { name } : {}),
  flow: (ref: string, action: PromptFlowAction) => api.post<PromptDetail>(`/prompts/${ref}/flow`, action),
  favourite: (ref: string) => api.post<{ is_favourite: boolean }>(`/prompts/${ref}/favourite`),
  governance: (ref: string) =>
    api.get<{ prompt_id: string; approved: boolean; violations: unknown[]; decisions: unknown[] }>(
      `/prompts/${ref}/governance`,
    ),
  versions: (ref: string) => api.get<VersionOut[]>(`/prompts/${ref}/versions`),
};

export const assistantApi = {
  invoke: (mode: AssistantMode, data: AssistantRequest) => api.post<AssistantResponse>(`/assistant/${mode}`, data),
};

export const executionApi = {
  run: (data: ExecutionRequest) => api.post<ExecutionOut>("/executions", data),
  list: (params?: { prompt_id?: number; status?: string; limit?: number; offset?: number }) =>
    api.get<ExecutionListResponse>("/executions" + toQuery(params)),
  get: (id: string) => api.get<ExecutionOut>(`/executions/${id}`),
};

export const workflowsApi = {
  list: () => api.get<WorkflowListResponse>("/workflows"),
  get: (ref: string) => api.get<WorkflowOut>(`/workflows/${ref}`),
  run: (ref: string, data: WorkflowRunRequest) => api.post<WorkflowExecutionOut>(`/workflows/${ref}/run`, data),
  executions: (ref: string) => api.get<{ items: WorkflowExecutionOut[] }>(`/workflows/${ref}/executions`),
};

export const governanceApi = {
  summary: () => api.get<GovernanceSummary>("/governance/summary"),
  policies: () => api.get<PolicyOut[]>("/governance/policies"),
  createPolicy: (data: PolicyIn) => api.post<PolicyOut>("/governance/policies", data),
  evaluate: (data: GovernanceEvaluationIn) => api.post<GovernanceEvaluationOut>("/governance/evaluate", data),
  violations: () =>
    api.get<{ items: Array<{ id: number; violation_id: string; policy_id: string; message: string; severity: string; created_at: string | null }> }>(
      "/governance/violations",
    ),
  scan: (text: string) =>
    api.post<{ findings: Array<{ severity: string; category: string; detail: string }>; safe: boolean }>(
      "/governance/scan" + query({ text }),
    ),
};

export const analyticsApi = {
  overview: () => api.get<AnalyticsOverview>("/analytics/overview"),
  productivity: () => api.get<{ items: unknown[] }>("/analytics/productivity"),
};

export const auditApi = {
  list: (params?: { event_type?: string; entity_type?: string; entity_ref?: string; actor?: string; limit?: number; offset?: number }) =>
    api.get<AuditListResponse>("/audit" + toQuery(params)),
  recent: (limit = 25) => api.get<{ items: AuditEventOut[] }>(`/audit/recent?limit=${limit}`),
};

export const knowledgeApi = {
  documents: () => api.get<{ items: KnowledgeDocumentLike[] }>("/knowledge/documents"),
};

export type KnowledgeDocumentLike = {
  id: number;
  doc_id: string;
  name: string;
  doc_type: string;
  source_app: string;
  department: string;
  author: string;
  summary: string;
};

export const adminApi = {
  users: () => api.get<UserSummary[]>("/admin/users"),
  create: (data: UserCreatePayload) => api.post<UserSummary>("/admin/users", data),
  update: (id: number, data: UserUpdatePayload) => api.put<UserSummary>(`/admin/users/${id}`, data),
  remove: (id: number) => api.del<{ ok: boolean }>(`/admin/users/${id}`),
};

function toQuery(params?: Record<string, string | number | boolean | undefined>): string {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params || {})) {
    if (v !== undefined && v !== "" && v !== null) qs.set(k, String(v));
  }
  const s = qs.toString();
  return s ? `?${s}` : "";
}

const query = (params?: Record<string, string>): string => toQuery(params);