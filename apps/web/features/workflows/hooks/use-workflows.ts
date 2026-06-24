/**
 * Workflow Hooks
 *
 * Custom hooks for workflow data fetching, filtering, and state management.
 */

import { useCallback, useMemo, useState } from 'react'
import { useWorkflowStore } from '@/stores/workflow-store'
import type { Workflow } from '@/types/workflow'
import defaultApi from '@/lib/api'

/**
 * Workflow filter options
 */
export interface WorkflowFilterOptions {
  status?: string
  search?: string
  agentType?: string
  limit?: number
  offset?: number
}

/**
 * Workflow statistics
 */
export interface WorkflowStats {
  total: number
  byStatus: Record<string, number>
  recentErrors: number
  byRunning?: number
  byCompleted?: number
  byFailed?: number
}

/**
 * Hook for workflow operations
 *
 * Provides methods to fetch, filter, and manage workflow data.
 */
export function useWorkflows() {
  const store = useWorkflowStore()

  // State for additional filters
  const [filters, setFilters] = useState<WorkflowFilterOptions>({
    status: undefined,
    search: undefined,
    agentType: undefined,
  })

  /**
   * Fetch all workflows from API
   */
  const fetchWorkflows = useCallback(async (params?: {
    offset?: number
    limit?: number
    status?: string
  }): Promise<Workflow[]> => {
    store.setLoading(true)
    store.setError(null)

    try {
      const response = await defaultApi.workflowsAPI.list(params)

      if (response.error) {
        throw new Error(response.error.message)
      }

      const workflows = response.data || []

      // Merge with local store
      store.setWorkflows(workflows)

      return workflows
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch workflows'
      store.setError(errorMessage)
      console.error('Failed to fetch workflows:', error)
      throw error
    } finally {
      store.setLoading(false)
    }
  }, [store])

  /**
   * Refresh workflows (fetch latest data)
   */
  const refreshWorkflows = useCallback(async () => {
    return fetchWorkflows()
  }, [fetchWorkflows])

  /**
   * Apply filters to workflows
   */
  const applyFilters = useCallback((currentFilters?: WorkflowFilterOptions): Workflow[] => {
    const current = currentFilters || filters
    const allWorkflows = store.workflows

    if (!allWorkflows.length) {
      return []
    }

    let filtered = allWorkflows

    // Filter by status
    if (current.status) {
      filtered = filtered.filter((w) => w.status === current.status)
    }

    // Filter by search query
    if (current.search) {
      const query = current.search.toLowerCase()
      filtered = filtered.filter((w) => {
        return (
          w.name.toLowerCase().includes(query) ||
          w.workflow_id.toLowerCase().includes(query) ||
          (w.description && w.description.toLowerCase().includes(query))
        )
      })
    }

    // Filter by agent type
    if (current.agentType) {
      filtered = filtered.filter((w) => w.agent_type === current.agentType)
    }

    // Apply pagination
    if (filters.limit !== undefined) {
      filtered = filtered.slice(0, filters.limit)
    }

    if (filters.offset !== undefined) {
      filtered = filtered.slice(filters.offset)
    }

    return filtered
  }, [filters, store.workflows])

  /**
   * Clear all filters
   */
  const clearFilters = useCallback(() => {
    setFilters({
      status: undefined,
      search: undefined,
      agentType: undefined,
    })
  }, [])

  /**
   * Get workflow statistics
   */
  const getStats = useCallback((): WorkflowStats => {
    const total = store.workflows.length
    const byStatus = store.workflows.reduce(
      (acc, workflow) => {
        acc[workflow.status] = (acc[workflow.status] || 0) + 1
        return acc
      },
      {} as Record<string, number>,
    )

    // Count workflows in error states (failed, cancelled)
    const recentErrors = store.workflows.filter(
      (w) => w.status === 'failed' || w.status === 'cancelled',
    ).length

    return {
      total,
      byStatus,
      recentErrors,
    }
  }, [store.workflows])

  /**
   * Handle form submission with filters
   */
  const handleFilterChange = useCallback((field: keyof WorkflowFilterOptions, value: string | undefined) => {
    setFilters((prev) => {
      const updated = { ...prev, [field]: value }

      // If status filter changes, fetch new data
      if (field === 'status' && value !== prev.status) {
        refreshWorkflows()
      }

      // If search query changes, apply new filter
      if (field === 'search') {
        const filtered = applyFilters(updated)
        console.log('Filtered workflows:', filtered.length)
      }

      return updated
    })
  }, [refreshWorkflows, applyFilters])

  /**
   * Get paginated workflows
   */
  const getPaginatedWorkflows = useMemo(
    () => applyFilters(),
    [applyFilters],
  )

  /**
   * Get current filtered workflow count
   */
  const getFilteredCount = useCallback(() => {
    return applyFilters().length
  }, [applyFilters])

  /**
   * Check if data is loading
   */
  const isLoading = store.isLoading

  /**
   * Get current error
   */
  const error = store.error

  return {
    workflows: getPaginatedWorkflows,
    filteredCount: getFilteredCount(),
    totalWorkflows: store.workflows.length,
    stats: getStats(),
    isLoading,
    error,
    filters,
    setFilters,
    handleFilterChange,
    clearFilters,
    refreshWorkflows,
    applyFilters,
  }
}
