import type { Execution, Project, Task, TaskMessage, Team, Template, TeamTemplatePayload, ApiKey, ApiKeyCreatePayload, ApiKeyUpdatePayload, ApiKeyValidatePayload, ApiKeyValidateResponse, ProviderInfoResponse, ReviewResult, ProjectFile, AuthResponse } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("agentforge_token");
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = typeof window !== "undefined" ? localStorage.getItem("agentforge_refresh") : null;
  if (!refresh) return null;
  try {
    const res = await fetch(`${BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    localStorage.setItem("agentforge_token", data.token);
    localStorage.setItem("agentforge_refresh", data.refresh_token);
    return data.token;
  } catch {
    return null;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);

  const attachToken = (headers: Record<string, string> = {}): Record<string, string> => {
    const token = getToken();
    if (token && !path.startsWith("/auth/")) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  };

  const doFetch = (headers: Record<string, string>) =>
    fetch(`${BASE}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...headers,
        ...(init?.headers as Record<string, string>),
      },
    });

  try {
    let headers = attachToken();
    let res = await doFetch(headers);

    if (res.status === 401 && !path.startsWith("/auth/")) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        headers = attachToken();
        res = await doFetch(headers);
      }
    }

    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail ?? `Request failed: ${res.status}`);
    }
    if (res.status === 204) return undefined as T;
    return res.json() as Promise<T>;
  } finally {
    clearTimeout(timeout);
  }
}

// Teams
export function listTeams(): Promise<Team[]> {
  return request("/teams");
}

export function getTeam(id: string): Promise<Team> {
  return request(`/teams/${id}`);
}

export function createTeam(data: { name: string; description?: string }): Promise<Team> {
  return request("/teams", { method: "POST", body: JSON.stringify(data) });
}

export function createTeamFromTemplate(data: TeamTemplatePayload): Promise<Team> {
  return request("/teams/template", { method: "POST", body: JSON.stringify(data) });
}

export function updateTeam(id: string, data: Partial<Team>): Promise<Team> {
  return request(`/teams/${id}`, { method: "PUT", body: JSON.stringify(data) });
}

export function deleteTeam(id: string): Promise<void> {
  return request(`/teams/${id}`, { method: "DELETE" });
}

export function addTeamMember(teamId: string, data: { role: string; model: string }): Promise<Team> {
  return request(`/teams/${teamId}/members`, { method: "POST", body: JSON.stringify(data) });
}

export function updateTeamMember(teamId: string, memberId: string, data: { model?: string }): Promise<Team> {
  return request(`/teams/${teamId}/members/${memberId}`, { method: "PUT", body: JSON.stringify(data) });
}

export function removeTeamMember(teamId: string, memberId: string): Promise<void> {
  return request(`/teams/${teamId}/members/${memberId}`, { method: "DELETE" });
}

// Tasks
export function listTasks(params?: { project_id?: string; team_id?: string }): Promise<Task[]> {
  const query = new URLSearchParams();
  if (params?.project_id) query.set("project_id", params.project_id);
  if (params?.team_id) query.set("team_id", params.team_id);
  const qs = query.toString();
  return request(`/tasks${qs ? `?${qs}` : ""}`);
}

export function getTask(id: string): Promise<Task> {
  return request(`/tasks/${id}`);
}

export function createTask(data: { team_id: string; title: string; description: string; project_id?: string }): Promise<Task> {
  const { project_id, ...body } = data;
  return request("/tasks", { method: "POST", body: JSON.stringify(body) });
}

export function getTaskMessages(taskId: string): Promise<TaskMessage[]> {
  return request(`/tasks/${taskId}/messages`);
}

// Executions
export function getExecution(taskId: string): Promise<Execution> {
  return request(`/executions/${taskId}`);
}

export function getExecutionById(execId: string): Promise<Execution> {
  return request(`/executions/detail/${execId}`);
}

