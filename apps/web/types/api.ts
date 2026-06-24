/**
 * API Type Definitions
 *
 * TypeScript interfaces for API responses and requests.
 */

import { WorkflowStatus, ExecutionStatus, Workflow, Execution } from './workflow'

/**
 * API Response interface
 */
export interface ApiResponse<T> {
  data: T | null
  error: ApiError | null
}

/**
 * API Error interface
 */
export interface ApiError {
  type: 'authentication' | 'permission' | 'validation' | 'server' | 'not_found'
  message: string
  statusCode?: number
  details?: Record<string, any>
}

/**
 * Request headers interface
 */
export interface RequestHeaders {
  'Content-Type'?: string
  'Authorization'?: string
  'X-Request-ID'?: string
}

/**
 * API Client methods interface
 */
export interface ApiClientMethods {
  get: <T>(endpoint: string, params?: Record<string, any>) => Promise<ApiResponse<T>>
  post: <T>(
    endpoint: string,
    body: unknown,
  ) => Promise<ApiResponse<T>>
  put: <T>(
    endpoint: string,
    body: unknown,
  ) => Promise<ApiResponse<T>>
  patch: <T>(
    endpoint: string,
    body: unknown,
  ) => Promise<ApiResponse<T>>
  del: <T>(endpoint: string) => Promise<ApiResponse<T>>
}

/**
 * Auth API methods
 */
export interface AuthApiMethods {
  login: (credentials: {
    email: string
    password: string
  }) => Promise<ApiResponse<{ token: string; user: string }>>
  logout: () => Promise<ApiResponse<void>>
  refreshToken: () => Promise<ApiResponse<string>>
}

/**
 * Workflow API methods
 */
export interface WorkflowApiMethods {
  list: (params?: {
    offset?: number
    limit?: number
    status?: WorkflowStatus
  }) => Promise<ApiResponse<Workflow[]>>
  get: (workflowId: string) => Promise<ApiResponse<Workflow>>
  create: (body: any) => Promise<ApiResponse<Workflow>>
  execute: (
    workflowId: string,
    body: any,
  ) => Promise<ApiResponse<Workflow>>
  listExecutions: (
    workflowId: string,
    params?: { limit?: number },
  ) => Promise<ApiResponse<Execution[]>>
  getExecution: (
    workflowId: string,
    executionId: string,
  ) => Promise<ApiResponse<Execution>>
  cancel: (
    workflowId: string,
    executionId: string,
  ) => Promise<ApiResponse<Execution>>
  retry: (
    workflowId: string,
    executionId: string,
  ) => Promise<ApiResponse<Execution>>
  resume: (
    workflowId: string,
    executionId: string,
  ) => Promise<ApiResponse<Execution>>
}

/**
 * WebSocket event types
 */
export interface WebSocketEvents {
  workflow_created: { workflowId: string; name: string }
  workflow_completed: { workflowId: string; status: 'completed' }
  workflow_failed: { workflowId: string; error: string }
  workflow_cancelled: { workflowId: string }
  execution_started: { executionId: string; workflowId: string }
  execution_completed: { executionId: string; status: 'completed' }
  execution_failed: { executionId: string; error: string }
  execution_cancelled: { executionId: string }
  heartbeat: { timestamp: number }
}

/**
 * WebSocket message types
 */
export type WebSocketMessage<T extends keyof WebSocketEvents> =
  WebSocketEvents[T]

/**
 * API Status codes
 */
export enum ApiStatusCode {
  OK = 200,
  CREATED = 201,
  BAD_REQUEST = 400,
  UNAUTHORIZED = 401,
  FORBIDDEN = 403,
  NOT_FOUND = 404,
  UNPROCESSABLE_ENTITY = 422,
  INTERNAL_SERVER_ERROR = 500,
}

/**
 * Environment configuration
 */
export interface EnvironmentConfig {
  API_URL: string
  API_NAME: string
  API_VERSION: string
  ENVIRONMENT: 'development' | 'staging' | 'production'
  DEBUG: boolean
}

/**
 * Query parameters type
 */
export interface QueryParams {
  offset?: number
  limit?: number
  status?: WorkflowStatus | ExecutionStatus
  sort?: string
  order?: 'asc' | 'desc'
}
