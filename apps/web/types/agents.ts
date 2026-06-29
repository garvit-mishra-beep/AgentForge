/**
 * Agent Types
 * Defines Typescript interfaces and types for agent-related functionality
 */

import type { ProviderName } from "@/lib/constants";

// Agent role definitions
export type AgentRole =
  | "team_lead"
  | "builder"
  | "reviewer"
  | "tester"
  | "security"
  | "devops"
  | "planner"
  | "architect"
  | "aggregator";

// Agent status definitions
export type AgentStatus =
  | "idle"
  | "planning"
  | "building"
  | "reviewing"
  | "testing"
  | "delivering"
  | "error"
  | "offline";

// Agent configuration
export interface AgentConfig {
  role: AgentRole;
  label: string;
  description: string;
  icon: string; // Lucide icon name
  defaultModel: string;
  availableModels: string[];
  color: string; // CSS variable reference
  bg: string; // background color class
  text: string; // text color class
}

// Agent instance/runtime state
export interface AgentInstance {
  id: string;
  agentId: string; // reference to agent template/config
  role: AgentRole;
  status: AgentStatus;
  currentTaskId: string | null;
  model: string;
  provider: ProviderName;
  lastActivity: string; // ISO timestamp
  tokensUsed: number;
  error: string | null;
}

// Agent message for UI/display
export interface AgentMessage {
  id: string;
  agentId: string;
  role: AgentRole;
  model: string;
  content: string;
  timestamp: string; // ISO timestamp
  isPartial: boolean; // true if this is a streaming chunk
}

// Agent capability definition
export interface AgentCapability {
  id: string;
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  outputSchema: Record<string, unknown>;
}

// Agent performance metrics
export interface AgentMetrics {
  tasksCompleted: number;
  successRate: number; // percentage
  avgResponseTime: number; // milliseconds
  totalTokensUsed: number;
  averageTokensPerTask: number;
}

// Agent assignment/association with teams
export interface AgentAssignment {
  agentId: string;
  teamId: string;
  role: AgentRole;
  model: string;
  isActive: boolean;
  assignedAt: string; // ISO timestamp
}

// Agent factory/creation parameters
export interface AgentFactoryParams {
  role: AgentRole;
  model: string;
  provider: ProviderName;
  configOverride?: Partial<AgentConfig>;
}

// Agent team composition
export interface TeamAgentComposition {
  teamId: string;
  agents: AgentAssignment[];
  primaryRole: AgentRole; // team_lead typically
  createdAt: string; // ISO timestamp
}

// Agent health/status
export interface AgentHealth {
  agentId: string;
  status: AgentStatus;
  isHealthy: boolean;
  lastCheck: string; // ISO timestamp
  version: string;
  uptimeSeconds: number;
}

// Agent interaction/event types
export interface AgentEvent {
  id: string;
  agentId: string;
  type: "start" | "message" | "complete" | "error" | "handoff";
  timestamp: string; // ISO timestamp
  payload: {
    message?: string;
    error?: string;
    nextAgent?: AgentRole;
    data?: Record<string, unknown>;
  };
}

// Agent capability registry
export interface AgentRegistry {
  agents: Record<AgentRole, AgentConfig>;
  capabilities: Record<string, AgentCapability>;
  getAgentConfig(role: AgentRole): AgentConfig | undefined;
  registerCapability(capability: AgentCapability): void;
}
