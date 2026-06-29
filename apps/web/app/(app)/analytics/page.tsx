"use client";

import { useEffect, useState } from "react";
import { MetricCard } from "@/components/ui/metric-card";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { listTeams, listTasks, listExecutions } from "@/lib/api";
import type { Team, Task, Execution } from "@/lib/types";
import { Loader2, Zap, Users, ListChecks, Activity, Clock, TrendingUp } from "lucide-react";

export default function AnalyticsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [t, ts, ex] = await Promise.all([
          listTeams().catch(() => []),
          listTasks().catch(() => []),
          listExecutions().catch(() => []),
        ]);
        setTeams(t);
        setTasks(ts);
        setExecutions(ex);
      } finally { setLoading(false); }
    }
    load();
  }, []);

  const totalMembers = teams.reduce((sum, t) => sum + t.members.length, 0);
  const completedTasks = tasks.filter((t) => t.status === "completed").length;
  const runningTasks = tasks.filter((t) => t.status === "running").length;
  const failedTasks = tasks.filter((t) => t.status === "failed").length;
  const successRate = tasks.length > 0 ? Math.round((completedTasks / tasks.length) * 100) : 0;
  const avgMembersPerTeam = teams.length > 0 ? (totalMembers / teams.length).toFixed(1) : "0";

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Usage metrics and performance data for your AI teams
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin mr-2" />
          Loading analytics...
        </div>
      ) : (
        <>
          {/* Overview Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <MetricCard icon={Users} label="Total Teams" value={teams.length} sublabel={`${totalMembers} total members`} />
            <MetricCard icon={ListChecks} label="Total Tasks" value={tasks.length} sublabel={`${completedTasks} completed`} />
            <MetricCard icon={Activity} label="Success Rate" value={`${successRate}%`} sublabel={`${failedTasks} failed`} trend={successRate >= 50 ? "up" : "down"} trendValue={`${successRate}%`} />
            <MetricCard icon={TrendingUp} label="Avg Team Size" value={avgMembersPerTeam} sublabel="members per team" />
          </div>

          {/* Status breakdown */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-primary" />
                  Task Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-emerald-400" />
                      <span className="text-xs text-muted-foreground">Completed</span>
                    </div>
                    <span className="text-sm font-semibold">{completedTasks}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-amber-400" />
                      <span className="text-xs text-muted-foreground">Running</span>
                    </div>
                    <span className="text-sm font-semibold">{runningTasks}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-destructive" />
                      <span className="text-xs text-muted-foreground">Failed</span>
                    </div>
                    <span className="text-sm font-semibold">{failedTasks}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-muted-foreground/50" />
                      <span className="text-xs text-muted-foreground">Pending</span>
                    </div>
                    <span className="text-sm font-semibold">{tasks.length - completedTasks - runningTasks - failedTasks}</span>
                  </div>

                  {/* Progress bar */}
                  {tasks.length > 0 && (
                    <div className="h-2 rounded-full bg-surface overflow-hidden flex">
                      <div className="bg-emerald-400 h-full transition-all" style={{ width: `${(completedTasks / tasks.length) * 100}%` }} />
                      <div className="bg-amber-400 h-full transition-all" style={{ width: `${(runningTasks / tasks.length) * 100}%` }} />
                      <div className="bg-destructive h-full transition-all" style={{ width: `${(failedTasks / tasks.length) * 100}%` }} />
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-primary" />
                  Agent Usage
                </CardTitle>
              </CardHeader>
              <CardContent>
                {teams.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">No teams yet</p>
                ) : (
                  <div className="space-y-2">
                    {["team_lead", "builder", "reviewer", "tester"].map((role) => {
                      const count = teams.reduce((sum, t) => sum + t.members.filter((m) => m.role === role).length, 0);
                      return (
                        <div key={role} className="flex items-center justify-between">
                          <span className="text-xs capitalize text-muted-foreground">{role.replace("_", " ")}</span>
                          <span className="text-sm font-semibold">{count}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Executions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-primary" />
                Recent Executions
              </CardTitle>
            </CardHeader>
            <CardContent>
              {executions.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">No executions yet</p>
              ) : (
                <div className="space-y-1.5">
                  {executions.slice(0, 10).map((exec) => (
                    <div key={exec.id} className="flex items-center justify-between rounded-lg border border-border bg-surface/50 px-3 py-2 text-xs">
                      <span className="text-muted-foreground font-mono">{exec.task_id.slice(0, 12)}...</span>
                      <Badge variant={exec.status === "completed" ? "success" : exec.status === "running" ? "warning" : exec.status === "failed" ? "destructive" : "secondary"}>
                        {exec.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
