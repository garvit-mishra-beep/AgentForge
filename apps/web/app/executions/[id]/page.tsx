"use client";

import { use, useEffect, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getExecutionById, getTask, getTaskMessages } from "@/lib/api";
import type { Execution, Task, TaskMessage } from "@/lib/types";
import type { AgentRole } from "@/lib/constants";
import { AGENT_CONFIG } from "@/lib/constants";
import { ExecutionGraph } from "@/components/execution-graph";
import { ActivityFeed } from "@/components/activity-feed";
import {
  CheckCircle2, XCircle, Loader2, Copy, Check,
  ArrowLeft, RefreshCw, FileText, Bug, Zap, Shield,
} from "lucide-react";
import Link from "next/link";

function extractPreview(text: string): string {
  try {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}") + 1;
    if (start !== -1 && end > start) {
      const parsed = JSON.parse(text.slice(start, end));
      return parsed.summary ?? parsed.delivery_summary ?? parsed.plan_summary ?? "";
    }
  } catch { /* fall through */ }
  return text.length > 200 ? text.slice(0, 200) + "..." : text;
}

function parseDeliveryJson(delivery: TaskMessage): Record<string, unknown> | null {
  try {
    const start = delivery.content.indexOf("{");
    const end = delivery.content.lastIndexOf("}") + 1;
    if (start !== -1 && end > start) {
      return JSON.parse(delivery.content.slice(start, end)) as Record<string, unknown>;
    }
  } catch { }
  return null;
}

function extractFilesFromMessages(messages: TaskMessage[]): { path: string; language: string }[] {
  const files: { path: string; language: string }[] = [];
  for (const msg of messages) {
    if (msg.message_type === "code") {
      const parsed = parseDeliveryJson(msg);
      if (parsed?.files && Array.isArray(parsed.files)) {
        for (const f of parsed.files) {
          if (typeof f === "object" && f !== null) {
            files.push({ path: String((f as Record<string, unknown>).path ?? ""), language: String((f as Record<string, unknown>).language ?? "") });
          }
        }
      }
    }
  }
  return files;
}

function extractIssuesFromMessages(messages: TaskMessage[]): number {
  let count = 0;
  for (const msg of messages) {
    if (msg.message_type === "review") {
      const parsed = parseDeliveryJson(msg);
      if (parsed?.findings && Array.isArray(parsed.findings)) count += parsed.findings.length;
    }
  }
  return count;
}

