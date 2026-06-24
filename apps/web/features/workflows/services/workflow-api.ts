/**
 * Workflow API Service
 *
 * Service layer for workflow API operations with error handling and retry logic.
 */

import defaultApi from '@/lib/api'
import type { Workflow, Execution, WorkflowCreatePayload, ExecutionCreatePayload } from '@/types/workflow'

/**
 * Workflow list response type
 */
export interface WorkflowListResponse {
  workflows: Workflow[]
  pagination?: {
    offset: number
    limit: number
    total: number
  }
}

/**
 * Execution list response type
 */
export interface ExecutionListResponse {
  executions: Execution[]
  pagination?: {
    limit: number
    offset: number
    total: number
  }
}

/**
 * Fetch workflow list from API
 *
 * @param params - Query parameters for pagination and filtering
 * @returns Parsed workflow list response
 */
export async function fetchWorkflows(params?: {
  offset?: number
  limit?: number
  status?: string
}): Promise<WorkflowListResponse> {
  const response = await defaultApi.workflowsAPI.list(params)

  if (response.error) {
    throw new Error(response.error.message)
  }

  return {
    workflows: response.data || [],
    pagination: response.pagination || undefined,
  }
}

/**
 * Fetch a single workflow by ID
 *
 * @param workflowId - The workflow identifier
 * @returns Parsed workflow data
 */
export async function fetchWorkflow(workflowId: string): Promise<Workflow> {
  const response = await defaultApi.workflowsAPI.get(workflowId)

  if (response.error) {
    throw new Error(response.error.message)
  }

  return response.data
}

/**
 * Create a new workflow
 *
 * @param payload - Workflow creation payload
 * @returns Created workflow
 */
export async function createWorkflow(
  payload: WorkflowCreatePayload,
): Promise<Workflow> {
  const response = await defaultApi.workflowsAPI.create(payload)

  if (response.error) {
    throw new Error(response.error.message)
  }

  return response.data
}

/**
 * Execute a workflow
 *
 * @param workflowId - The workflow identifier
 * @param payload - Execution creation payload
 * @returns Created execution
 */
export async function executeWorkflow(
  workflowId: string,
  payload?: ExecutionCreatePayload,
): Promise<Execution> {
  const response = await defaultApi.workflowsAPI.execute(workflowId, payload)

  if (response.error) {
    throw new Error(response.error.message)
  }

  return response.data
}

/**
 * Cancel a workflow execution
 *
 * @param workflowId - The workflow identifier
 * @param executionId - The execution identifier
 */
export async function cancelExecution(
  workflowId: string,
  executionId: string,
): Promise<void> {
  const response = await defaultApi.workflowsAPI.cancel(workflowId, executionId)

  if (response.error) {
    throw new Error(response.error.message)
  }
}

/**
 * Retry a failed execution
 *
 * @param workflowId - The workflow identifier
 * @param executionId - The execution identifier
 */
export async function retryExecution(
  workflowId: string,
  executionId: string,
): Promise<void> {
  const response = await defaultApi.workflowsAPI.retry(workflowId, executionId)

  if (response.error) {
    throw new Error(response.error.message)
  }
}

/**
 * Resume a paused execution
 *
 * @param workflowId - The workflow identifier
 * @param executionId - The execution identifier
 */
export async function resumeExecution(
  workflowId: string,
  executionId: string,
): Promise<void> {
  const response = await defaultApi.workflowsAPI.resume(workflowId, executionId)

  if (response.error) {
    throw new Error(response.error.message)
  }
}

/**
 * Fetch workflow executions list
 *
 * @param workflowId - The workflow identifier
 * @param params - Query parameters
 * @returns Parsed executions list
 */
export async function fetchExecutions(
  workflowId: string,
  params?: {
    limit?: number
    offset?: number
    status?: string
  },
): Promise<ExecutionListResponse> {
  const response = await defaultApi.workflowsAPI.listExecutions(workflowId, params)

  if (response.error) {
    throw new Error(response.error.message)
  }

  return {
    executions: response.data || [],
    pagination: response.pagination || undefined,
  }
}

/**
 * Fetch single execution
 *
 * @param workflowId - The workflow identifier
 * @param executionId - The execution identifier
 * @returns Parsed execution data
 */
export async function fetchExecution(
  workflowId: string,
  executionId: string,
): Promise<Execution> {
  const response = await defaultApi.workflowsAPI.getExecution(workflowId, executionId)

  if (response.error) {
    throw new Error(response.error.message)
  }

  return response.data
}

/**
 * Delete a workflow
 *
 * @param workflowId - The workflow identifier
 */
export async function deleteWorkflow(workflowId: string): Promise<void> {
  const response = await defaultApi.del(`/workflows/${workflowId}`)

  if (response.error) {
    throw new Error(response.error.message)
  }
}

/**
 * Get workflow error with details
 *
 * @param error - The error object from API response
 * @param errorType - The type of error
 * @returns Formatted error message with type
 */
export function getWorkflowError(error: { message: string; statusCode?: number }): {
  message: string
  type: 'network' | 'authentication' | 'permission' | 'validation' | 'server'
  statusCode?: number
} {
  const statusCode = error.statusCode || 0
  const message = error.message || 'Unknown error'

  if (statusCode === 401 || statusCode === 403) {
    return {
      message: 'Authentication required. Please login.',
      type: 'authentication',
      statusCode,
    }
  }

  if (statusCode >= 400 && statusCode < 500) {
    return {
      message,
      type: 'server',
      statusCode,
    }
  }

  if (statusCode >= 500) {
    return {
      message: 'Internal server error. Please try again later.',
      type: 'server',
      statusCode,
    }
  }

  return {
    message,
    type: 'network',
  }
}

/**
 * Handle API request error with retry logic
 *
 * @param requestFn - Async function to retry
 * @param options - Retry configuration
 * @returns Result of request
 */
export async function requestWithRetry<T>(
  requestFn: () => Promise<T>,
  options: {
    maxRetries?: number
    retryDelay?: number
    backoff?: boolean
  } = {},
): Promise<T> {
  const { maxRetries = 3, retryDelay = 1000, backoff = true } = options
  let lastError: Error | null = null

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn()
    } catch (error) {
      lastError = error instanceof Error ? error : new Error('Unknown error')

      // Don't retry on non-retryable errors
      if (lastError.message.includes('ECONNREFUSED') || lastError.message.includes('ENOTFOUND')) {
        break
      }

      // Retry with delay
      if (attempt < maxRetries) {
        const delay = backoff ? retryDelay * Math.pow(2, attempt) : retryDelay
        await new Promise((resolve) => setTimeout(resolve, delay))
      }
    }
  }

  throw lastError || new Error('All retries failed')
}
