/**
 * Workflows Dashboard Page
 *
 * Main page for listing, filtering, and creating workflows.
 */

'use client'

import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { useRouter } from 'next/navigation'
import {
  LayoutDashboard,
  Workflow,
  CheckCircle2,
  Clock,
  Loader2,
  Plus,
  ArrowRight,
  TrendingUp,
  Award,
} from 'lucide-react'
import { useAuthStore } from '@/stores/auth-store'
import { WorkflowFilters } from '../../features/workflows/components/workflow-filters'
import { WorkflowTable } from '../../features/workflows/components/workflow-table'
import { useWorkflows } from '../../features/workflows/hooks/use-workflows'
import { createWorkflow } from '../../features/workflows/services/workflow-api'
import { Button } from '@/components/ui/loading'

// ===============================
// KPI SUMMARY CHARTS
// ===============================
const ExecutionThroughputChart = () => {
  const data = [
    { day: 'Mon', count: 12 },
    { day: 'Tue', count: 19 },
    { day: 'Wed', count: 15 },
    { day: 'Thu', count: 24 },
    { day: 'Fri', fill: true, count: 18 },
    { day: 'Sat', count: 8 },
    { day: 'Sun', count: 6 },
  ];
  const maxVal = 25;

  return (
    <div className="bg-card border rounded-xl p-5 shadow-sm flex flex-col justify-between h-[180px]">
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
          <TrendingUp className="h-3.5 w-3.5 text-primary" />
          <span>Execution Throughput</span>
        </h4>
        <p className="text-2xl font-bold mt-1 text-foreground">102 <span className="text-xs font-normal text-muted-foreground">runs this week</span></p>
      </div>
      <div className="flex items-end justify-between h-20 pt-2 gap-2">
        {data.map((d, idx) => {
          const heightPct = (d.count / maxVal) * 100;
          return (
            <div key={idx} className="flex flex-col items-center gap-1.5 flex-1 group">
              <div className="w-full flex justify-center text-[9px] font-semibold text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                {d.count}
              </div>
              <div className="w-full bg-muted rounded-t-md h-12 flex items-end relative overflow-hidden">
                <div 
                  style={{ height: `${heightPct}%` }}
                  className="w-full bg-gradient-to-t from-primary to-cyan-400 rounded-t-md group-hover:brightness-110 transition-all duration-500"
                />
              </div>
              <span className="text-[9px] text-muted-foreground font-semibold">{d.day}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const SuccessRatioRing = () => {
  const pct = 94;
  const radius = 30;
  const circ = 2 * Math.PI * radius;
  const strokeDashoffset = circ - (pct / 100) * circ;

  return (
    <div className="bg-card border rounded-xl p-5 shadow-sm flex items-center justify-between h-[180px]">
      <div className="space-y-1.5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
          <Award className="h-3.5 w-3.5 text-green-500" />
          <span>Agent Success Rate</span>
        </h4>
        <div className="flex items-baseline gap-1">
          <span className="text-2xl font-bold text-foreground">94.2%</span>
          <span className="text-xs text-green-600 font-semibold">+1.8%</span>
        </div>
        <p className="text-[10px] text-muted-foreground leading-normal max-w-[160px]">
          98 out of 102 developer agent nodes executed successfully without manual escalation.
        </p>
      </div>
      <div className="relative flex items-center justify-center shrink-0 ml-2">
        <svg width="76" height="76" viewBox="0 0 80 80" className="transform -rotate-90">
          <circle cx="40" cy="40" r={radius} fill="none" stroke="#f1f5f9" strokeWidth="6" />
          <circle 
            cx="40" 
            cy="40" 
            r={radius} 
            fill="none" 
            stroke="url(#grad-green)" 
            strokeWidth="6" 
            strokeDasharray={circ} 
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000"
          />
          <defs>
            <linearGradient id="grad-green" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#34d399" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute text-xs font-bold text-foreground">
          {pct}%
        </div>
      </div>
    </div>
  );
};


export default function WorkflowsPage() {
  const router = useRouter()
  const { isLoading: authLoading } = useAuthStore()
  const {
    workflows,
    filteredCount,
    totalWorkflows,
    isLoading: apiLoading,
    error,
    filters,
    clearFilters,
    refreshWorkflows,
  } = useWorkflows()

  // Local state for filters & search
  const [showFilters, setShowFilters] = useState(false)
  const [searchValue, setSearchValue] = useState(filters.search || '')
  const [statusValue, setStatusValue] = useState(filters.status)

  // Creation modal state
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [newWorkflowId, setNewWorkflowId] = useState('')
  const [newName, setNewName] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [newPrompt, setNewPrompt] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  // Fetch workflows on load
  useEffect(() => {
    refreshWorkflows().catch(() => {})
  }, [refreshWorkflows])

  const isLoading = authLoading || apiLoading
  const hasResults = !isLoading && workflows.length > 0
  const emptyMessage = error
    ? `Error: ${error}. Please try again later.`
    : 'No workflows found. Get started by creating a new workflow!'

  const handleCreateWorkflow = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newWorkflowId || !newName || !newPrompt) {
      setSubmitError('Please fill out all required fields.')
      return
    }

    setIsSubmitting(true)
    setSubmitError(null)

    try {
      const created = await createWorkflow({
        workflow_id: newWorkflowId.trim(),
        name: newName.trim(),
        description: newDescription.trim(),
        agent_type: 'planner',
        inputs: {
          prompt: newPrompt.trim(),
          requirements: [
            { name: 'Architecture & Endpoint Design', description: newPrompt.trim(), effort: '2h' }
          ]
        },
        output_schema: {}
      })

      setIsCreateOpen(false)
      // Reset form
      setNewWorkflowId('')
      setNewName('')
      setNewDescription('')
      setNewPrompt('')

      await refreshWorkflows()
      router.push(`/workflows/${created.workflow_id}`)
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to create workflow')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center justify-between border-b pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Workflows Dashboard</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Orchestrate and track your autonomous developer agents
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="default"
            onClick={() => setIsCreateOpen(true)}
            className="gap-2 shadow-md hover:shadow-lg transition-all"
          >
            <Plus className="h-4 w-4" />
            <span>New Workflow</span>
          </Button>

          <span
            className={cn(
              'inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm bg-card font-medium',
              error
                ? 'border-destructive/20 text-destructive bg-destructive/5'
                : 'border-border text-foreground',
            )}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                <span>Loading...</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span>{filteredCount} Active</span>
              </>
            )}
          </span>
        </div>
      </div>

      {/* Analytics Panels */}
      <div className="grid gap-6 md:grid-cols-2">
        <ExecutionThroughputChart />
        <SuccessRatioRing />
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
          onClick={(id) => router.push(`/workflows/${id}`)}
          className="min-h-[400px]"
        />
      )}

      {/* Empty State */}
      {!hasResults && !isLoading && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card p-12 text-center shadow-sm">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 mb-4">
            <Workflow className="h-8 w-8 text-primary" />
          </div>
          <h3 className="text-lg font-semibold">No workflows found</h3>
          <p className="text-muted-foreground mt-1 max-w-sm text-sm">
            Configure your first agent workflow to start planning and building software modules.
          </p>
          <div className="mt-6 flex gap-3">
            <Button
              onClick={() => setIsCreateOpen(true)}
              className="gap-1.5"
            >
              <Plus className="h-4 w-4" />
              <span>Create Workflow</span>
            </Button>
            <Button
              variant="outline"
              onClick={refreshWorkflows}
            >
              Refresh List
            </Button>
          </div>
        </div>
      )}

      {/* Footer Stats */}
      {hasResults && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between rounded-xl border bg-card p-4 gap-4 text-sm shadow-sm">
          <div className="flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                <LayoutDashboard className="h-4 w-4 text-primary" />
              </div>
              <div>
                <div className="font-semibold">{totalWorkflows}</div>
                <div className="text-xs text-muted-foreground">Total Definitions</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-green-500/10">
                <div className="h-2 w-2 animate-pulse rounded-full bg-green-600" />
              </div>
              <div>
                <div className="font-semibold text-green-700">
                  {workflows.filter((w: any) => w.status === 'running').length}
                </div>
                <div className="text-xs text-muted-foreground">Running Executions</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10">
                <CheckCircle2 className="h-4 w-4 text-blue-600" />
              </div>
              <div>
                <div className="font-semibold text-blue-700">
                  {workflows.filter((w: any) => w.status === 'completed').length}
                </div>
                <div className="text-xs text-muted-foreground">Completed</div>
              </div>
            </div>
          </div>

          <button
            onClick={refreshWorkflows}
            className="flex items-center gap-2 rounded-lg border border-border px-3 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground transition-colors self-end sm:self-auto"
          >
            <Clock className="h-4 w-4" />
            <span>Refresh</span>
          </button>
        </div>
      )}

      {/* Create Workflow Dialog Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg rounded-xl border bg-card p-6 shadow-2xl space-y-4 animate-scale-in">
            <div className="space-y-1">
              <h2 className="text-xl font-bold">Create Workflow Definition</h2>
              <p className="text-sm text-muted-foreground">
                Set up requirement inputs for your multi-agent implementation pipeline.
              </p>
            </div>

            <form onSubmit={handleCreateWorkflow} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-semibold">Workflow ID *</label>
                <input
                  type="text"
                  placeholder="e.g. auth-service"
                  value={newWorkflowId}
                  onChange={(e) => setNewWorkflowId(e.target.value.replace(/[^a-zA-Z0-9-_]/g, ''))}
                  className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-semibold">Workflow Name *</label>
                <input
                  type="text"
                  placeholder="e.g. Authentication Handler"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-semibold">Description (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Implement registration and token validates"
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-semibold">Agent Instruction / Prompt *</label>
                <textarea
                  placeholder="e.g. Create a Python auth class with login method, validate username and password, return JWT token. Write tests covering successful and failed scenarios."
                  value={newPrompt}
                  onChange={(e) => setNewPrompt(e.target.value)}
                  rows={4}
                  className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  required
                />
              </div>

              {submitError && (
                <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive border border-destructive/20">
                  {submitError}
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-accent"
                >
                  Cancel
                </button>
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="gap-1.5"
                >
                  {isSubmitting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <ArrowRight className="h-4 w-4" />
                  )}
                  <span>{isSubmitting ? 'Building...' : 'Build Workflow'}</span>
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
