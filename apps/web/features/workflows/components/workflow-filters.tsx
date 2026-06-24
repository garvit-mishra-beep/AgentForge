/**
 * Workflow Filters Component
 *
 * Provides filtering and search controls for the workflow dashboard.
 */

'use client'

import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/loading'
import { SelectComponent } from '@/components/ui/loading'
import { Search, X, Filter } from 'lucide-react'

/**
 * Props for WorkflowFilters component
 */
export interface WorkflowFiltersProps {
  searchValue: string
  setSearchValue: (value: string) => void
  statusValue?: string
  setStatusValue: (value?: string) => void
  showFilters: boolean
  setShowFilters: (show: boolean) => void
  resetFilters?: () => void
  clearSearch?: () => void
}

/**
 * WorkflowFilters component
 */
export function WorkflowFilters({
  searchValue,
  setSearchValue,
  statusValue,
  setStatusValue,
  showFilters,
  setShowFilters,
  resetFilters,
}: WorkflowFiltersProps) {
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchValue(e.target.value)
  }

  const handleSearchClear = () => {
    setSearchValue('')
  }

  const handleReset = () => {
    setSearchValue('')
    setStatusValue(undefined)
    resetFilters?.()
  }

  if (!showFilters) {
    return null
  }

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      {/* Search */}
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="search"
          placeholder="Search workflows..."
          value={searchValue}
          onChange={handleSearchChange}
          className="pl-9 pr-8"
        />
        {searchValue && (
          <button
            onClick={handleSearchClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 rounded p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex items-center justify-end gap-2">
        {/* Status Filter - using simple select */}
        <SelectComponent value={statusValue || ''} onChange={setStatusValue}>
          <option value="all">All Statuses</option>
          <option value="created">Created</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
          <option value="paused">Paused</option>
          <option value="escalated">Escalated</option>
        </SelectComponent>

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
          onClick={() => setShowFilters(false)}
          className="h-8 w-8"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
