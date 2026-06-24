/**
 * Workflow Dashboard Page
 *
 * Main dashboard for viewing and managing workflows.
 */

'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  Workflow,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
} from 'lucide-react'
import { useAuthStore } from '@/stores/auth-store'
import { WorkflowFilters } from '../../features/workflows/components/workflow-filters'
import { WorkflowTable } from '../../features/workflows/components/workflow-table'
import { useWorkflows } from '../../features/workflows/hooks/use-workflows'

export default function DashboardPage() {
  const { isLoading: authLoading } = useAuthStore()
  const {
    workflows,
    filteredCount,
    totalWorkflows,
    stats,
    isLoading: apiLoading,
    error,
    filters,
    clearFilters,
    refreshWorkflows,
  } = useWorkflows()

  // Local state for filters
  const [showFilters, setShowFilters] = useState(false)
  const [searchValue, setSearchValue] = useState(filters.search || '')
  const [statusValue, setStatusValue] = useState(filters.status)

  // Combined loading state
  const isLoading = authLoading || apiLoading

  const hasResults = !isLoading && workflows.length > 0
  const emptyMessage = error
    ? `Error: ${error}. Please try again later.`
    : 'No workflows found. Try adjusting your filters or create a new workflow.'

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Workflows</h1>
          <p className="text-muted-foreground mt-1">
            Manage and monitor your workflow executions
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={cn(
              'inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm',
              error
                ? 'border-destructive/20 bg-destructive/10 text-destructive'
                : 'border-primary/20 bg-primary/10 text-primary',
            )}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Loading...</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="h-4 w-4" />
                <span>{filteredCount} workflows</span>
              </>
            )}
          </span>
        </div>
      </div>

      {/* Filters */}
      <WorkflowFilters
        searchValue={searchValue}
        setSearchValue={setSearchValue}
        statusValue={statusValue}
        setStatusValue={setStatusValue}
        showFilters={showFilters}
        setShowFilters={setShowFilters}
        resetFilters={() => {
          setSearchValue('')
          setStatusValue(undefined)
          clearFilters()
        }}
        clearSearch={() => setSearchValue('')}
      />

      {/* Workflow Table */}
      {hasResults && (
        <WorkflowTable
          workflows={workflows}
          loading={isLoading}
          emptyMessage={emptyMessage}
          className="min-h-[400px]"
        />
      )}

      {/* Empty State */}
      {!hasResults && !isLoading && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed bg-muted/30 p-12 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
            {error ? (
              <XCircle className="h-8 w-8 text-destructive" />
            ) : (
              <Workflow className="h-8 w-8 text-muted-foreground" />
            )}
          </div>
          <h3 className="mt-4 text-lg font-semibold">
            {error
              ? 'Failed to load workflows'
              : 'No workflows found'}
          </h3>
          {!error && (
            <p className="text-muted-foreground mt-1 max-w-sm">
              {filters.status
                ? `No workflows with status "${filters.status}". Try a different filter or clear it.`
                : 'Get started by creating your first workflow or try adjusting your search filters.'}
            </p>
          )}
          {error && (
            <p className="text-muted-foreground mt-2 text-sm">
              {error}
            </p>
          )}
          <div className="mt-4 flex gap-2">
            <button
              onClick={() => {
                setSearchValue('')
                setStatusValue(undefined)
                clearFilters()
              }}
              className="rounded-md border border-primary/20 bg-primary/10 px-4 py-2 text-sm text-primary hover:bg-primary/20"
            >
              Reset Filters
            </button>
            <button
              onClick={refreshWorkflows}
              className="rounded-md border border-border px-4 py-2 text-sm hover:bg-muted"
            >
              Refresh
            </button>
          </div>
        </div>
      )}

      {/* Footer Stats */}
      {hasResults && (
        <div className="flex items-center justify-between rounded-lg border bg-muted/50 p-4 text-sm">
          <div className="flex items-center gap-6">
            {/* Total */}
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                <LayoutDashboard className="h-4 w-4 text-primary" />
              </div>
              <div>
                <div className="font-semibold">{totalWorkflows}</div>
                <div className="text-muted-foreground">Total Workflows</div>
              </div>
            </div>

            {/* Running */}
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-500/10">
                <div className="h-2 w-2 animate-ring rounded-full bg-green-600" />
              </div>
              <div>
                <div className="font-semibold text-green-700">
                  {stats.byRunning || workflows.filter((w: any) => w.status === 'running').length}
                </div>
                <div className="text-muted-foreground">Running</div>
              </div>
            </div>

            {/* Completed */}
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500/10">
                <CheckCircle2 className="h-4 w-4 text-blue-600" />
              </div>
              <div>
                <div className="font-semibold text-blue-700">
                  {stats.byCompleted || workflows.filter((w: any) => w.status === 'completed').length}
                </div>
                <div className="text-muted-foreground">Completed</div>
              </div>
            </div>

            {/* Failed */}
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-500/10">
                <XCircle className="h-4 w-4 text-red-600" />
              </div>
              <div>
                <div className="font-semibold text-red-700">
                  {stats.byFailed || workflows.filter((w: any) => w.status === 'failed').length}
                </div>
                <div className="text-muted-foreground">Failed</div>
              </div>
            </div>
          </div>

          {/* Refresh */}
          <button
            onClick={refreshWorkflows}
            className="flex items-center gap-2 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-muted"
          >
            <Clock className="h-4 w-4" />
            <span>Refresh</span>
          </button>
        </div>
      )}
    </div>
  )
}
