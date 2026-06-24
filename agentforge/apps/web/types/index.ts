export interface Agent {
  id: string;
  name: string;
  slug: string;
  description?: string;
  llm_config: {
    provider: string;
    model: string;
    temperature: number;
    max_tokens: number;
  };
  system_prompt?: string;
  tools: string[];
  memory_config: {
    type: "none" | "short_term" | "long_term";
    turns?: number;
  };
  version: number;
  status: "draft" | "active" | "archived";
  created_at: string;
  updated_at: string;
}

export interface Workflow {
  id: string;
  name: string;
  description?: string;
  definition: {
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
  };
  version: number;
  status: "draft" | "published";
  created_at: string;
  updated_at: string;
}

export interface WorkflowNode {
  id: string;
  type: "agent" | "condition" | "output";
  agent_id?: string;
  label?: string;
  config?: Record<string, unknown>;
  position?: { x: number; y: number };
}

export interface WorkflowEdge {
  from: string;
  to: string;
  condition?: string;
  label?: string;
}

export interface Execution {
  id: string;
  agent_id?: string;
  workflow_id?: string;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  steps: ExecutionStep[];
  total_tokens: number;
  total_cost_usd: number;
  duration_ms: number;
  error?: string;
  created_at: string;
  completed_at?: string;
}

export interface ExecutionStep {
  node: string;
  llm_calls: number;
  tokens_in: number;
  tokens_out: number;
  duration_ms: number;
  tool_calls: { tool: string; duration_ms: number; result_summary?: string }[];
  started_at?: string;
  completed_at?: string;
}

export interface UsageMetrics {
  total_executions: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_duration_ms: number;
}

export interface ApiResponse<T> {
  data?: T;
  error?: { message: string; status: number };
}
