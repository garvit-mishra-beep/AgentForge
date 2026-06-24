/**
 * Workflow State Store
 *
 * Zustand store for managing workflow state including:
 * - CRUD operations
 * - Execution management
 * - List and filtering
 */

import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { generateId } from '@/lib/utils'

// Workflow status types
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

// Execution status types
export type ExecutionStatus =
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'

// Workflow interface
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
  retry_count?: number
}

// Execution interface
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

// Action interfaces
interface WorkflowStore {
  workflows: Workflow[]
  executions: Execution[]
  activeWorkflowId: string | null
  activeExecutionId: string | null
  isLoading: boolean
  error: string | null

  // Actions
  setWorkflows: (workflows: Workflow[]) => void
  appendWorkflows: (workflows: Workflow[]) => void
  addWorkflow: (workflow: Omit<Workflow, 'id' | 'created_at' | 'updated_at'>) => Workflow
  removeWorkflow: (workflowId: string) => void
  setActiveWorkflow: (workflowId: string | null) => void
  resetActiveWorkflow: () => void

  setExecutions: (executions: Execution[]) => void
  appendExecutions: (executions: Execution[]) => void
  addExecution: (execution: Omit<Execution, 'id' | 'created_at'>) => Execution
  removeExecution: (executionId: string) => void
  setActiveExecution: (executionId: string | null) => void
  resetActiveExecution: () => void

  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void

  // Filter actions
  filterWorkflows: (status?: WorkflowStatus, limit?: number, offset?: number) => Workflow[]
  clearFilter: () => void
}

// Create store
export const useWorkflowStore = create<WorkflowStore>()(
  devtools(
    persist(
      (set, get) => ({
        workflows: [],
        executions: [],
        activeWorkflowId: null,
        activeExecutionId: null,
        isLoading: false,
        error: null,

        // Set all workflows
        setWorkflows: (workflows) =>
          set({ workflows, activeWorkflowId: workflows[0]?.id || null }),

        // Append new workflows
        appendWorkflows: (workflows) =>
          set((state) => ({
            workflows: [
              ...state.workflows,
              ...workflows.map((w) => ({
                ...w,
                id: w.id || generateId('wf'),
              })),
            ],
          })),

        // Add single workflow
        addWorkflow: (workflowData) => {
          const workflow: Workflow = {
            ...workflowData,
            id: (workflowData as any).id || generateId('wf'),
            status: workflowData.status || 'created',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }
          set((state) => ({
            workflows: [...state.workflows, workflow],
            activeWorkflowId: workflow.id,
          }))
          return workflow
        },

        // Remove workflow
        removeWorkflow: (workflowId) =>
          set((state) => ({
            workflows: state.workflows.filter((w) => w.id !== workflowId),
            activeWorkflowId:
              state.activeWorkflowId === workflowId
                ? null
                : state.activeWorkflowId,
          })),

        // Set active workflow
        setActiveWorkflow: (workflowId) =>
          set({ activeWorkflowId: workflowId || null }),

        // Reset active workflow
        resetActiveWorkflow: () => set({ activeWorkflowId: null }),

        // Set all executions
        setExecutions: (executions) => set({ executions }),

        // Append new executions
        appendExecutions: (executions) =>
          set((state) => ({
            executions: [
              ...state.executions,
              ...executions.map((e) => ({
                ...e,
                id: e.id || generateId('ex'),
              })),
            ],
          })),

        // Add single execution
        addExecution: (executionData) => {
          const execution: Execution = {
            ...executionData,
            id: (executionData as any).id || generateId('ex'),
            status: executionData.status || 'running',
            created_at: new Date().toISOString(),
          }
          set((state) => ({
            executions: [...state.executions, execution],
            activeExecutionId: execution.id,
          }))
          return execution
        },

        // Remove execution
        removeExecution: (executionId) =>
          set((state) => ({
            executions: state.executions.filter((e) => e.id !== executionId),
            activeExecutionId:
              state.activeExecutionId === executionId
                ? null
                : state.activeExecutionId,
          })),

        // Set active execution
        setActiveExecution: (executionId) =>
          set({ activeExecutionId: executionId || null }),

        // Reset active execution
        resetActiveExecution: () => set({ activeExecutionId: null }),

        // Set loading state
        setLoading: (loading) => set({ isLoading: loading }),

        // Set error
        setError: (error) => set({ error }),

        // Filter workflows by status
        filterWorkflows: (status, limit, offset) => {
          let filtered = get().workflows

          if (status) {
            filtered = filtered.filter((w) => w.status === status)
          }

          if (offset !== undefined) {
            filtered = filtered.slice(offset)
          }

          if (limit !== undefined) {
            filtered = filtered.slice(0, limit)
          }

          return filtered
        },

        // Clear filter
        clearFilter: () => set({ workflows: get().workflows }),
      }),
      {
        name: 'workflow-store',
        partialize: (state) => ({
          workflows: state.workflows,
          executions: state.executions,
        }),
        version: 1,
      },
    ),
    {
      enabled: process.env.NODE_ENV === 'development',
    },
  ),
)
