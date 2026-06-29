"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { MetricCard } from "@/components/ui/metric-card";
import { QuickReviewTextarea } from "@/components/review/QuickReviewTextarea";
import { QuickReviewProgress } from "@/components/review/QuickReviewProgress";
import { QuickReviewResults } from "@/components/review/QuickReviewResults";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { listTeams, listTasks, listExecutions, submitReview, pollReview } from "@/lib/api";
import type { Team, Task, Execution, ReviewResult, ReviewRecord, ReviewStatus } from "@/lib/types";
import {
  Users, ListChecks, Activity, Zap, ArrowRight, Play, Plus, Clock,
  CheckCircle2, XCircle, RefreshCw, Loader2,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

const POLL_INTERVAL = 3000;
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

  const hasRunning = tasks.some((t) => t.status === "running");

  async function loadInitial() {
    const [tms, ts, ex] = await Promise.all([
      listTeams().catch(() => [] as Team[]),
      listTasks().catch(() => [] as Task[]),
      listExecutions().catch(() => [] as Execution[]),
    ]);
    setTeams(tms);
    setTasks(ts);
    setExecutions(ex);
    setLoading(false);
  }

  async function pollExecutions() {
    const [ex, ts] = await Promise.all([
      listExecutions().catch(() => null),
      listTasks().catch(() => null),
    ]);
    if (ex) setExecutions(ex);
    if (ts) setTasks(ts);
  }

  useEffect(() => { loadInitial(); }, []);

  useEffect(() => {
    if (!hasRunning) return;
    const interval = setInterval(pollExecutions, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [hasRunning]);

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
  const recentTasks = tasks.slice(0, 6);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-8">
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column â€” 2/3 */}
        <div className="lg:col-span-2 space-y-6">
          {/* Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <MetricCard icon={Users} label="Active Teams" value={activeTeams.length} sublabel={`${teams.length} total`} />
            <MetricCard icon={ListChecks} label="Total Tasks" value={tasks.length} sublabel={`${completedTasks.length} completed`} />
            <MetricCard icon={Activity} label="Running" value={runningTasks.length} sublabel="Active now" />
            <MetricCard icon={Zap} label="Executions" value={executions.length} sublabel="Total runs" />
          </div>

          {/* Recent Tasks */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold">Recent Tasks</h2>
              <Link href="/tasks" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
                View all &rarr;
              </Link>
            </div>
            {recentTasks.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border bg-card p-8 text-center">
                <p className="text-sm text-muted-foreground">No tasks yet.</p>
              </div>
            ) : (
              <div className="space-y-1.5">
                {recentTasks.map((task) => {
                  const sc = task.status === "completed" ? { Icon: CheckCircle2, color: "text-emerald-400" }
                    : task.status === "running" ? { Icon: RefreshCw, color: "text-amber-400" }
                    : task.status === "failed" ? { Icon: XCircle, color: "text-destructive" }
                    : { Icon: Clock, color: "text-muted-foreground" };
                  return (
                    <Link key={task.id} href={`/tasks/${task.id}`} className="block group">
                      <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-2.5 hover:border-border-hover transition-all">
                        <sc.Icon className={cn("h-4 w-4 shrink-0", sc.color, task.status === "running" && "animate-spin")} />
                        <span className="text-sm font-medium truncate flex-1 group-hover:text-primary transition-colors">{task.title}</span>
                        <Badge variant={
                          task.status === "completed" ? "success" : task.status === "running" ? "warning" : task.status === "failed" ? "destructive" : "secondary"
                        } className="shrink-0 text-[10px]">
                          {task.status}
                        </Badge>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </section>

          {/* Active Executions */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <h2 className="text-sm font-semibold">Active Executions</h2>
              {hasRunning && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />}
            </div>
            {executions.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border bg-card p-8 text-center">
                <p className="text-sm text-muted-foreground">No executions yet.</p>
              </div>
            ) : (
              <div className="space-y-1.5">
                {executions.slice(0, 5).map((exec) => {
                  const sc = exec.status === "completed" ? { Icon: CheckCircle2, color: "text-emerald-400" }
                    : exec.status === "running" ? { Icon: RefreshCw, color: "text-amber-400" }
                    : exec.status === "failed" ? { Icon: XCircle, color: "text-destructive" }
                    : { Icon: Clock, color: "text-muted-foreground" };
                  return (
                    <Link key={exec.id} href={`/executions/${exec.id}`} className="block group">
                      <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-2.5 hover:border-border-hover transition-all">
                        <sc.Icon className={cn("h-4 w-4 shrink-0", sc.color, exec.status === "running" && "animate-pulse")} />
                        <div className="flex-1 min-w-0">
                          <span className="text-sm font-medium truncate block group-hover:text-primary transition-colors">
                            {exec.task_id.slice(0, 12)}...
                          </span>
                          <span className="text-[10px] text-muted-foreground font-mono">
                            Node: {exec.current_node ?? "â€”"}
                          </span>
                        </div>
                        <Badge variant={
                          exec.status === "completed" ? "success" : exec.status === "running" ? "warning" : exec.status === "failed" ? "destructive" : "secondary"
                        } className="shrink-0 text-[10px]">
                          {exec.status}
                        </Badge>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </section>
        </div>

        {/* Right column â€” 1/3 */}
        <div className="space-y-6">
          {/* Your Teams */}
          <section className="rounded-xl border border-border bg-card p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold">Your Teams</h2>
              </div>
              <Link href="/teams" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
                View all &rarr;
              </Link>
            </div>
            {teams.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-4">No teams yet.</p>
            ) : (
              <div className="space-y-1.5">
                {teams.slice(0, 4).map((team) => (
                  <Link key={team.id} href={`/teams/${team.id}`} className="block group">
                    <div className="flex items-center justify-between rounded-lg px-2.5 py-2 hover:bg-surface/50 transition-colors">
                      <span className="text-xs font-medium group-hover:text-primary transition-colors">{team.name}</span>
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] text-muted-foreground">{team.members.length} members</span>
                        <ArrowRight className="h-3 w-3 text-muted-foreground group-hover:text-foreground transition-colors" />
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </section>

          {/* Quick Review */}
          <section className="rounded-xl border border-border bg-card p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-primary-muted">
                <Zap className="h-3 w-3 text-primary" />
              </div>
              <h2 className="text-sm font-semibold">Quick Review</h2>
            </div>

            {reviewState === "idle" && (
              <QuickReviewTextarea onReview={handleReview} busy={false} />
            )}
            {reviewState === "busy" && (
              <QuickReviewProgress status={reviewStatus} elapsed={reviewElapsed} />
            )}
            {reviewState === "error" && (
              <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3">
                <p className="text-xs font-medium text-destructive mb-1">Review failed</p>
                <p className="text-[10px] text-muted-foreground">{reviewError}</p>
                <Button onClick={handleReviewAnother} variant="outline" size="sm" className="mt-2">
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
        </div>
      </div>
    </div>
  );
}
