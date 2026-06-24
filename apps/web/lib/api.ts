/**
 * API Client for AgentOS
 *
 * Typed API client with authentication support, JWT storage,
 * error handling, and request helpers.
 */

// Base API URL - update this to your backend
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

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
 * API Response interface
 */
export interface ApiResponse<T> {
  data: T | null
  error: ApiError | null
  pagination?: {
    offset: number
    limit: number
    total: number
  }
}

/**
 * RequestOptions interface
 */
export interface RequestOptions {
  signal?: AbortSignal
  retry?: number
  retryDelay?: number
}

/**
 * Get headers for authenticated requests
 */
export function getAuthHeaders(): Record<string, string> {
  const token = getAuthToken()

  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  }
}

/**
 * Get authentication token from localStorage
 */
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') {
    return null
  }

  try {
    const token = localStorage.getItem('agentos_auth_token')
    return token ? JSON.parse(token) : null
  } catch {
    return null
  }
}

/**
 * Set authentication token in localStorage
 */
export function setAuthToken(token: string): void {
  if (typeof window === 'undefined') {
    return
  }

  try {
    localStorage.setItem('agentos_auth_token', JSON.stringify(token))
  } catch {
    // Ignore storage errors
  }
}

/**
 * Clear authentication token from localStorage
 */
export function clearAuthToken(): void {
  if (typeof window === 'undefined') {
    return
  }

  try {
    localStorage.removeItem('agentos_auth_token')
  } catch {
    // Ignore storage errors
  }
}

/**
 * Check if token is expired (JWT)
 */
export function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const exp = payload.exp
    const now = Math.floor(Date.now() / 1000)

    return now >= exp
  } catch {
    return true
  }
}

/**
 * Refresh authentication token
 */
export async function refreshAuthToken(): Promise<string | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })

    if (response.ok) {
      const data = await response.json()
      return data.token
    }

    return null
  } catch {
    return null
  }
}

/**
 * Make API request with error handling and retry logic
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit & RequestOptions = {},
): Promise<ApiResponse<T>> {
  const { signal } = options

  try {
    const url = `${API_BASE_URL}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    // Handle request with auth
    const token = getAuthToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    // Check for cancelled requests
    if (signal?.aborted) {
      return {
        data: null,
        error: {
          type: 'authentication',
          message: 'Request was cancelled',
        },
      }
    }

    // Check if request is a no-op
    const isNoOp =
      options.method === 'GET' &&
      Object.keys(options.body || {}).length === 0 &&
      Object.keys(options.headers || {}).length === 1

    if (isNoOp) {
      return {
        data: null,
        error: {
          type: 'authentication',
          message: 'Request body cannot be read.',
        },
      }
    }

    // Execute request
    const response = await fetch(url, {
      ...options,
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    })

    // Check for auth errors
    if (response.status === 401 || response.status === 403) {
      const errorToken = await refreshAuthToken()
      if (errorToken) {
        setAuthToken(errorToken)
        // Retry with new token
        return apiRequest(endpoint, options)
      }
      return {
        data: null,
        error: {
          type: response.status === 401 ? 'authentication' : 'permission',
          message: 'Unauthorized access',
          statusCode: response.status,
        },
      }
    }

    // Parse response
    let data: T | null = null
    let error: ApiError | null = null

    if (response.status >= 200 && response.status < 300) {
      try {
        const json = await response.json()
        data = json
      } catch {
        data = null
      }
    } else {
      try {
        const json = await response.json()
        error = {
          type: 'server',
          message: json.detail || response.statusText,
          statusCode: response.status,
        }
      } catch {
        error = {
          type: 'server',
          message: response.statusText,
          statusCode: response.status,
        }
      }
    }

    return {
      data,
      error,
    }
  } catch (err) {
    // Handle network errors
    if (signal?.aborted) {
      return {
        data: null,
        error: {
          type: 'authentication',
          message: 'Request was cancelled',
        },
      }
    }

    return {
      data: null,
      error: {
        type: 'server',
        message: err instanceof Error ? err.message : 'Network error',
      },
    }
  }
}

/**
 * Make GET request
 */
