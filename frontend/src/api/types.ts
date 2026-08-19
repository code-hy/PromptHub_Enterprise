export type PromptStatus =
  | "DRAFT"
  | "REVIEW"
  | "PUBLISHED"
  | "APPROVED"
  | "DEPRECATED"
  | "RETIRED";

export type Catalog = {
  business_functions: string[];
  tasks: string[];
  applications: string[];
  statuses: string[];
  classifications: string[];
  risk_levels: string[];
  input_types: string[];
  audiences: string[];
  tones: string[];
  output_formats: string[];
  event_types: string[];
  roles: string[];
  models: Array<Record<string, string>>;
  providers: Array<Record<string, string>>;
};

export type PromptInputOut = {
  id: number;
  name: string;
  input_type: string;
  required: boolean;
  description: string;
  sample_value: string;
  position: number;
};

export type PromptInputIn = {
  name: string;
  input_type?: string;
  required?: boolean;
  description?: string;
  sample_value?: string;
};

export type PromptSummary = {
  id: number;
  prompt_id: string;
  name: string;
  description: string;
  status: PromptStatus;
  version: string;
  business_function: string;
  application: string;
  task: string;
  owner_id: number | null;
  data_classification: string;
  risk_level: string;
  tags: string[];
  rating_avg: number;
  rating_count: number;
  execution_count: number;
  is_favourite: boolean;
};

export type PromptDetail = PromptSummary & {
  goal: string;
  context: string;
  source: string;
  expectations: string;
  system_instruction: string;
  prompt_template: string;
  audience: string;
  tone: string;
  output_format: string;
  max_length: string;
  contains_pii: boolean;
  contains_financial_data: boolean;
  contains_customer_data: boolean;
  external_sharing: string;
  requires_approval: boolean;
  temperature: number;
  require_evidence: boolean;
  avoid_unsupported_claims: boolean;
  ask_clarification_questions: boolean;
  manual_time_minutes: number;
  ai_time_minutes: number;
  quality_score: number;
  inputs: PromptInputOut[];
  owner_name: string;
  created_at: string | null;
  updated_at: string | null;
  published_at: string | null;
};

export type PromptListResponse = {
  items: PromptSummary[];
  total: number;
  page: number;
  page_size: number;
};

export type PromptCreatePayload = {
  name: string;
  description?: string;
  business_function?: string;
  application?: string;
  task?: string;
  goal?: string;
  context?: string;
  source?: string;
  expectations?: string;
  system_instruction?: string;
  prompt_template?: string;
  audience?: string;
  tone?: string;
  output_format?: string;
  max_length?: string;
  data_classification?: string;
  risk_level?: string;
  requires_approval?: boolean;
  contains_pii?: boolean;
  contains_financial_data?: boolean;
  contains_customer_data?: boolean;
  external_sharing?: string;
  temperature?: number;
  require_evidence?: boolean;
  avoid_unsupported_claims?: boolean;
  ask_clarification_questions?: boolean;
  manual_time_minutes?: number;
  ai_time_minutes?: number;
  tags?: string[];
  inputs?: PromptInputIn[];
};

export type PromptFlowAction = {
  action: "publish" | "deprecate" | "retire" | "submit_for_review" | "approve" | "reject";
  note?: string;
};

export type VersionOut = {
  id: number;
  prompt_id: number;
  version: string;
  version_number: number;
  author_id: number | null;
  changes: string;
  approval_status: string;
  created_at: string | null;
};

export type AssistantMode = "analyse" | "improve" | "generate" | "explain";

export type AssistantRequest = {
  prompt: string;
  mode?: AssistantMode;
  business_function?: string;
  task?: string;
};

export type AssistantResponse = {
  score: number;
  rating: string;
  breakdown: Record<string, Record<string, number>>;
  missing: string[];
  present: string[];
  recommendations: string[];
  analysis: Array<Record<string, string>>;
  improved_prompt: string;
  generated_prompt: string;
  explanation: string;
};

export type ExecutionOut = {
  id: number;
  execution_id: string;
  prompt_id: number;
  version: string;
  provider: string;
  model: string;
  status: string;
  input_data: Record<string, string>;
  output: string;
  tokens: number;
  latency_ms: number;
  sources_used: string[];
  evidence: Array<Record<string, string>>;
  eval_metrics: Record<string, number>;
  error_message: string;
  estimated_time_saved_minutes: number;
  created_at: string | null;
};