export function listExecutions(params?: { project_id?: string }): Promise<Execution[]> {
  const query = new URLSearchParams();
  if (params?.project_id) query.set("project_id", params.project_id);
  const qs = query.toString();
  return request(`/executions${qs ? `?${qs}` : ""}`);
}

// Projects
export async function listProjects(): Promise<Project[]> {
  return request("/projects");
}

export async function getProject(id: string): Promise<Project> {
  return request(`/projects/${id}`);
}

export async function createProject(data: { name: string; description?: string }): Promise<Project> {
  return request("/projects", { method: "POST", body: JSON.stringify(data) });
}

export async function updateProject(id: string, data: { name?: string; description?: string }): Promise<Project> {
  return request(`/projects/${id}`, { method: "PUT", body: JSON.stringify(data) });
}

export async function deleteProject(id: string): Promise<void> {
  return request(`/projects/${id}`, { method: "DELETE" });
}

export async function assignTeamToProject(projectId: string, teamId: string): Promise<void> {
  return request(`/projects/${projectId}/teams`, { method: "POST", body: JSON.stringify({ team_id: teamId }) });
}

export async function removeTeamFromProject(projectId: string, teamId: string): Promise<void> {
  return request(`/projects/${projectId}/teams/${teamId}`, { method: "DELETE" });
}

// Project Files
export async function uploadFile(projectId: string, file: File, parentId?: string): Promise<ProjectFile> {
  const formData = new FormData();
  formData.append("file", file);
  if (parentId) formData.append("parent_id", parentId);

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60000);
  try {
    const res = await fetch(`${BASE}/projects/${projectId}/upload`, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail ?? `Upload failed: ${res.status}`);
    }
    return res.json();
  } finally {
    clearTimeout(timeout);
  }
}

export async function uploadZip(projectId: string, file: File): Promise<{ status: string; files_extracted: number; files: { id: string; path: string }[] }> {
  const formData = new FormData();
  formData.append("file", file);

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 120000);
  try {
    const res = await fetch(`${BASE}/projects/${projectId}/upload/zip`, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail ?? `Upload failed: ${res.status}`);
    }
    return res.json();
  } finally {
    clearTimeout(timeout);
  }
}

export async function listProjectFiles(projectId: string, parentId?: string): Promise<ProjectFile[]> {
  const query = parentId ? `?parent_id=${parentId}` : "";
  return request(`/projects/${projectId}/files${query}`);
}

export async function getProjectFile(projectId: string, fileId: string): Promise<ProjectFile> {
  return request(`/projects/${projectId}/files/${fileId}`);
}

export async function deleteProjectFile(projectId: string, fileId: string): Promise<void> {
  return request(`/projects/${projectId}/files/${fileId}`, { method: "DELETE" });
}

export function getFileDownloadUrl(projectId: string, fileId: string): string {
  return `${BASE}/projects/${projectId}/files/${fileId}/download`;
}

// Repository Context
export interface ContextSummaryItem {
  file_id: string;
  filename: string;
  file_path: string;
  language: string;
  parsed_at: string | null;
  error_message: string | null;
  symbol_count: number;
  import_count: number;
  chunk_count: number;
}

export interface CodeSymbolItem {
  id: string;
  symbol_type: string;
  name: string;
  line_start: number;
  line_end: number;
  signature: string;
  docstring: string;
  visibility: string;
  filename: string;
  filepath: string;
}

export interface CodeImportItem {
  source: string;
  alias: string;
  is_relative: boolean;
  line_number: number;
  filename: string;
}

export interface CodeChunkItem {
  id: string;
  chunk_type: string;
  name: string;
  content: string;
  line_start: number;
  line_end: number;
  tokens_estimate: number;
  filename: string;
}

export function parseFileContext(projectId: string, fileId: string): Promise<{ status: string; context_id: string; language: string; symbols: number; imports: number; chunks: number }> {
  return request(`/projects/${projectId}/context/parse/${fileId}`, { method: "POST" });
}

