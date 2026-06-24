/**
 * Workflow Table Component
 *
 * Displays workflows in a table format with sorting and filtering.
 */

'use client'

import * as React from 'react'
import Link from 'next/link'
import { cn } from '@/lib/utils'
import {
  Search,
  X,
  SlidersHorizontal,
  Filter,
  Play,
  CheckCircle2,
  Circle,
  XCircle,
  RotateCcw,
  Clock,
} from 'lucide-react'
import { Button } from '@/components/ui/loading'
import { Input } from '@/components/ui/input'
import type { Workflow, WorkflowStatus as WorkflowStatusType } from '@/types/workflow'

/**
 * Workflow table row props
 */
interface WorkflowTableRowProps {
  workflow: Workflow
  onClick: (workflowId: string) => void
  onRetry?: (workflowId: string) => void
  onCancel?: (workflowId: string) => void
  className?: string
}

/**
 * WorkflowTable component
 *
 * Displays workflows in a table format with all available columns.
 */
interface WorkflowTableProps {
  workflows: Workflow[]
  loading?: boolean
  emptyMessage?: string
  onClick?: (workflowId: string) => void
  onRetry?: (workflowId: string) => void
  onCancel?: (workflowId: string) => void
  className?: string
}


/**
 * Format timestamp for display
 */
function formatTimestamp(dateString: string): string {
  return new Date(dateString).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * WorkflowTable component
 */
export function WorkflowTable({
  workflows,
  loading = false,
  emptyMessage = 'No workflows found',
  onClick,
  onRetry,
  onCancel,
  className,
}: WorkflowTableProps) {
  return (
    <div className={cn('space-y-4', className)}>
      {/* Stats Overview */}
      {workflows.length > 0 && (
        <div className="flex items-center justify-between rounded-lg border bg-muted/50 p-3 text-sm">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                <SlidersHorizontal className="h-4 w-4 text-primary" />
              </div>
              <div>
                <div className="font-semibold">{workflows.length}</div>
                <div className="text-muted-foreground">Total Workflows</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-500/10">
                <div className="h-2 w-2 animate-ring rounded-full bg-green-600" />
              </div>
              <div>
                <div className="font-semibold text-green-700">
                  {workflows.filter((w) => w.status === 'running').length}
                </div>
                <div className="text-muted-foreground">Running</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-500/10">
                <div className="h-2 w-2 animate-ring rounded-full bg-green-600" />
              </div>
              <div>
                <div className="font-semibold text-green-700">
                  {workflows.filter((w: Workflow) => w.status === 'completed').length}
                </div>
                <div className="text-muted-foreground">Completed</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-500/10">
                <XCircle className="h-4 w-4 text-red-600" />
              </div>
              <div>
                <div className="font-semibold text-red-700">
                  {workflows.filter((w: Workflow) => w.status === 'failed').length}
                </div>
                <div className="text-muted-foreground">Failed</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-hidden rounded-lg border border-border">
        <div className="flex min-h-[300px] flex-col overflow-auto bg-card">
          {/* Header */}
          <div className="flex border-b border-border bg-muted/50">
            {/* Name */}
            <div className="flex flex-1 flex-col p-4">
              <span className="text-sm font-semibold">Name</span>
              <span className="text-xs text-muted-foreground">Workflow name and ID</span>
            </div>

            {/* Status */}
            <div className="flex flex-col p-4">
              <span className="text-sm font-semibold">Status</span>
              <span className="text-xs text-muted-foreground">Current execution status</span>
            </div>

            {/* Timestamps */}
            <div className="flex flex-col min-w-[200px] p-4">
              <span className="text-sm font-semibold">Created At</span>
              <span className="text-xs text-muted-foreground">Created timestamp</span>
            </div>

            {/* Updated At */}
            <div className="flex flex-col min-w-[200px] p-4">
              <span className="text-sm font-semibold">Updated At</span>
              <span className="text-xs text-muted-foreground">Last updated timestamp</span>
            </div>

            {/* Actions */}
            <div className="flex items-center p-4">
              <span className="text-sm font-semibold">Actions</span>
            </div>
          </div>

          {/* Loading State */}
          {loading ? (
            <div className="flex flex-1 items-center justify-center">
              <div className="flex items-center gap-3 rounded-lg border border-dashed bg-muted/30 p-8">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary/20 border-t-primary" />
                <span className="text-muted-foreground">Loading workflows...</span>
              </div>
            </div>
          ) : (
            /* Empty State */
            workflows.length === 0 ? (
              <div className="flex flex-1 flex-col items-center justify-center p-8 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                  <SlidersHorizontal className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="mt-4 text-lg font-semibold">No workflows found</h3>
                <p className="text-muted-foreground">
                  {emptyMessage || 'Get started by creating your first workflow.'}
                </p>
              </div>
            ) : (
              /* Workflow Rows */
              workflows.map((workflow) => (
                <WorkflowTableRow
                  key={workflow.id}
                  workflow={workflow}
                  onClick={onClick || (() => { })}
                  onRetry={onRetry}
                  onCancel={onCancel}
                />
              ))
            )
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * WorkflowTableRow component
 */
function WorkflowTableRow({
  workflow,
  onClick,
  onRetry,
  onCancel,
}: WorkflowTableRowProps) {
  const status = workflow.status as WorkflowStatusType

  return (
    <Link
      href={`/workflows/${workflow.id}`}
      onClick={(e) => {
        e.preventDefault()
        e.stopPropagation()
        onClick?.(workflow.id)
      }}
      className="group flex border-b border-border last:border-b-0 transition-colors hover:bg-accent/30"
    >
      {/* Name Column */}
      <div className="flex min-w-0 flex-col p-4 overflow-hidden">
        <div className="flex items-center gap-2 truncate">
          <div
            className={cn(
              'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg',
              status === 'running'
                ? 'bg-primary/10 text-primary'
                : status === 'failed'
                  ? 'bg-destructive/10 text-destructive'
                  : status === 'completed'
                    ? 'bg-green-500/10 text-green-700'
                    : 'bg-accent/10 text-accent-foreground',
            )}
          >
            {status === 'running' && <Play className="h-4 w-4" />}
            {status === 'completed' && <CheckCircle2 className="h-4 w-4" />}
            {status === 'failed' && <XCircle className="h-4 w-4" />}
            {status === 'cancelled' && <XCircle className="h-4 w-4" />}
            {status === 'created' && <Circle className="h-4 w-4" />}
          </div>

          <div className="flex flex-col overflow-hidden">
            <span className="truncate font-medium text-foreground">
              {workflow.name}
            </span>
            <span className="truncate text-xs text-muted-foreground">
              {workflow.workflow_id}
            </span>
          </div>
        </div>
      </div>

      {/* Status Column */}
      <div className="flex items-center justify-center p-4">
        <div
          className={cn(
            'inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold',
            status === 'completed'
              ? 'border-transparent bg-green-500/10 text-green-700'
              : status === 'failed'
                ? 'border-transparent bg-red-500/10 text-red-700'
                : status === 'cancelled'
                  ? 'border-transparent bg-amber-500/10 text-amber-700'
                  : 'border-transparent bg-primary/10 text-primary',
          )}
        >
          {status}
        </div>
      </div>

      {/* Created At Column */}
      <div className="flex items-center p-4">
        <Clock className="h-3.5 w-3.5 mr-1.5 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">
          {formatTimestamp(workflow.created_at)}
        </span>
      </div>

      {/* Updated At Column */}
      <div className="flex items-center p-4">
        <Clock className="h-3.5 w-3.5 mr-1.5 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">
          {formatTimestamp(workflow.updated_at)}
        </span>
      </div>

      {/* Actions Column */}
      <div className="flex items-center p-4">
        {status === 'running' && (
          <button
            className="flex h-8 w-8 items-center justify-center rounded-md border border-border hover:bg-accent hover:text-accent-foreground"
            title="View execution"
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
            }}
          >
            <Play className="h-4 w-4" />
          </button>
        )}
        {status === 'failed' && onRetry && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onRetry?.(workflow.id)
            }}
            className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
            title="Retry execution"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        )}
        {status === 'cancelled' && onCancel && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onCancel?.(workflow.id)
            }}
            className="flex h-8 w-8 items-center justify-center rounded-md border border-border hover:bg-accent hover:text-accent-foreground"
            title="Cancel execution"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        )}
        {status === 'completed' && (
          <span className="text-sm text-muted-foreground">✓</span>
        )}
      </div>
    </Link>
  )
}

