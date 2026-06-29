/**
 * WebSocket Types
 * Generated from WEBSOCKET_EVENT_MAP.md - defines WebSocket event types for real-time communication
 */

import type { AgentRole, TaskStatus } from "@/lib/constants";

// Base WebSocket event structure
export interface WSEvent<T = unknown> {
  type: string;
  payload: T;
  timestamp: string; // ISO date string
}

// Agent message event - streaming agent responses
export interface AgentMessageEventPayload {
  content: string; // text chunk from agent
  role: AgentRole; // which agent sent the message
  model: string; // model being used
  chunk_index: number; // sequence number for ordering chunks
}

// Task status update event
export interface TaskStatusUpdateEventPayload {
  task_id: string;
  status: TaskStatus;
  progress: number | null; // percentage (0-100) for long-running operations
}

// Execution log event - real-time logs from execution nodes
export interface ExecutionLogEventPayload {
  execution_id: string;
  node: string; // which node generated the log (team_lead, builder, etc.)
  timestamp: string; // ISO timestamp
  data: string; // log content
}

// Team update event
export interface TeamUpdateEventPayload {
  team_id: string;
  members: Array<{
    id: string;
    team_id: string;
    role: AgentRole;
    model: string;
    instructions: string;
    created_at: string;
  }>;
}

// Artifact update event - notifications when new artifacts are generated
export interface ArtifactUpdateEventPayload {
  task_id: string;
  artifact_type: string; // "image", "file", "log", "artifact", etc.
  url: string; // URL to access/download the artifact
  metadata: Record<string, unknown>; // additional metadata about the artifact
}

// Connection status events
export interface WSConnectionEventPayload {
  status: "connecting" | "connected" | "reconnecting" | "disconnected" | "error";
  message?: string;
}

// Union of all possible WebSocket event payloads
export type WSAgentMessageEvent = WSEvent<AgentMessageEventPayload>;
export type WSTaskStatusUpdateEvent = WSEvent<TaskStatusUpdateEventPayload>;
export type WSExecutionLogEvent = WSEvent<ExecutionLogEventPayload>;
export type WSTeamUpdateEvent = WSEvent<TeamUpdateEventPayload>;
export type WSArtifactUpdateEvent = WSEvent<ArtifactUpdateEventPayload>;
export type WSConnectionEvent = WSEvent<WSConnectionEventPayload>;

export type KnownWSEvent =
  | WSAgentMessageEvent
  | WSTaskStatusUpdateEvent
  | WSExecutionLogEvent
  | WSTeamUpdateEvent
  | WSArtifactUpdateEvent
  | WSConnectionEvent;
