import type { AgentRole, AgentStatus, MessageType, TaskStatus, ProviderName } from "./constants";

export interface Team {
  id: string;
  name: string;
  description: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  members: TeamMember[];
  metadata?: Record<string, unknown>;
}

export interface TeamMember {
  id: string;
  team_id: string;
  role: AgentRole;
  model: string;
  instructions?: string;
  provider?: string;
  status?: AgentStatus;
  current_task?: string;
  tokens_used?: number;
  last_action?: string;
  created_at: string;
}

export interface Task {
  id: string;
  team_id: string;
  title: string;
  description: string;
  status: TaskStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  error_message: string | null;
  project_id?: string;
  metadata?: Record<string, unknown>;
}

export interface TaskMessage {
  id: string;
  task_id: string;
  step_order: number;
  role: AgentRole;
  model: string;
  message_type: MessageType;
  content: string;
  created_at: string;
  tokens?: number;
  metadata?: Record<string, unknown>;
}

export interface Execution {
  id: string;
  task_id: string;
  status: string;
  current_node: string | null;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
  steps?: ExecutionStep[];
  total_tokens?: number;
  total_files?: number;
}

export interface ExecutionStep {
  node: string;
  agent: AgentRole;
  status: "pending" | "active" | "completed" | "failed";
  started_at: string | null;
  completed_at: string | null;
  tokens?: number;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  team_ids: string[];
  metadata?: Record<string, unknown>;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  roles: { role: AgentRole; model: string; provider?: string }[];
  metadata?: Record<string, unknown>;
}

export interface TeamTemplatePayloadMember {
  role: AgentRole;
  model: string;
  instructions: string;
}

export interface TeamTemplatePayload {
  name: string;
  description: string | null;
  use_case: string;
  members: TeamTemplatePayloadMember[];
}

export interface ApiKey {
  id: string;
  provider: ProviderName;
  key_preview: string;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApiKeyCreatePayload {
  provider: ProviderName;
  key: string;
}

export interface ApiKeyUpdatePayload {
  key?: string;
  is_enabled?: boolean;
}

export interface ApiKeyValidatePayload {
  provider: ProviderName;
  key: string;
}

export interface ApiKeyValidateResponse {
  valid: boolean;
  provider: ProviderName;
  message: string;
  format_valid: boolean;
  live_valid: boolean | null;
}

export interface ProviderInfoResponse {
  providers: Record<string, { label: string }>;
}

export interface ReviewIssue {
  severity: string;
  title: string;
  line: number | null;
  description: string;
  suggestion: string;
}

export interface ReviewComparison {
  baseline_issues: ReviewIssue[];
  bugs_single_would_miss: number;
  summary: string;
  categories?: {
    bugs_caught: number;
    security_issues: number;
    tests_generated: number;
    performance_issues: number;
    style_issues: number;
  };
  chatgpt_would_miss?: {
    bugs: number;
    security: number;
    tests: number;
  };
}

export interface ProjectFile {
  id: string;
  project_id: string;
  parent_id: string | null;
  filename: string;
  filepath: string;
  mime_type: string;
  size_bytes: number;
  is_directory: boolean;
  file_hash: string | null;
  status: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export type ReviewStatus = "queued" | "analyzing" | "reviewing" | "completed" | "failed";

export interface ReviewResult {
  review_id: string;
  status: ReviewStatus;
  issues: ReviewIssue[];
  summary: string;
  comparison: ReviewComparison | null;
  duration_ms: number;
  error: string | null;
}

export interface ReviewRecord {
  review_id: string;
  code: string;
  language: string;
  issues: number;
  summary: string;
  timestamp: number;
}

// Auth
export interface AuthResponse {
  token: string;
  refresh_token: string;
  user_id: string;
  email: string;
  name: string;
}