export async function get<T>(
  endpoint: string,
  params?: Record<string, any>,
): Promise<ApiResponse<T>> {
  let url = endpoint
  if (params && Object.keys(params).length > 0) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null) {
        searchParams.append(key, String(val))
      }
    })
    const query = searchParams.toString()
    if (query) {
      url += `?${query}`
    }
  }
  return apiRequest<T>(url, {
    method: 'GET',
  })
}

/**
 * Make POST request
 */
export async function post<T>(
  endpoint: string,
  body?: any,
): Promise<ApiResponse<T>> {
  return apiRequest<T>(endpoint, {
    method: 'POST',
    body,
  })
}

/**
 * Make PUT request
 */
export async function put<T>(
  endpoint: string,
  body?: any,
): Promise<ApiResponse<T>> {
  return apiRequest<T>(endpoint, {
    method: 'PUT',
    body,
  })
}

/**
 * Make PATCH request
 */
export async function patch<T>(
  endpoint: string,
  body?: any,
): Promise<ApiResponse<T>> {
  return apiRequest<T>(endpoint, {
    method: 'PATCH',
    body,
  })
}

/**
 * Make DELETE request
 */
export async function del<T>(endpoint: string): Promise<ApiResponse<T>> {
  return apiRequest<T>(endpoint, {
    method: 'DELETE',
  })
}

/**
 * Get workflows API
 */
export const workflowsAPI = {
  list: (
    params?: {
      offset?: number
      limit?: number
      status?: string
    },
  ): Promise<ApiResponse<any[]>> =>
    get('/workflows', params),

  get: (workflowId: string): Promise<ApiResponse<any>> =>
    get(`/workflows/${workflowId}`),

  create: (body: any): Promise<ApiResponse<any>> =>
    post('/workflows', body),

  execute: (workflowId: string, body: any): Promise<ApiResponse<any>> =>
    post(`/workflows/${workflowId}/execute`, body),

  listExecutions: (
    workflowId: string,
    params?: { limit?: number },
  ): Promise<ApiResponse<any[]>> =>
    get(`/workflows/${workflowId}/executions`, params),

  getExecution: (
    workflowId: string,
    executionId: string,
  ): Promise<ApiResponse<any>> =>
    get(`/workflows/${workflowId}/executions/${executionId}`),

  cancel: (
    workflowId: string,
    executionId: string,
  ): Promise<ApiResponse<any>> =>
    post(`/workflows/${workflowId}/executions/${executionId}/cancel`),

  retry: (
    workflowId: string,
    executionId: string,
  ): Promise<ApiResponse<any>> =>
    post(`/workflows/${workflowId}/executions/${executionId}/retry`),

  resume: (
    workflowId: string,
    executionId: string,
  ): Promise<ApiResponse<any>> =>
    post(`/workflows/${workflowId}/executions/${executionId}/resume`),

  getExecutionMessages: (
    workflowId: string,
    executionId: string,
  ): Promise<ApiResponse<any[]>> =>
    get(`/workflows/${workflowId}/executions/${executionId}/messages`),
}

/**
 * Get auth API
 */
export const authAPI = {
  login: (credentials: { email: string; password: string }) =>
    post('/auth/token', credentials),

  logout: (): Promise<ApiResponse<void>> =>
    post('/auth/logout'),

  refreshToken: (): Promise<ApiResponse<string>> =>
    post('/auth/refresh'),
}

/**
 * Export all API functions for use in components
 */
export default {
  get,
  post,
  put,
  patch,
  del,
  workflowsAPI,
  authAPI,
  getAuthHeaders,
  getAuthToken,
  setAuthToken,
  clearAuthToken,
  isTokenExpired,
  refreshAuthToken,
}