export function parseAllFileContexts(projectId: string): Promise<{ total: number; results: { file_id: string; filename: string; language: string; symbols: number; imports: number; status: string }[] }> {
  return request(`/projects/${projectId}/context/parse-all`, { method: "POST" });
}

export function getContextSummary(projectId: string): Promise<ContextSummaryItem[]> {
  return request(`/projects/${projectId}/context/summary`);
}

export function listContextSymbols(projectId: string, params?: { file_id?: string; symbol_type?: string; search?: string }): Promise<CodeSymbolItem[]> {
  const query = new URLSearchParams();
  if (params?.file_id) query.set("file_id", params.file_id);
  if (params?.symbol_type) query.set("symbol_type", params.symbol_type);
  if (params?.search) query.set("search", params.search);
  const qs = query.toString();
  return request(`/projects/${projectId}/context/symbols${qs ? `?${qs}` : ""}`);
}

export function getFileContext(projectId: string, fileId: string): Promise<{
  context_id: string;
  language: string;
  parsed_at: string | null;
  error_message: string | null;
  symbols: { id: string; symbol_type: string; name: string; line_start: number; line_end: number; signature: string; docstring: string; visibility: string }[];
  imports: { id: string; source: string; alias: string; is_relative: boolean; line_number: number }[];
  chunks: CodeChunkItem[];
}> {
  return request(`/projects/${projectId}/context/file/${fileId}`);
}

export function deleteFileContext(projectId: string, fileId: string): Promise<void> {
  return request(`/projects/${projectId}/context/file/${fileId}`, { method: "DELETE" });
}

// Templates (not yet implemented on backend — returns empty for now)
export async function listTemplates(): Promise<Template[]> {
  try {
    return await request("/templates");
  } catch {
    return [];
  }
}

export async function getTemplate(id: string): Promise<Template> {
  try {
    return await request(`/templates/${id}`);
  } catch {
    throw new Error("Templates API not available");
  }
}

// API Keys (BYOK)
export function listApiKeys(): Promise<ApiKey[]> {
  return request("/keys");
}

export function getApiKey(id: string): Promise<ApiKey> {
  return request(`/keys/${id}`);
}

export function createApiKey(data: ApiKeyCreatePayload): Promise<ApiKey> {
  return request("/keys", { method: "POST", body: JSON.stringify(data) });
}

export function updateApiKey(id: string, data: ApiKeyUpdatePayload): Promise<ApiKey> {
  return request(`/keys/${id}`, { method: "PUT", body: JSON.stringify(data) });
}

export function deleteApiKey(id: string): Promise<void> {
  return request(`/keys/${id}`, { method: "DELETE" });
}

export function validateApiKey(data: ApiKeyValidatePayload): Promise<ApiKeyValidateResponse> {
  return request("/keys/validate", { method: "POST", body: JSON.stringify(data) });
}

export function listProviderInfo(): Promise<ProviderInfoResponse> {
  return request("/keys/providers");
}

// Quick Review
export function submitReview(data: { code: string; language?: string }): Promise<ReviewResult> {
  return request("/review", { method: "POST", body: JSON.stringify(data) });
}

export function getReview(id: string): Promise<ReviewResult> {
  return request(`/review/${id}`);
}

export async function pollReview(
  id: string,
  onProgress?: (status: string) => void,
  pollIntervalMs = 2000,
  maxDurationMs = 120000,
): Promise<ReviewResult> {
  const deadline = Date.now() + maxDurationMs;
  while (Date.now() < deadline) {
    const result = await getReview(id);
    onProgress?.(result.status);
    if (result.status === "completed" || result.status === "failed") {
      return result;
    }
    await new Promise((r) => setTimeout(r, pollIntervalMs));
  }
  throw new Error("Review timed out");
}

// Analytics
export interface AnalyticsDashboard {
  projects: number;
  teams: number;
  tasks: { total: number; [status: string]: number };
  executions: { total: number; completed: number; failed: number; success_rate: number; avg_duration_ms: number };
  tokens: { total: number };
  files: number;
  api_keys: number;
}

