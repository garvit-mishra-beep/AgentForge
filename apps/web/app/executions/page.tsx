"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { listExecutions, listTasks } from "@/lib/api";
import type { Execution, Task } from "@/lib/types";
import { Loader2, Activity, CheckCircle2, XCircle, RefreshCw, Clock, ChevronRight, Plus } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";

export default function ExecutionsPage() {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const [ex, t] = await Promise.all([
        listExecutions().catch(() => []),
        listTasks().catch(() => []),
      ]);
      setExecutions(ex);
      setTasks(t);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  const taskMap = new Map(tasks.map((t) => [t.id, t]));

  const statusConfig = (status: string) => {
    if (status === "completed") return { label: "Completed", color: "success" as const, Icon: CheckCircle2 };
    if (status === "running") return { label: "Running", color: "warning" as const, Icon: RefreshCw };
    if (status === "failed") return { label: "Failed", color: "destructive" as const, Icon: XCircle };
    return { label: "Pending", color: "secondary" as const, Icon: Clock };
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Executions</h1>
        <p className="text-sm text-muted-foreground mt-1">
          History of all AI team task executions
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin mr-2" />
          Loading executions...
        </div>
      ) : executions.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary-muted">
            <Activity className="h-6 w-6 text-primary" />
          </div>
          <h3 className="text-sm font-semibold mb-1">No executions yet</h3>
          <p className="text-sm text-muted-foreground mb-4 max-w-xs">
            Create a task to see executions appear here.
          </p>
          <Link href="/tasks">
            <Button variant="default">
              <Plus className="h-4 w-4" />
              New Task
            </Button>
          </Link>
        </div>
      ) : (
        <div className="space-y-2">
          {executions.map((exec, i) => {
            const task = taskMap.get(exec.task_id);
            const sc = statusConfig(exec.status);

            return (
              <motion.div
                key={exec.id}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: i * 0.03 }}
              >
                <Link href={`/executions/${exec.id}`} className="block group">
                  <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-3 hover:border-border-hover transition-all">
                    <div className={cn(
                      "flex h-8 w-8 items-center justify-center rounded-lg",
                      exec.status === "completed" && "bg-emerald-500/10",
                      exec.status === "running" && "bg-amber-500/10",
                      exec.status === "failed" && "bg-destructive/10",
                    )}>
                      <sc.Icon className={cn(
                        "h-4 w-4",
                        exec.status === "completed" && "text-emerald-400",
                        exec.status === "running" && "text-amber-400",
                        exec.status === "failed" && "text-destructive",
                      )} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-sm font-medium truncate group-hover:text-primary transition-colors">
                          {task?.title ?? `Task ${exec.task_id.slice(0, 8)}`}
                        </span>
                        <Badge variant={sc.color}>{sc.label}</Badge>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        <span className="font-mono">Node: {exec.current_node ?? "—"}</span>
                        {exec.started_at && (
                          <span>{new Date(exec.started_at).toLocaleDateString()}</span>
                        )}
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors shrink-0" />
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
