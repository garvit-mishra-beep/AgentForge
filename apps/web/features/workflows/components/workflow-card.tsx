/**
 * Workflow Card Component
 *
 * Card component for displaying workflow information in a grid layout.
 */

'use client'

import * as React from 'react'
import Link from 'next/link'
import { cn } from '@/lib/utils'
import { StatusBadge } from '@/components/ui/status-badge'
import {
  CheckCircle2,
  Circle,
  XCircle,
  RotateCcw,
  Play,
  Pause,
} from 'lucide-react'
import type { Workflow } from '@/types/workflow'

/**
 * Props for WorkflowCard component
 */
interface WorkflowCardProps {
  workflow: Workflow
  showActions?: boolean
  onRetry?: (workflowId: string) => void
  onCancel?: (workflowId: string) => void
  className?: string
}

/**
 * Props for WorkflowCardCompact component
 */
interface WorkflowCardCompactProps {
  workflow: Workflow
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
 * WorkflowCard component
 */
export function WorkflowCard({
  workflow,
  showActions = true,
  onRetry,
  onCancel,
  className,
}: WorkflowCardProps) {
  return (
    <Link
      href={`/workflows/${workflow.id}`}
      className={cn(
        'group relative flex flex-col justify-between overflow-hidden rounded-xl border bg-card transition-all hover:border-primary/50 hover:shadow-lg',
        workflow.status === 'failed'
          ? 'border-destructive/50'
          : 'border-border',
        className,
      )}
    >
      {/* Status Badge */}
      <div className="absolute right-3 top-3 z-10">
        <StatusBadge
          variant={
            workflow.status === 'completed'
              ? 'success'
              : workflow.status === 'failed'
                ? 'destructive'
                : workflow.status === 'cancelled'
                  ? 'warning'
                  : 'default'
          }
        >
          {workflow.status}
        </StatusBadge>
      </div>

      {/* Left Icon */}
      <div
        className={cn(
          'flex h-12 w-12 items-center justify-center rounded-xl transition-colors group-hover:scale-105',
          workflow.status === 'running'
            ? 'bg-primary/10 text-primary'
            : workflow.status === 'failed'
              ? 'bg-destructive/10 text-destructive'
              : workflow.status === 'completed'
                ? 'bg-green-500/10 text-green-700'
                : 'bg-accent/10 text-accent-foreground',
        )}
      >
        {workflow.status === 'running' && <Play className="h-5 w-5 animate-pulse" />}
        {workflow.status === 'completed' && <CheckCircle2 className="h-5 w-5" />}
        {workflow.status === 'failed' && <XCircle className="h-5 w-5" />}
        {workflow.status === 'cancelled' && <XCircle className="h-5 w-5" />}
        {workflow.status === 'paused' && <Pause className="h-5 w-5" />}
        {workflow.status === 'created' && <Circle className="h-5 w-5" />}
      </div>

      {/* Content */}
      <div className="flex-1 p-4">
        {/* Name */}
        <h3 className="font-semibold text-foreground line-clamp-1">
          {workflow.name}
        </h3>

        {/* Workflow ID */}
        <p className="mt-1 text-xs font-mono text-muted-foreground">
          {workflow.workflow_id}
        </p>

        {/* Description */}
        {workflow.description && (
          <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">
            {workflow.description}
          </p>
        )}

      </div>

      {/* Footer */}
      <div className="flex items-center justify-between border-t pt-3 text-xs text-muted-foreground">
        {/* Agent Type */}
        {workflow.agent_type && (
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
            {workflow.agent_type}
          </span>
        )}

        {/* Updated At */}
        <span>
          Updated: {formatTimestamp(workflow.updated_at)}
        </span>
      </div>

      {/* Actions */}
      {showActions && (
        <div
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
          }}
          className={cn(
            'absolute right-3 top-14 flex items-center gap-1 rounded-lg border bg-background p-1.5 transition-all opacity-0 group-hover:opacity-100',
            'shadow-md',
          )}
        >
          {workflow.status === 'running' && (
            <button
              className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-muted"
              title="View execution"
            >
              <Play className="h-4 w-4" />
            </button>
          )}
          {workflow.status === 'failed' && onRetry && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onRetry(workflow.id)
              }}
              className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
              title="Retry execution"
            >
              <RotateCcw className="h-4 w-4" />
            </button>
          )}
          {workflow.status === 'cancelled' && onCancel && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onCancel(workflow.id)
              }}
              className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-muted"
              title="Cancel execution"
            >
              <RotateCcw className="h-4 w-4" />
            </button>
          )}
        </div>
      )}
    </Link>
  )
}

/**
 * Compact workflow card for list views
 */
interface WorkflowCardCompactProps {
  workflow: Workflow
  onRetry?: (workflowId: string) => void
  onCancel?: (workflowId: string) => void
  className?: string
}

export function WorkflowCardCompact({
  workflow,
  onRetry,
  onCancel,
  className,
}: WorkflowCardCompactProps) {
  return (
    <Link
      href={`/workflows/${workflow.id}`}
      className={cn(
        'flex cursor-pointer items-center gap-4 rounded-lg border px-3 py-2.5 transition-colors hover:bg-accent/50',
        workflow.status === 'failed'
          ? 'border-destructive/50 hover:bg-destructive/10'
          : 'border-border',
        className,
      )}
    >
      {/* Status Icon */}
      <div
        className={cn(
          'flex h-9 w-9 shrink-0 items-center justify-center rounded-lg',
          workflow.status === 'running'
            ? 'bg-primary/10 text-primary'
            : workflow.status === 'failed'
              ? 'bg-destructive/10 text-destructive'
              : workflow.status === 'completed'
                ? 'bg-green-500/10 text-green-700'
                : 'bg-accent/10 text-accent-foreground',
        )}
      >
        {workflow.status === 'running' && <Play className="h-4 w-4" />}
        {workflow.status === 'completed' && <CheckCircle2 className="h-4 w-4" />}
        {workflow.status === 'failed' && <XCircle className="h-4 w-4" />}
        {workflow.status === 'cancelled' && <XCircle className="h-4 w-4" />}
        {workflow.status === 'paused' && <Pause className="h-4 w-4" />}
        {workflow.status === 'created' && <Circle className="h-4 w-4" />}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        <div className="flex items-center justify-between">
          <h4 className="truncate font-medium text-foreground">
            {workflow.name}
          </h4>
          <StatusBadge
            variant={
              workflow.status === 'completed'
                ? 'success'
                : workflow.status === 'failed'
                  ? 'destructive'
                  : workflow.status === 'cancelled'
                    ? 'warning'
                    : 'default'
            }
          >
            {workflow.status}
          </StatusBadge>
        </div>
        <p className="truncate text-xs text-muted-foreground">
          {workflow.workflow_id}
        </p>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1">
        {workflow.status === 'failed' && onRetry && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onRetry(workflow.id)
            }}
            className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-muted"
            title="Retry"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        )}
        {workflow.status === 'cancelled' && onCancel && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onCancel(workflow.id)
            }}
            className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-muted"
            title="Cancel"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        )}
      </div>
    </Link>
  )
}
