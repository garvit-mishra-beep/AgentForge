"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { MetricCard } from "@/components/metric-card";
import { AgentNetwork } from "@/components/agent-network";
import { QuickReviewTextarea } from "@/components/QuickReviewTextarea";
import { QuickReviewProgress } from "@/components/QuickReviewProgress";
import { QuickReviewResults } from "@/components/QuickReviewResults";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { listTeams, listTasks, listExecutions, submitReview, pollReview } from "@/lib/api";
import type { Team, Task, Execution, ReviewResult, ReviewRecord, ReviewStatus } from "@/lib/types";
import type { AgentRole, AgentStatus } from "@/lib/constants";
import {
  Users, ListChecks, Activity, Zap, ArrowRight, Play, Plus, Clock,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

export default function Dashboard() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);

  const [reviewState, setReviewState] = useState<"idle" | "busy" | "done" | "error">("idle");
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus>("queued");
  const [reviewResult, setReviewResult] = useState<ReviewResult | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [reviewElapsed, setReviewElapsed] = useState(0);
  const [reviewHistory, setReviewHistory] = useState<ReviewRecord[]>([]);
  const reviewIdRef = useRef<string | null>(null);

  useEffect(() => {
    listTeams().catch(() => [] as Team[]).then(setTeams);
    listTasks().catch(() => [] as Task[]).then(setTasks);
    listExecutions().catch(() => [] as Execution[]).then(setExecutions).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (reviewState !== "busy") return;
    const interval = setInterval(() => setReviewElapsed((v) => v + 1), 1000);
    return () => clearInterval(interval);
  }, [reviewState]);

  const handleReview = useCallback(async (code: string) => {
    setReviewState("busy");
    setReviewElapsed(0);
    setReviewError(null);
    setReviewResult(null);
    setReviewStatus("queued");

    try {
      const created = await submitReview({ code });
      reviewIdRef.current = created.review_id;

      const result = await pollReview(
        created.review_id,
        (status) => setReviewStatus(status as ReviewStatus),
        2000,
        120000,
      );

      setReviewResult(result);
      setReviewState("done");

      setReviewHistory((prev) => {
        const next: ReviewRecord = {
          review_id: result.review_id,
          code: code.slice(0, 200),
          language: "detected",
          issues: result.issues.length,
          summary: result.summary,
          timestamp: Date.now(),
        };
        return [next, ...prev].slice(0, 10);
      });
    } catch (e) {
      setReviewError(e instanceof Error ? e.message : "Review failed");
      setReviewState("error");
    }
  }, []);

  const handleReviewAnother = useCallback(() => {
    setReviewState("idle");
    setReviewResult(null);
    setReviewError(null);
    setReviewElapsed(0);
    setReviewStatus("queued");
    reviewIdRef.current = null;
  }, []);

  const handleSelectHistory = useCallback((record: ReviewRecord) => {
    handleReview(record.code);
  }, [handleReview]);

  const activeTeams = teams.filter((t) => t.members.length >= 2);
  const runningTasks = tasks.filter((t) => t.status === "running");
  const completedTasks = tasks.filter((t) => t.status === "completed");

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Mission Control</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {activeTeams.length} active teams &middot; {runningTasks.length} running tasks
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/teams">
            <Button size="sm" variant="secondary">
              <Plus className="h-3.5 w-3.5" />
              New Team
            </Button>
          </Link>
          <Link href="/tasks">
            <Button size="sm">
              <Play className="h-3.5 w-3.5" />
              New Task
            </Button>
          </Link>
        </div>
      </div>

      {/* Quick Review */}
      <section className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary-muted">
            <Zap className="h-3.5 w-3.5 text-primary" />
          </div>
          <div>
            <h2 className="text-sm font-semibold">Quick Review</h2>
            <p className="text-[11px] text-muted-foreground">
              Multi-agent code review &mdash; paste any AI-generated code
            </p>
          </div>
        </div>

        {reviewState === "idle" && (
          <QuickReviewTextarea onReview={handleReview} busy={false} />
        )}
        {reviewState === "busy" && (
          <QuickReviewProgress status={reviewStatus} elapsed={reviewElapsed} />
        )}
        {reviewState === "error" && (
          <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
            <p className="text-sm font-medium text-destructive mb-1">Review failed</p>
            <p className="text-xs text-muted-foreground">{reviewError}</p>
            <Button onClick={handleReviewAnother} variant="outline" size="sm" className="mt-3">
              Try again
            </Button>
          </div>
        )}
        {reviewState === "done" && reviewResult && (
          <QuickReviewResults
            result={reviewResult}
            history={reviewHistory}
            onReviewAnother={handleReviewAnother}
            onSelectHistory={handleSelectHistory}
          />
        )}
      </section>

      {/* Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <MetricCard icon={Users} label="Active Teams" value={activeTeams.length} sublabel={`${teams.length} total`} />
        <MetricCard icon={ListChecks} label="Total Tasks" value={tasks.length} sublabel={`${completedTasks.length} completed`} />
        <MetricCard icon={Activity} label="Running" value={runningTasks.length} sublabel="Active now" />
        <MetricCard icon={Zap} label="Executions" value={executions.length} sublabel="Total runs" />
      </div>

      {/* Teams */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold">Teams</h2>
          <Link href="/teams" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
            View all &rarr;
          </Link>
        </div>

        {teams.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border bg-card p-8 text-center">
            <p className="text-sm text-muted-foreground">No teams yet.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {teams.slice(0, 6).map((team, idx) => {
              const memberStatuses = team.members.map((m) => ({
                id: m.id,
                role: m.role as AgentRole,
                model: m.model,
                status: (m.status ?? "idle") as AgentStatus,
                current_task: m.current_task,
                tokens_used: m.tokens_used,
              }));
              const hasActive = memberStatuses.some((m) => m.status !== "idle");

              return (
                <motion.div
                  key={team.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: idx * 0.05 }}
                >
                  <Link href={`/teams/${team.id}`} className="block group">
                    <div className={cn(
                      "rounded-xl border p-4 transition-all",
                      hasActive ? "border-primary/30 bg-card" : "border-border bg-card",
                      "hover:border-border-hover",
                    )}>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-semibold group-hover:text-primary transition-colors">
                            {team.name}
                          </h3>
                          {hasActive && (
                            <Badge variant="warning" className="gap-1">
                              <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
                              Active
                            </Badge>
                          )}
                        </div>
                        <ArrowRight className="h-3.5 w-3.5 text-muted-foreground group-hover:text-foreground transition-colors" />
                      </div>
                      <AgentNetwork agents={memberStatuses} />
                    </div>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        )}
      </section>

      {runningTasks.length > 0 && (
        <section>
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-sm font-semibold">Running Tasks</h2>
            <Badge variant="warning">{runningTasks.length}</Badge>
          </div>
          <div className="space-y-2">
            {runningTasks.slice(0, 3).map((task) => (
              <Link key={task.id} href={`/tasks/${task.id}`} className="block group">
                <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-3 hover:border-border-hover transition-all">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-builder-surface">
                    <Clock className="h-4 w-4 text-builder animate-pulse" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate group-hover:text-primary">{task.title}</p>
                    <p className="text-xs text-muted-foreground truncate">{task.description}</p>
                  </div>
                  <Badge variant="warning" className="shrink-0">Running</Badge>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
