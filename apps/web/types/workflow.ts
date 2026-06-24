/**
 * Workflow Type Definitions
 *
 * TypeScript interfaces for workflow and execution models.
 */

/**
 * Workflow status enumeration
 */
export type WorkflowStatus =
  | 'created'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'paused'
  | 'resuming'
  | 'resumed'
  | 'escalated'

/**
 * Workflow model interface
 */
export interface Workflow {
  id: string
  workflow_id: string
  name: string
  description?: string
  status: WorkflowStatus
  execution_id?: string
  agent_type: string
  inputs?: Record<string, any>
  output_schema?: Record<string, any>
  created_at: string
  updated_at: string
  creator_id?: string
  tags?: string[]
}

/**
 * Execution status enumeration
 */
export type ExecutionStatus =
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'

/**
 * Execution model interface
 */
export interface Execution {
  id: string
  workflow_id: string
  status: ExecutionStatus
  priority?: number
  cancel_on_timeout?: boolean
  webhook_url?: string
  created_at: string
  started_at?: string
  completed_at?: string
  error?: string
}

/**
 * Workflow creation payload
 */
export interface WorkflowCreatePayload {
  workflow_id: string
  name: string
  description?: string
  agent_type?: string
  inputs?: Record<string, any>
  output_schema?: Record<string, any>
  timeout_seconds?: number
  max_retries?: number
}

/**
 * Execution creation payload
 */
export interface ExecutionCreatePayload {
  priority?: number
  cancel_on_timeout?: boolean
  webhook_url?: string
}

/**
 * Workflow update payload
 */
export interface WorkflowUpdatePayload {
  name?: string
  description?: string
  timeout_seconds?: number
  max_retries?: number
}

/**
 * Execution update payload
 */
export interface ExecutionUpdatePayload {
  status?: string
  error?: string
  webhook_url?: string
}

/**
 * Workflow response schema
 */
export interface WorkflowResponse extends Workflow {
  agent_type: 'planner' | 'developer' | 'reviewer' | 'supervisor'
}

/**
 * Execution response schema
 */
export interface ExecutionResponse extends Execution {
  workflow_id: string
}
