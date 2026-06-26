"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { listTeams, listTasks, createTask } from "@/lib/api";
import type { Task, Team } from "@/lib/types";
import { Loader2, Sparkles, Send, CheckCircle2, XCircle, RefreshCw, Clock, Plus, ChevronRight, Play } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { useToast } from "@/components/ui/toast";

const TASK_EXAMPLES = [
  "Build JWT Authentication in FastAPI",
  "Create REST CRUD API for Tasks",
  "Design PostgreSQL schema for e-commerce",
  "Build React DataTable component in TypeScript",
  "Write pytest test suite for auth module",
];

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

function TasksPageInner() {
  const { toast } = useToast();
  const searchParams = useSearchParams();
  const preselectedTeam = searchParams.get("team") ?? "";

  const [tasks, setTasks] = useState<Task[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState(preselectedTeam);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const [t, tms] = await Promise.all([listTasks(), listTeams()]);
      setTasks(t);
      setTeams(tms);
    } catch {
      toast("Failed to load data", { type: "error", description: "Check API connection." });
    }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedTeam || !title.trim()) return;
    setBusy(true);
    try {
      await createTask({ team_id: selectedTeam, title: title.trim(), description: description.trim() || title.trim() });
      toast("Task created", { type: "success", description: `"${title.trim()}" has been submitted.` });
      setTitle(""); setDescription("");
      await load();
    } catch (err) {
      toast("Failed to create task", { type: "error", description: "Check API connection." });
    }
    finally { setBusy(false); }
  }

  const readyTeams = teams.filter((t) => t.members.length >= 2);

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Tasks</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Describe what you want built and watch your AI team deliver
          </p>
        </div>
      </div>

      {/* Create Task */}
      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            New Task
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs text-muted-foreground mb-1.5 block font-medium">Select Team</label>
              {readyTeams.length === 0 ? (
                <div className="text-xs text-muted-foreground rounded-lg border border-border bg-surface/50 px-3 py-2">
                  No complete teams available.{' '}
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
                      <span className="ml-1.5 opacity-60">
                        ({team.members.map((m) => m.model.split(":")[0]).join(", ")})
                      </span>
                    </button>
                  ))}
                </div>
              )}
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
                rows={3}
                className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-foreground transition-colors placeholder:text-muted-foreground/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
              />
            </div>

            <Button type="submit" disabled={busy || !selectedTeam || !title.trim()}>
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              {busy ? "Starting..." : "Start Task"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Task List */}
      <div>
        <h2 className="text-sm font-semibold mb-3">
          Recent Tasks
          {tasks.length > 0 && <span className="text-muted-foreground font-normal ml-1">({tasks.length})</span>}
        </h2>

        {loading ? (
          <div className="flex items-center justify-center py-12 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin mr-2" />
            Loading tasks...
          </div>
        ) : tasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-primary-muted">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <h3 className="text-sm font-semibold mb-1">No tasks yet</h3>
            <p className="text-xs text-muted-foreground max-w-xs">Pick a team, describe what you need, and watch your AI agents collaborate.</p>
          </div>
        ) : (
          <div className="space-y-1.5">
            {tasks.map((task) => (
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
