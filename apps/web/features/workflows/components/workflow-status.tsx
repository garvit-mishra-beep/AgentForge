/**
 * Workflow Status Component
 *
 * Displays workflow execution status with appropriate icon and styling.
 */

'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'
import { StatusBadge } from '@/components/ui/status-badge'
import { CheckCircle2, Circle, AlertTriangle, XCircle, Pause, RotateCcw, ChevronRight } from 'lucide-react'

// Workflow status variants - simplified without status config

interface WorkflowStatusProps {
  status: 'created' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused' | 'resumed' | 'escalated'
  withDescription?: boolean
  compact?: boolean
  className?: string
}

export function WorkflowStatus({
  status,
  withDescription = false,
  compact = false,
  className,
}: WorkflowStatusProps) {
  return (
    <StatusBadge
      variant="default"
      className={cn('gap-1.5', className)}
    >
      {status}
      {!compact && withDescription && (
        <span className="ml-1.5 text-[0.625rem] opacity-70">
          Running
        </span>
      )}
    </StatusBadge>
  )
}

interface WorkflowStatusCardProps {
  status: 'created' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused' | 'resumed' | 'escalated'
  name?: string
  workflowId?: string
  description?: string
  retryCount?: number
  onRetry?: () => void
  onCancel?: () => void
  onClick?: () => void
  className?: string
}

export function WorkflowStatusCard({
  status,
  name,
  workflowId,
  description,
  retryCount = 0,
  onRetry,
  onCancel,
  onClick,
  className,
}: WorkflowStatusCardProps) {

  return (
    <div
      onClick={onClick}
      className={cn(
        'rounded-lg border bg-card p-4 transition-all hover:border-primary/50',
        status === 'failed' ? 'border-destructive/50' : 'border-border',
        className,
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              'flex h-10 w-10 items-center justify-center rounded-lg',
              status === 'running'
                ? 'bg-primary/10 text-primary'
                : status === 'failed'
                  ? 'bg-destructive/10 text-destructive'
                  : status === 'completed'
                    ? 'bg-green-500/10 text-green-700'
                    : 'bg-accent/10 text-accent-foreground',
            )}
          >
            {status === 'running' && <div className="h-2 w-2 animate-ring rounded-full bg-current" />}
            {status === 'created' && <Circle className="h-5 w-5" />}
            {status === 'completed' && <CheckCircle2 className="h-5 w-5" />}
            {status === 'failed' && <XCircle className="h-5 w-5" />}
            {status === 'cancelled' && <XCircle className="h-5 w-5" />}
            {status === 'paused' && <Pause className="h-5 w-5" />}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-foreground">{name || workflowId}</h3>
              <WorkflowStatus status={status} compact />
            </div>
            {description && (
              <p className="text-sm text-muted-foreground mt-0.5">{description}</p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1">
          {status === 'failed' && onRetry && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onRetry?.()
              }}
              className="flex h-8 w-8 items-center justify-center rounded-md border bg-background hover:bg-accent hover:text-accent-foreground"
              aria-label="Retry execution"
            >
              <RotateCcw className="h-4 w-4" />
            </button>
          )}
          {status === 'cancelled' && onCancel && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onCancel?.()
              }}
              className="flex h-8 w-8 items-center justify-center rounded-md border bg-background hover:bg-accent hover:text-accent-foreground"
              aria-label="Cancel execution"
            >
              <ChevronRight className="h-4 w-4 rotate-45" />
            </button>
          )}
        </div>
      </div>

      {/* Retry Info */}
      {retryCount > 0 && (
        <div className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
          <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
          <span>Retried {retryCount} time{retryCount > 1 ? 's' : ''}</span>
        </div>
      )}
    </div>
  )
}