export type ExecutionRequest = {
  prompt_id: number;
  input_data?: Record<string, string>;
  model_provider?: string | null;
  model_name?: string | null;
  temperature?: number | null;
  document_ids?: number[];
  use_grounding?: boolean;
};

export type ExecutionListResponse = {
  items: ExecutionOut[];
  total: number;
};

export type WorkflowStepOut = {
  id: number;
  step_id: string;
  sequence: number;
  name: string;
  prompt_id: number;
  prompt_name: string;
  input_mapping: Record<string, string>;
  continue_on_failure: boolean;
};

export type WorkflowOut = {
  id: number;
  workflow_id: string;
  name: string;
  description: string;
  status: string;
  business_function: string;
  tags: string[];
  owner_id: number | null;
  steps: WorkflowStepOut[];
  estimated_manual_minutes: number;
  estimated_ai_minutes: number;
  created_at: string | null;
};

export type WorkflowListResponse = {
  items: WorkflowOut[];
  total: number;
};

export type WorkflowRunRequest = {
  input_data?: Record<string, string>;
  document_ids?: number[];
};

export type WorkflowExecutionOut = {
  id: number;
  workflow_id: number;
  execution_id: string;
  workflow_name: string;
  status: string;
  inputs: Record<string, string>;
  step_results: Array<{
    sequence: number;
    step_name: string;
    status: string;
    output: string;
    prompt_name?: string;
    latency_ms?: number;
  }>;
  final_output: string;
  sources_used: string[];
  latency_ms: number;
  error_message: string;
  created_at: string | null;
  ended_at: string | null;
};

export type PolicyOut = {
  id: number;
  policy_id: string;
  name: string;
  description: string;
  condition: Record<string, unknown>;
  action: Record<string, unknown>;
  severity: string;
  enabled: boolean;
};

export type PolicyIn = {
  name: string;
  description?: string;
  condition?: Record<string, unknown>;
  action?: Record<string, unknown>;
  severity?: string;
  enabled?: boolean;
};

export type GovernanceEvaluationIn = {
  data_classification?: string;
  risk_level?: string;
  contains_pii?: boolean;
  contains_financial_data?: boolean;
  contains_customer_data?: boolean;
  external_sharing?: string;
  llm_provider?: string;
};

export type GovernanceEvaluationOut = {
  approved: boolean;
  violations: Array<{ policy: string; rule: string; severity: string; message: string }>;
  decisions: Array<Record<string, string>>;
};

export type GovernanceSummary = {
  total_prompts: number;
  published: number;
  awaiting_approval: number;
  high_risk: number;
  missing_owner: number;
  deprecated: number;
  classifications: Array<Record<string, string | number>>;
  risk_distribution: Array<Record<string, string | number>>;
  violations: Array<Record<string, unknown>>;
};

export type AuditEventOut = {
  id: number;
  event_type: string;
  actor: string;
  entity_type: string;
  entity_ref: string;
  entity_name: string;
  details: Record<string, string>;
  created_at: string | null;
};

export type AuditListResponse = {
  items: AuditEventOut[];
  total: number;
};

export type AnalyticsOverview = {
  prompt_count: number;
  published_count: number;
  execution_count: number;
  success_rate: number;
  avg_rating: number;
  rating_count: number;
  estimated_time_saved_minutes: number;
  avg_latency_ms: number;
  avg_tokens: number;
  top_prompts: Array<{ name: string; count: number }>;
  execution_by_category: Array<{ name: string; count: number }>;
  executions_by_day: Array<{ date: string; count: number }>;
  model_usage: Array<Record<string, string | number>>;
  status_distribution: Array<Record<string, string | number>>;
};

export type KnowledgeDocument = {
  id: number;
  doc_id: string;
  name: string;
  doc_type: string;
  source_app: string;
  department: string;
  author: string;
  summary: string;
};

export type UserSummary = {
  id: number;
  user_id: string;
  username: string;
  display_name: string;
  email: string;
  role: string;
  department: string;
  title: string;
};