"use client";

import { Suspense, useEffect, useState, useCallback, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@radix-ui/react-dialog";
import { listTeams, listTasks, createTask, listProjects } from "@/lib/api";
import type { Task, Team, Project } from "@/lib/types";
import {
  Loader2, Sparkles, Send, CheckCircle2, XCircle, RefreshCw, Clock,
  ChevronRight, Plus, Search, X, Filter,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/toast";

const TASK_EXAMPLES = [
  "Build JWT Authentication in FastAPI",
  "Create REST CRUD API for Tasks",
  "Design PostgreSQL schema for e-commerce",
  "Build React DataTable component in TypeScript",
  "Write pytest test suite for auth module",
];

const STATUS_OPTIONS = ["all", "pending", "running", "completed", "failed"] as const;

function TaskCard({ task }: { task: Task }) {
  const statusConfig = {
    completed: { label: "Completed", color: "success" as const, Icon: CheckCircle2 },
    running: { label: "Running", color: "warning" as const, Icon: RefreshCw },
    failed: { label: "Failed", color: "destructive" as const, Icon: XCircle },
    pending: { label: "Pending", color: "secondary" as const, Icon: Clock },
  }[task.status];

  return (
    <Link href={`/tasks/${task.id}`} className="block group">
      <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-3 transition-all hover:border-border-hover hover:bg-surface-hover">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-sm font-medium truncate group-hover:text-primary transition-colors">{task.title}</span>
            <Badge variant={statusConfig.color} className="shrink-0">
              <statusConfig.Icon className={cn("h-3 w-3 mr-1", task.status === "running" && "animate-spin")} />
              {statusConfig.label}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground truncate">{task.description}</p>
        </div>
        <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors shrink-0" />
      </div>
    </Link>
  );
}

function NewTaskDialog({
  open, onOpenChange, teams, onCreated,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  teams: Team[];
  onCreated: () => void;
}) {
  const router = useRouter();
  const { toast } = useToast();
  const [selectedTeam, setSelectedTeam] = useState("");
  const [selectedProject, setSelectedProject] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [fastDemo, setFastDemo] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const readyTeams = teams.filter((t) => t.members.length >= 2);

  useEffect(() => {
    if (open) {
      setSelectedTeam("");
      setSelectedProject("");
      setFastDemo(false);
      setTitle("");
      setDescription("");
      listProjects().then(setProjects).catch(() => {});
    }
  }, [open]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selectedTeam || !title.trim()) return;
    setBusy(true);
    try {
      const task = await createTask({
        team_id: selectedTeam,
        title: title.trim(),
        description: description.trim() || title.trim(),
        project_id: selectedProject || undefined,
      });
      // Optionally save Fast Demo Mode preference locally
      if (fastDemo) {
        localStorage.setItem(`task_fast_demo_${task.id}`, "true");
      }
      toast("Task created", { type: "success", description: `"${title.trim()}" has been submitted.` });
      onOpenChange(false);
      onCreated();
      router.push(`/tasks/${task.id}`);
    } catch {
      toast("Failed to create task", { type: "error", description: "Check API connection." });
    } finally { setBusy(false); }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => onOpenChange(false)}>
        <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <h2 className="text-sm font-semibold">New Task</h2>
            </div>
            <button onClick={() => onOpenChange(false)} className="text-muted-foreground hover:text-foreground cursor-pointer">
              <X className="h-4 w-4" />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs text-muted-foreground mb-1.5 block font-medium">Select Team</label>
              {readyTeams.length === 0 ? (
                <div className="text-xs text-muted-foreground rounded-lg border border-border bg-surface/50 px-3 py-2">
                  No complete teams available.{" "}
                  <Link href="/teams" className="text-primary hover:underline">Create one first</Link>
                </div>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {readyTeams.map((team) => (
                    <button
                      key={team.id}
                      type="button"
                      onClick={() => setSelectedTeam(team.id)}
                      className={cn(
                        "rounded-lg border px-3 py-1.5 text-xs font-medium transition-all cursor-pointer",
                        selectedTeam === team.id
                          ? "border-primary bg-primary-muted text-primary"
                          : "border-border text-muted-foreground hover:border-border-hover hover:text-foreground",
                      )}
                    >
                      {team.name}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div>
              <label className="text-xs text-muted-foreground mb-1.5 block font-medium">Select Project (optional)</label>
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none focus:border-primary/50 transition-colors cursor-pointer"
              >
                <option value="">None (Standalone Task)</option>
                {projects.map((proj) => (
                  <option key={proj.id} value={proj.id}>
                    {proj.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs text-muted-foreground mb-1.5 block font-medium">Task Title</label>
              <Input placeholder="e.g., Build JWT Authentication" value={title} onChange={(e) => setTitle(e.target.value)} className="text-sm" />
              <div className="flex flex-wrap gap-1.5 mt-2">
                {TASK_EXAMPLES.filter((e) => !title || e.toLowerCase().includes(title.toLowerCase())).slice(0, 3).map((ex) => (
                  <button
                    key={ex}
                    type="button"
                    onClick={() => setTitle(ex)}
                    className="rounded-md border border-border px-2 py-0.5 text-[10px] text-muted-foreground hover:text-foreground hover:border-border-hover transition-colors cursor-pointer"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-xs text-muted-foreground mb-1.5 block font-medium">Description (optional)</label>
              <textarea
                placeholder="Add more details..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-foreground transition-colors placeholder:text-muted-foreground/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
              />
            </div>

            <div className="flex items-center justify-between rounded-lg border border-border bg-surface/30 px-3 py-2">
              <div>
                <label className="text-xs font-semibold text-foreground block">Fast Demo Mode</label>
                <span className="text-[10px] text-muted-foreground">Skip review loops and cap agent runs for quick validation</span>
              </div>
              <input
                type="checkbox"
                checked={fastDemo}
                onChange={(e) => setFastDemo(e.target.checked)}
                className="h-4 w-4 rounded border-border bg-surface text-primary focus:ring-primary focus:ring-offset-background cursor-pointer"
              />
            </div>

            <Button type="submit" disabled={busy || !selectedTeam || !title.trim()} className="w-full">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              {busy ? "Starting..." : "Start Task"}
            </Button>
          </form>
        </div>
      </div>
    </Dialog>
  );
}

function TasksPageInner() {
  const { toast } = useToast();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);

  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [filterTeam, setFilterTeam] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [t, tms] = await Promise.all([listTasks(), listTeams()]);
      setTasks(t);
      setTeams(tms);
    } catch {
      toast("Failed to load data", { type: "error", description: "Check API connection." });
    } finally { setLoading(false); }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  const filteredTasks = tasks.filter((task) => {
    if (filterStatus !== "all" && task.status !== filterStatus) return false;
    if (filterTeam !== "all" && task.team_id !== filterTeam) return false;
    if (searchQuery && !task.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const hasFilters = filterStatus !== "all" || filterTeam !== "all" || searchQuery !== "";

  return (
    <div className="space-y-6 animate-fade-in">
      <NewTaskDialog
        open={showNew}
        onOpenChange={setShowNew}
        teams={teams}
        onCreated={load}
      />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Tasks</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Describe what you want built and watch your AI team deliver
          </p>
        </div>
        <Button onClick={() => setShowNew(true)}>
          <Plus className="h-4 w-4" />
          New Task
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            placeholder="Search tasks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-border bg-surface pl-8 pr-3 py-2 text-xs text-foreground placeholder:text-muted-foreground/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>

        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="rounded-lg border border-border bg-surface px-3 py-2 text-xs text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer"
        >
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{s === "all" ? "All Status" : s.charAt(0).toUpperCase() + s.slice(1)}</option>
          ))}
        </select>

        <select
          value={filterTeam}
          onChange={(e) => setFilterTeam(e.target.value)}
          className="rounded-lg border border-border bg-surface px-3 py-2 text-xs text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer"
        >
          <option value="all">All Teams</option>
          {teams.map((t) => (
            <option key={t.id} value={t.id}>{t.name}</option>
          ))}
        </select>

        {hasFilters && (
          <button
            onClick={() => { setFilterStatus("all"); setFilterTeam("all"); setSearchQuery(""); }}
            className="flex items-center gap-1 rounded-lg border border-border px-3 py-2 text-xs text-muted-foreground hover:text-foreground hover:border-border-hover transition-colors cursor-pointer"
          >
            <X className="h-3 w-3" />
            Clear
          </button>
        )}
        <span className="text-[10px] text-muted-foreground ml-auto">
          {filteredTasks.length} / {tasks.length} tasks
        </span>
      </div>

      {/* Task List */}
      <div>
        {loading ? (
          <div className="flex items-center justify-center py-12 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin mr-2" />
            Loading tasks...
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-primary-muted">
              {hasFilters ? <Filter className="h-5 w-5 text-primary" /> : <Sparkles className="h-5 w-5 text-primary" />}
            </div>
            <h3 className="text-sm font-semibold mb-1">{hasFilters ? "No matching tasks" : "No tasks yet"}</h3>
            <p className="text-xs text-muted-foreground max-w-xs">
              {hasFilters ? "Try adjusting your filters." : "Pick a team, describe what you need, and watch your AI agents collaborate."}
            </p>
          </div>
        ) : (
          <div className="space-y-1.5">
            {filteredTasks.map((task) => (
              <TaskCard key={task.id} task={task} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function TasksPage() {
  return (
    <Suspense fallback={<div className="text-sm text-muted-foreground py-8 text-center">Loading...</div>}>
      <TasksPageInner />
    </Suspense>
  );
}