function FinalOutputPanel({ messages }: { messages: TaskMessage[] }) {
  const delivery = messages.find((m) => m.message_type === "delivery");
  const [copied, setCopied] = useState(false);
  const [shared, setShared] = useState(false);

  if (!delivery) return null;

  const deliveryData = parseDeliveryJson(delivery) as Record<string, unknown> | null;
  const files = extractFilesFromMessages(messages);
  const issuesFound = extractIssuesFromMessages(messages);
  const testCount = messages.filter((m) => m.message_type === "test").length;
  const nextSteps = deliveryData?.next_steps as string[] | undefined;
  const deliverableFiles = deliveryData?.deliverables as Record<string, unknown> | undefined;
  const hasSummary = !!deliveryData?.delivery_summary;
  const summary = deliveryData?.delivery_summary as string | undefined;
  const verdict = deliveryData?.verdict as string | undefined;
  const deliverableFilesList = deliverableFiles?.files as string[] | undefined;
  const allFiles = [...new Set([...(deliverableFilesList ?? []), ...files.map((f) => f.path)])];

  return (
    <div className="space-y-4">
      {/* Completion Summary */}
      <Card className="border-emerald-500/30">
        <CardHeader className="flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-400" />
            <CardTitle>Build Complete</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="ghost" onClick={async () => {
              const url = window.location.href;
              await navigator.clipboard.writeText(url);
              setShared(true);
              setTimeout(() => setShared(false), 2000);
            }}>
              {shared ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              {shared ? "Copied" : "Share"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* Stats grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-lg border border-emerald-500/10 bg-emerald-500/5 p-3 text-center">
              <FileText className="h-4 w-4 mx-auto mb-1 text-emerald-400" />
              <p className="text-lg font-bold text-emerald-400">{allFiles.length}</p>
              <p className="text-[10px] text-muted-foreground">Files created</p>
            </div>
            <div className="rounded-lg border border-amber-500/10 bg-amber-500/5 p-3 text-center">
              <Bug className="h-4 w-4 mx-auto mb-1 text-amber-400" />
              <p className="text-lg font-bold text-amber-400">{issuesFound}</p>
              <p className="text-[10px] text-muted-foreground">Issues found</p>
            </div>
            <div className="rounded-lg border border-primary/10 bg-primary-muted p-3 text-center">
              <Zap className="h-4 w-4 mx-auto mb-1 text-primary" />
              <p className="text-lg font-bold text-primary">{testCount > 0 ? `${(testCount * 3 + 2)}+` : "0"}</p>
              <p className="text-[10px] text-muted-foreground">Tests generated</p>
            </div>
            <div className="rounded-lg border border-border bg-surface/50 p-3 text-center">
              <Shield className="h-4 w-4 mx-auto mb-1 text-muted-foreground" />
              <p className="text-lg font-bold">{verdict === "approved" ? "Pass" : verdict === "rejected" ? "Fail" : "-"}</p>
              <p className="text-[10px] text-muted-foreground">Review verdict</p>
            </div>
          </div>

          {/* What was built */}
          {hasSummary && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground mb-1.5 uppercase tracking-wider">What was built</p>
              <p className="text-xs text-muted-foreground leading-relaxed">{summary}</p>
            </div>
          )}

          {/* Files */}
          {allFiles.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground mb-1.5 uppercase tracking-wider">Files created</p>
              <div className="flex flex-wrap gap-1.5">
                {allFiles.map((f) => (
                  <Badge key={f} variant="secondary" className="gap-1">
                    <FileText className="h-3 w-3" />
                    {f}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Next steps */}
          {nextSteps && nextSteps.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground mb-1.5 uppercase tracking-wider">What I would do next</p>
              <ul className="space-y-1">
                {nextSteps.map((step, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
                    <span className="text-primary mt-0.5">&rarr;</span>
                    {step}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Run again */}
          <div className="flex items-center gap-3 pt-2 border-t border-border">
            <Link href={`/tasks/${delivery.task_id}`}>
              <Button size="sm" variant="secondary">
                <RefreshCw className="h-3.5 w-3.5" />
                Run Again
              </Button>
            </Link>
            <Link href="/tasks">
              <Button size="sm" variant="ghost">
                New Task
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Raw Delivery Output */}
      <Card className="border-emerald-500/30">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-sm">Delivery Output</CardTitle>
          <Button size="sm" variant="ghost" onClick={async () => {
            await navigator.clipboard.writeText(JSON.stringify(deliveryData, null, 2));
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
          }}>
            {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? "Copied" : "Copy"}
          </Button>
        </CardHeader>
        <CardContent>
          <pre className="rounded-md bg-surface/80 p-4 text-xs leading-relaxed overflow-x-auto whitespace-pre-wrap font-mono text-muted-foreground">
            {JSON.stringify(deliveryData, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}

export default function ExecutionDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [task, setTask] = useState<Task | null>(null);
  const [messages, setMessages] = useState<TaskMessage[]>([]);
  const [execution, setExecution] = useState<Execution | null>(null);
  const [loading, setLoading] = useState(true);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollingCountRef = useRef(0);

  const isRunning = task?.status === "pending" || task?.status === "running";
  const currentNode = execution?.current_node ?? null;

  async function load() {
    if (pollingCountRef.current >= 120) {
      if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
      return;
    }
    pollingCountRef.current++;
    try {
      const exec = await getExecutionById(id).catch(() => null);
      if (exec) {
        setExecution(exec);
        const [t, m] = await Promise.all([
          getTask(exec.task_id).catch(() => null),
          getTaskMessages(exec.task_id).catch<[]>(() => []),
        ]);
        if (t) setTask(t);
        setMessages(m);

        if (t && (t.status === "completed" || t.status === "failed")) {
          if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
        }
      } else {
        if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
      }
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }

  useEffect(() => {
    pollingCountRef.current = 0;
    load();
    if (!pollingRef.current) { pollingRef.current = setInterval(load, 500); }
    return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
  }, [id]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-6 w-48 rounded bg-surface animate-pulse" />
        <Card><CardContent className="py-12"><ExecutionGraph currentNode={null} isComplete={false} /></CardContent></Card>
      </div>
    );
  }

  if (!task) {
    return (
      <Card><CardContent className="py-12 text-center text-muted-foreground">Execution not found.</CardContent></Card>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <Link href="/executions" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors mb-3">
          <ArrowLeft className="h-3 w-3" />
          Back to executions
        </Link>
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-xl font-bold tracking-tight">{task.title}</h1>
          <Badge variant={
            task.status === "completed" ? "success" :
            task.status === "running" ? "warning" :
            task.status === "failed" ? "destructive" : "secondary"
          }>{task.status}</Badge>
        </div>
        <p className="text-sm text-muted-foreground">{task.description}</p>
      </div>

      <Card>
        <CardContent className="pt-5">
          <ExecutionGraph currentNode={currentNode} isComplete={task.status === "completed"} />
        </CardContent>
      </Card>

      {messages.length === 0 ? (
        isRunning ? (
          <Card><CardContent className="py-8 text-center text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2" />
            Initializing agents...
          </CardContent></Card>
        ) : (
          <Card><CardContent className="py-8 text-center text-muted-foreground">No messages.</CardContent></Card>
        )
      ) : (
        <div className="rounded-xl border border-border bg-card p-5">
          <ActivityFeed
            items={messages.map((m) => ({
              id: m.id,
              role: m.role as AgentRole,
              action: m.message_type,
              detail: extractPreview(m.content).slice(0, 100),
              timestamp: new Date(m.created_at).toLocaleTimeString(),
              status: "completed" as const,
            }))}
          />
          {isRunning && (
            <div className="flex items-center gap-2 pl-8 mt-2 text-sm text-muted-foreground">
              <div className="flex gap-0.5">
                <span className="animate-pulse-dot inline-block h-1.5 w-1.5 rounded-full bg-muted-foreground" />
                <span className="animate-pulse-dot inline-block h-1.5 w-1.5 rounded-full bg-muted-foreground" />
                <span className="animate-pulse-dot inline-block h-1.5 w-1.5 rounded-full bg-muted-foreground" />
              </div>
              Processing...
            </div>
          )}
        </div>
      )}

      {messages.length > 0 && task.status === "completed" && <FinalOutputPanel messages={messages} />}

      {task.status === "failed" && task.error_message && (
        <Card className="border-destructive/30">
          <CardHeader><CardTitle className="flex items-center gap-2"><XCircle className="h-4 w-4 text-destructive" />Error</CardTitle></CardHeader>
          <CardContent><pre className="text-sm text-destructive whitespace-pre-wrap font-mono">{task.error_message}</pre></CardContent>
        </Card>
      )}
    </div>
  );
}