export interface AnalyticsTrend {
  date: string;
  total: number;
  completed: number;
  failed: number;
  avg_duration_ms: number;
  tokens: number;
}

export interface ModelUsage {
  model: string;
  total: number;
  completed: number;
  failed: number;
  avg_duration_ms: number;
  tokens: number;
}

export interface TeamPerformance {
  id: string;
  name: string;
  total_execs: number;
  completed: number;
  failed: number;
  avg_duration_ms: number;
  tokens: number;
}

// Auth
export function loginUser(email: string, password: string): Promise<AuthResponse> {
  return request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
}

export function registerUser(name: string, email: string, password: string): Promise<AuthResponse> {
  return request("/auth/register", { method: "POST", body: JSON.stringify({ name, email, password }) });
}

export function getAnalyticsDashboard(): Promise<AnalyticsDashboard> {
  return request("/analytics/dashboard");
}

export function getAnalyticsTrends(days?: number): Promise<{ executions: AnalyticsTrend[]; tasks_created: { date: string; count: number }[] }> {
  const qs = days ? `?days=${days}` : "";
  return request(`/analytics/trends${qs}`);
}

export function getModelUsage(): Promise<ModelUsage[]> {
  return request("/analytics/models");
}

export function getTeamPerformance(): Promise<TeamPerformance[]> {
  return request("/analytics/teams");
}

export function trackAnalyticsEvent(data: Record<string, unknown>): Promise<{ id: string; status: string }> {
  return request("/analytics/track", { method: "POST", body: JSON.stringify(data) });
}

export function exportAnalytics(): Promise<Record<string, unknown>> {
  return request("/analytics/export");
}

// Memories
export interface MemoryItem {
  id: string;
  user_id: string;
  project_id: string | null;
  team_id: string | null;
  task_id: string | null;
  key: string;
  content: string;
  memory_type: string;
  importance: number;
  tags: string[];
  source: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export function listMemories(params?: {
  project_id?: string;
  team_id?: string;
  memory_type?: string;
  search?: string;
  tags?: string;
  min_importance?: number;
  limit?: number;
  offset?: number;
}): Promise<MemoryItem[]> {
  const query = new URLSearchParams();
  if (params?.project_id) query.set("project_id", params.project_id);
  if (params?.team_id) query.set("team_id", params.team_id);
  if (params?.memory_type) query.set("memory_type", params.memory_type);
  if (params?.search) query.set("search", params.search);
  if (params?.tags) query.set("tags", params.tags);
  if (params?.min_importance != null) query.set("min_importance", String(params.min_importance));
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));
  const qs = query.toString();
  return request(`/memories${qs ? `?${qs}` : ""}`);
}

export function getRelevantMemories(context: string, params?: { project_id?: string; team_id?: string; limit?: number }): Promise<MemoryItem[]> {
  const query = new URLSearchParams({ context });
  if (params?.project_id) query.set("project_id", params.project_id);
  if (params?.team_id) query.set("team_id", params.team_id);
  if (params?.limit) query.set("limit", String(params.limit));
  return request(`/memories/relevant?${query.toString()}`);
}

export function getMemory(id: string): Promise<MemoryItem> {
  return request(`/memories/${id}`);
}

export function createMemory(data: { key: string; content: string; memory_type?: string; importance?: number; tags?: string[]; project_id?: string; team_id?: string; task_id?: string; source?: string; metadata?: Record<string, unknown> }): Promise<{ id: string; status: string }> {
  return request("/memories", { method: "POST", body: JSON.stringify(data) });
}

export function updateMemory(id: string, data: { content?: string; importance?: number; tags?: string[] }): Promise<{ status: string }> {
  return request(`/memories/${id}`, { method: "PUT", body: JSON.stringify(data) });
}

export function deleteMemory(id: string): Promise<void> {
  return request(`/memories/${id}`, { method: "DELETE" });
}