/**
 * Workflow Table Header Component
 */
interface WorkflowTableHeaderProps {
  searchValue: string
  statusValue?: string
  setStatusValue: (value?: string) => void
  resetFilters?: () => void
  className?: string
}

export function WorkflowTableHeader({
  searchValue,
  statusValue,
  setStatusValue,
  resetFilters,
  className,
}: Pick<WorkflowTableHeaderProps, 'searchValue' | 'statusValue' | 'setStatusValue' | 'resetFilters' | 'className'>) {
  const [localSearch, setLocalSearch] = React.useState(searchValue)

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalSearch(e.target.value)
  }

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setLocalSearch(searchValue)
    }, 300)

    return () => clearTimeout(timer)
  }, [searchValue])

  React.useEffect(() => {
    if (!searchValue) {
      setLocalSearch('')
    }
  }, [searchValue])

  const handleReset = () => {
    setLocalSearch('')
    setStatusValue(undefined)
    resetFilters?.()
  }

  return (
    <div className={cn('flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between', className)}>
      {/* Search */}
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="search"
          placeholder="Search workflows..."
          value={localSearch}
          onChange={handleSearchChange}
          className="pl-9 pr-8"
        />
      </div>

      {/* Filters */}
      <div className="flex items-center justify-end gap-2">
        {/* Status Filter */}
        <div className="relative">
          <select
            value={statusValue || ''}
            onChange={(e) => {
              const value = e.target.value
              setStatusValue(value ? value : undefined)
            }}
            className="inline-flex h-9 w-[140px] items-center justify-between rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          >
            <option value="all">All Statuses</option>
            <option value="created">Created</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
            <option value="paused">Paused</option>
            <option value="resumed">Resumed</option>
            <option value="escalated">Escalated</option>
          </select>
        </div>

        {/* Reset Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={handleReset}
          className="gap-1.5"
        >
          <Filter className="h-4 w-4" />
          <span>Reset</span>
        </Button>

        {/* Close Button */}
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
