/**
 * API Types
 * Generated from API_SCHEMA_MAP.md - defines request/response types for all API endpoints
 */

import type { AgentRole, MessageType, TaskStatus, ProviderName } from "@/lib/constants";

// Task types
export interface TaskCreateRequest {
  team_id: string;
  title: string; // max 200 chars
  description: string; // max 10000 chars
  project_id?: string | null;
}

export interface TaskResponse {
  id: string;
  team_id: string;
  title: string;
  description: string;
  status: TaskStatus;
  created_by: string;
  created_at: string; // ISO date string
  updated_at: string; // ISO date string
  completed_at: string | null;
  error_message: string | null;
  project_id: string | null;
}

export interface TaskMessageResponse {
  id: string;
  task_id: string;
  step_order: number;
  role: AgentRole;
  model: string;
  message_type: MessageType;
  content: string;
  created_at: string; // ISO date string
}

// Team types
export interface TeamCreate {
  name: string; // max 255 chars
  description: string | null; // max 2000 chars
}

export interface TeamResponse {
  id: string;
  name: string;
  description: string | null;
  created_by: string;
  created_at: string; // ISO date string
  updated_at: string; // ISO date string
  members: TeamMemberResponse[];
}

export interface TeamMemberCreate {
  role: AgentRole;
  model: string; // min 1, max 100 chars
}

export interface TeamMemberResponse {
  id: string;
  team_id: string;
  role: AgentRole;
  model: string;
  instructions: string;
  created_at: string; // ISO date string
}

// Project types
export interface ProjectCreate {
  name: string; // max 255 chars
  description: string | null; // max 2000 chars
}

export interface ProjectResponse {
  id: string;
  name: string;
  description: string | null;
  created_by: string;
  created_at: string; // ISO date string
  updated_at: string; // ISO date string
  team_ids: string[];
}

export interface ProjectTeamAssign {
  team_id: string;
}

// File types
export interface FileResponse {
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
  created_at: string; // ISO date string
  updated_at: string; // ISO date string
}

// API Key types
export interface ApiKeyCreate {
  provider: ProviderName;
  key: string; // min_length=1
}

export interface ApiKeyResponse {
  id: string;
  provider: ProviderName;
  key_preview: string;
  is_enabled: boolean;
  is_default: boolean;
  created_at: string; // ISO date string
  updated_at: string; // ISO date string
}

export interface ApiKeyValidateRequest {
  provider: ProviderName;
  key: string; // min_length=1
}

export interface ApiKeyValidateResponse {
  valid: boolean;
  provider: ProviderName;
  message: string;
  format_valid: boolean;
  live_valid: boolean | null;
}

export interface ProviderInfoResponse {
  providers: Record<string, {
    label: string;
  }>;
}

// Review types
export interface ReviewRequest {
  code: string; // min_length=1
  language: string | null;
}

export interface ReviewResponse {
  review_id: string;
  status: string;
}

// Auth types
export interface LoginRequest {
  email: string; // min_length=1, max_length=255
  password: string; // min_length=8, max_length=128
}

export interface RegisterRequest {
  email: string; // min_length=1, max_length=255
  password: string; // min_length=8, max_length=128
  name: string; // min_length=1, max_length=255
}

export interface AuthResponse {
  token: string;
  refresh_token: string;
  user_id: string;
  email: string;
  name: string;
}

export interface RefreshRequest {
  refresh_token: string; // min_length=1
}

export interface RefreshResponse {
  token: string;
  refresh_token: string;
}

export interface LogoutRequest {
  refresh_token: string; // min_length=1
}

// Feedback types
export interface FeedbackCreate {
  title: string; // min_length=1, max_length=500
  decision: "accepted" | "rejected";
  severity: string; // defaults to "medium"
  file: string | null;
  project_id: string | null;
  task_id: string | null;
}

// Execution types
export interface ExecutionResponse {
  id: string;
  task_id: string;
  status: string;
  current_node: string | null;
  started_at: string; // ISO date string
  completed_at: string | null;
  error_message: string | null;
}

// Analytics types
export interface UsageDataPoint {
  date: string; // ISO date string
  cost_usd: number;
  tokens: number;
}

export interface UsageStatsResponse {
  total_cost_usd: number;
  total_requests: number;
  by_provider_model: Array<{
    provider: string;
    model: string;
    total: number;
    completed: number;
    failed: number;
    avg_duration_ms: number;
    tokens: number;
  }>;
  daily_data: UsageDataPoint[];
}
