import type { Execution, Project, Task, TaskMessage, Team, Template, TeamTemplatePayload, ApiKey, ApiKeyCreatePayload, ApiKeyUpdatePayload, ApiKeyValidatePayload, ApiKeyValidateResponse, ProviderInfoResponse, ReviewResult, ProjectFile, AuthResponse } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";

let refreshLock: Promise<boolean> | null = null;

export async function refreshAccessToken(): Promise<boolean> {
  if (refreshLock) return refreshLock;
  refreshLock = _doRefresh();
  try {
    return await refreshLock;
  } finally {
    refreshLock = null;
  }
}

async function _doRefresh(): Promise<boolean> {
  try {
    const refreshToken = typeof window !== "undefined" ? localStorage.getItem("agentforge_refresh_token") : null;
    const body = refreshToken ? JSON.stringify({ refresh_token: refreshToken }) : undefined;
    const res = await fetch(`${BASE}/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body,
    });
    if (!res.ok) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("agentforge_user");
        localStorage.removeItem("agentforge_token");
        localStorage.removeItem("agentforge_refresh_token");
        if (window.location.pathname !== "/login" && window.location.pathname !== "/register") {
          window.location.href = "/login";
        }
      }
      return false;
    }
    const data = await res.json();
    if (typeof window !== "undefined") {
      if (data.token) {
        localStorage.setItem("agentforge_token", data.token);
      }
      if (data.refresh_token) {
        localStorage.setItem("agentforge_refresh_token", data.refresh_token);
      }
    }
    return true;
  } catch {
    return false;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);

  const token = typeof window !== "undefined" ? localStorage.getItem("agentforge_token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    ...(typeof crypto !== "undefined" ? { "X-Request-ID": crypto.randomUUID() } : {}),
  };

  try {
    let res = await fetch(`${BASE}${path}`, {
      ...init,
      credentials: "include",
      signal: controller.signal,
      headers: { ...headers, ...(init?.headers as Record<string, string>) },
    });

    if (res.status === 401 && !path.startsWith("/auth/")) {
      const ok = await refreshAccessToken();
      if (ok) {
        const newToken = typeof window !== "undefined" ? localStorage.getItem("agentforge_token") : null;
        const newHeaders = {
          ...headers,
          ...(newToken ? { "Authorization": `Bearer ${newToken}` } : {}),
          ...(init?.headers as Record<string, string>),
        };
        res = await fetch(`${BASE}${path}`, {
          ...init,
          credentials: "include",
          signal: controller.signal,
          headers: newHeaders,
        });
      }
    }

    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail ?? `Request failed: ${res.status}`);
    }
    if (res.status === 204) return undefined as T;
    const data = await res.json();
    if (typeof window !== "undefined" && (path === "/auth/login" || path === "/auth/register")) {
      if (data.token) {
        localStorage.setItem("agentforge_token", data.token);
      }
      if (data.refresh_token) {
        localStorage.setItem("agentforge_refresh_token", data.refresh_token);
      }
    }
    return data as T;
  } finally {
    clearTimeout(timeout);
  }
}


export const api = {
  get<T>(path: string): Promise<T> {
    return request<T>(path);
  },
  post<T>(path: string, body: unknown): Promise<T> {
    return request<T>(path, { method: "POST", body: JSON.stringify(body) });
  },
  put<T>(path: string, body: unknown): Promise<T> {
    return request<T>(path, { method: "PUT", body: JSON.stringify(body) });
  },
  del(path: string): Promise<void> {
    return request<void>(path, { method: "DELETE" });
  },
};

// Teams
export function listTeams(): Promise<Team[]> {
  return api.get("/teams");
}

export function getTeam(id: string): Promise<Team> {
  return api.get(`/teams/${id}`);
}

export function createTeam(data: { name: string; description?: string }): Promise<Team> {
  return api.post("/teams", data);
}

export function createTeamFromTemplate(data: TeamTemplatePayload): Promise<Team> {
  return api.post("/teams/template", data);
}

export function updateTeam(id: string, data: Partial<Team>): Promise<Team> {
  return api.put(`/teams/${id}`, data);
}

export function deleteTeam(id: string): Promise<void> {
  return api.del(`/teams/${id}`);
}

export function addTeamMember(teamId: string, data: { role: string; model: string }): Promise<Team> {
  return api.post(`/teams/${teamId}/members`, data);
}

export function updateTeamMember(teamId: string, memberId: string, data: { model?: string }): Promise<Team> {
  return api.put(`/teams/${teamId}/members/${memberId}`, data);
}

export function removeTeamMember(teamId: string, memberId: string): Promise<void> {
  return api.del(`/teams/${teamId}/members/${memberId}`);
}

// Tasks
export function listTasks(params?: { project_id?: string; team_id?: string }): Promise<Task[]> {
  const query = new URLSearchParams();
  if (params?.project_id) query.set("project_id", params.project_id);
  if (params?.team_id) query.set("team_id", params.team_id);
  const qs = query.toString();
  return api.get(`/tasks${qs ? `?${qs}` : ""}`);
}

export function getTask(id: string): Promise<Task> {
  return api.get(`/tasks/${id}`);
}

export function createTask(data: { team_id: string; title: string; description: string; project_id?: string }): Promise<Task> {
  const body: Record<string, string> = { team_id: data.team_id, title: data.title, description: data.description };
  return api.post("/tasks", body);
}

export function getTaskMessages(taskId: string): Promise<TaskMessage[]> {
  return api.get(`/tasks/${taskId}/messages`);
}

// Executions
export function getExecution(taskId: string): Promise<Execution> {
  return api.get(`/executions/${taskId}`);
}

export function getExecutionById(execId: string): Promise<Execution> {
  return api.get(`/executions/detail/${execId}`);
}

export function listExecutions(params?: { project_id?: string }): Promise<Execution[]> {
  const query = new URLSearchParams();
  if (params?.project_id) query.set("project_id", params.project_id);
  const qs = query.toString();
  return api.get(`/executions${qs ? `?${qs}` : ""}`);
}

// Projects
export async function listProjects(): Promise<Project[]> {
  return api.get("/projects");
}

export async function getProject(id: string): Promise<Project> {
  return api.get(`/projects/${id}`);
}

export async function createProject(data: { name: string; description?: string }): Promise<Project> {
  return api.post("/projects", data);
}

export async function updateProject(id: string, data: { name?: string; description?: string }): Promise<Project> {
  return api.put(`/projects/${id}`, data);
}

export async function deleteProject(id: string): Promise<void> {
  return api.del(`/projects/${id}`);
}

export async function assignTeamToProject(projectId: string, teamId: string): Promise<void> {
  return api.post(`/projects/${projectId}/teams`, { team_id: teamId });
}

export async function removeTeamFromProject(projectId: string, teamId: string): Promise<void> {
  return api.del(`/projects/${projectId}/teams/${teamId}`);
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
      credentials: "include",
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
      credentials: "include",
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
  return api.get(`/projects/${projectId}/files${query}`);
}

export async function getProjectFile(projectId: string, fileId: string): Promise<ProjectFile> {
  return api.get(`/projects/${projectId}/files/${fileId}`);
}

export async function deleteProjectFile(projectId: string, fileId: string): Promise<void> {
  return api.del(`/projects/${projectId}/files/${fileId}`);
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
  return api.post(`/projects/${projectId}/context/parse/${fileId}`, {});
}

export function parseAllFileContexts(projectId: string): Promise<{ total: number; results: { file_id: string; filename: string; language: string; symbols: number; imports: number; status: string }[] }> {
  return api.post(`/projects/${projectId}/context/parse-all`, {});
}

export function getContextSummary(projectId: string): Promise<ContextSummaryItem[]> {
  return api.get(`/projects/${projectId}/context/summary`);
}

export function listContextSymbols(projectId: string, params?: { file_id?: string; symbol_type?: string; search?: string }): Promise<CodeSymbolItem[]> {
  const query = new URLSearchParams();
  if (params?.file_id) query.set("file_id", params.file_id);
  if (params?.symbol_type) query.set("symbol_type", params.symbol_type);
  if (params?.search) query.set("search", params.search);
  const qs = query.toString();
  return api.get(`/projects/${projectId}/context/symbols${qs ? `?${qs}` : ""}`);
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
  return api.get(`/projects/${projectId}/context/file/${fileId}`);
}

export function deleteFileContext(projectId: string, fileId: string): Promise<void> {
  return api.del(`/projects/${projectId}/context/file/${fileId}`);
}

// Templates (not yet implemented on backend â€” returns empty for now)
export async function listTemplates(): Promise<Template[]> {
  try {
    return await api.get("/templates");
  } catch {
    return [];
  }
}

export async function getTemplate(id: string): Promise<Template> {
  try {
    return await api.get(`/templates/${id}`);
  } catch {
    throw new Error("Templates API not available");
  }
}

// API Keys (BYOK)
export function listApiKeys(): Promise<ApiKey[]> {
  return api.get("/keys");
}

export function getApiKey(id: string): Promise<ApiKey> {
  return api.get(`/keys/${id}`);
}

export function createApiKey(data: ApiKeyCreatePayload): Promise<ApiKey> {
  return api.post("/keys", data);
}

export function updateApiKey(id: string, data: ApiKeyUpdatePayload): Promise<ApiKey> {
  return api.put(`/keys/${id}`, data);
}

export function deleteApiKey(id: string): Promise<void> {
  return api.del(`/keys/${id}`);
}

export function validateApiKey(data: ApiKeyValidatePayload): Promise<ApiKeyValidateResponse> {
  return api.post("/keys/validate", data);
}

export function listProviderInfo(): Promise<ProviderInfoResponse> {
  return api.get("/keys/providers");
}

// Quick Review
export function submitReview(data: { code: string; language?: string }): Promise<ReviewResult> {
  return api.post("/review", data);
}

export function getReview(id: string): Promise<ReviewResult> {
  return api.get(`/review/${id}`);
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
  return api.post("/auth/login", { email, password });
}

export function registerUser(name: string, email: string, password: string): Promise<AuthResponse> {
  return api.post("/auth/register", { name, email, password });
}

export async function logoutUser(): Promise<void> {
  const refreshToken = typeof window !== "undefined" ? localStorage.getItem("agentforge_refresh_token") : null;
  const body = refreshToken ? { refresh_token: refreshToken } : {};
  try {
    await api.post("/auth/logout", body);
  } finally {
    if (typeof window !== "undefined") {
      localStorage.removeItem("agentforge_token");
      localStorage.removeItem("agentforge_refresh_token");
      localStorage.removeItem("agentforge_user");
    }
  }
}

export function getMe(): Promise<{ id: string; email: string; name: string }> {
  return api.get("/auth/me");
}


export function getAnalyticsDashboard(): Promise<AnalyticsDashboard> {
  return api.get("/analytics/dashboard");
}

export function getAnalyticsTrends(days?: number): Promise<{ executions: AnalyticsTrend[]; tasks_created: { date: string; count: number }[] }> {
  const qs = days ? `?days=${days}` : "";
  return api.get(`/analytics/trends${qs}`);
}

export function getModelUsage(): Promise<ModelUsage[]> {
  return api.get("/analytics/models");
}

export function getTeamPerformance(): Promise<TeamPerformance[]> {
  return api.get("/analytics/teams");
}

export function trackAnalyticsEvent(data: Record<string, unknown>): Promise<{ id: string; status: string }> {
  return api.post("/analytics/track", data);
}

export function exportAnalytics(): Promise<Record<string, unknown>> {
  return api.get("/analytics/export");
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
  return api.get(`/memories${qs ? `?${qs}` : ""}`);
}

export function getRelevantMemories(context: string, params?: { project_id?: string; team_id?: string; limit?: number }): Promise<MemoryItem[]> {
  const query = new URLSearchParams({ context });
  if (params?.project_id) query.set("project_id", params.project_id);
  if (params?.team_id) query.set("team_id", params.team_id);
  if (params?.limit) query.set("limit", String(params.limit));
  return api.get(`/memories/relevant?${query.toString()}`);
}

export function getMemory(id: string): Promise<MemoryItem> {
  return api.get(`/memories/${id}`);
}

export function createMemory(data: { key: string; content: string; memory_type?: string; importance?: number; tags?: string[]; project_id?: string; team_id?: string; task_id?: string; source?: string; metadata?: Record<string, unknown> }): Promise<{ id: string; status: string }> {
  return api.post("/memories", data);
}

export function updateMemory(id: string, data: { content?: string; importance?: number; tags?: string[] }): Promise<{ status: string }> {
  return api.put(`/memories/${id}`, data);
}

export function deleteMemory(id: string): Promise<void> {
  return api.del(`/memories/${id}`);
}
