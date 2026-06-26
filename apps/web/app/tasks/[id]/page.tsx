"use client";

import { use, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { getExecution, getTask, getTaskMessages } from "@/lib/api";
import type { Execution, Task, TaskMessage } from "@/lib/types";
import type { AgentRole } from "@/lib/constants";
import { AGENT_CONFIG } from "@/lib/constants";
import { AgentAvatar } from "@/components/agent-avatar";
import { ExecutionGraph } from "@/components/execution-graph";
import { ProgressStream } from "@/components/progress-stream";
import { ActivityFeed } from "@/components/activity-feed";
import { MetricCard } from "@/components/metric-card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  CheckCircle2, XCircle, Loader2, Copy, Check,
  ArrowLeft, Clock, Zap, FileText, Users, Activity,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

function extractPreview(text: string): string {
  try {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}") + 1;
    if (start !== -1 && end > start) {
      const parsed = JSON.parse(text.slice(start, end));
      return parsed.summary ?? parsed.delivery_summary ?? parsed.plan_summary ?? parsed.verdict ?? "";
    }
  } catch { /* fall through */ }
  return text.length > 300 ? text.slice(0, 300) + "..." : text;
}

function extractJSON(text: string): string {
  try {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}") + 1;
    if (start !== -1 && end > start) {
      return JSON.stringify(JSON.parse(text.slice(start, end)), null, 2);
    }
  } catch { /* fall through */ }
  return text;
}

function MessageCard({ msg }: { msg: TaskMessage }) {
  const config = AGENT_CONFIG[msg.role as AgentRole];
  const Icon = config?.icon;

  if (!config) return null;

  const preview = extractPreview(msg.content);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex items-start gap-3"
    >
      <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border-2 mt-0.5", config.border, config.bgSurface)}>
        <Icon className={cn("h-4 w-4", config.text)} />
      </div>
      <div className="flex-1 min-w-0 space-y-1.5">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant={config.badgeVariant}>{config.label}</Badge>
          <code className="text-[10px] text-muted-foreground font-mono truncate max-w-[140px]">{msg.model}</code>
          <span className="text-[10px] text-muted-foreground">
            {msg.created_at ? new Date(msg.created_at).toLocaleTimeString() : ""}
          </span>
          {msg.tokens && (
            <span className="text-[9px] font-mono text-muted-foreground/60">{msg.tokens} tok</span>
          )}
        </div>
        <div className={cn(
          "rounded-lg border p-3",
          msg.message_type === "plan" && "border-lead/20 bg-lead-surface",
          msg.message_type === "code" && "border-builder/20 bg-builder-surface",
          msg.message_type === "review" && "border-reviewer/20 bg-reviewer-surface",
          msg.message_type === "delivery" && "border-deliver/20 bg-deliver-surface",
          msg.message_type === "error" && "border-destructive/20 bg-destructive/5",
          !["plan", "code", "review", "delivery", "error"].includes(msg.message_type) && "border-border bg-surface/50",
        )}>
          <p className="text-xs text-muted-foreground whitespace-pre-wrap leading-relaxed">
            {preview || msg.content?.slice(0, 300) + "..."}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

function FinalOutputPanel({ messages }: { messages: TaskMessage[] }) {
  const delivery = messages.find((m) => m.message_type === "delivery");
  const [copied, setCopied] = useState(false);

  if (!delivery) return null;

  const output = extractJSON(delivery.content);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-3"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          <span className="text-sm font-semibold">Final Delivery</span>
        </div>
        <Button size="sm" variant="ghost" onClick={async () => {
          await navigator.clipboard.writeText(output);
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        }}>
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>
      <pre className="rounded-xl border border-deliver/20 bg-surface/50 p-4 text-xs leading-relaxed overflow-x-auto whitespace-pre-wrap font-mono text-muted-foreground">
        {output}
      </pre>
    </motion.div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-6 w-48 rounded-lg bg-surface" />
      <div className="h-4 w-72 rounded-lg bg-surface" />
      <div className="flex gap-3">
        {[1, 2, 3, 4].map((i) => <div key={i} className="flex-1 h-20 rounded-xl bg-surface" />)}
      </div>
      <div className="h-24 rounded-xl bg-surface" />
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex gap-3">
            <div className="h-8 w-8 rounded-lg bg-surface" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-32 rounded bg-surface" />
              <div className="h-12 rounded-lg bg-surface" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function TaskExecutionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [task, setTask] = useState<Task | null>(null);
  const [messages, setMessages] = useState<TaskMessage[]>([]);
  const [execution, setExecution] = useState<Execution | null>(null);
  const [loading, setLoading] = useState(true);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollingCountRef = useRef(0);
  const bottomRef = useRef<HTMLDivElement>(null);

  const isRunning = task?.status === "pending" || task?.status === "running";
  const isCompleted = task?.status === "completed";
  const currentNode = execution?.current_node ?? null;

  async function load() {
    if (pollingCountRef.current >= 100) {
      if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
      return;
    }
    pollingCountRef.current++;
    try {
      const [t, m, e] = await Promise.all([
        getTask(id).catch(() => null),
        getTaskMessages(id).catch<[]>(() => []),
        getExecution(id).catch(() => null),
      ]);
      if (t) setTask(t);
      setMessages(m);
      if (e) setExecution(e);

      if (t && (t.status === "completed" || t.status === "failed")) {
        if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
      }
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }

  useEffect(() => {
    pollingCountRef.current = 0;
    load();
    if (!pollingRef.current) { pollingRef.current = setInterval(load, 600); }
    return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
  }, [id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (loading) {
    return <div className="max-w-4xl mx-auto"><Skeleton /></div>;
  }

  if (!task) {
    return (
      <div className="flex items-center justify-center py-16 text-muted-foreground">
        Task not found
      </div>
    );
  }

  const statusBadge = () => {
    switch (task.status) {
      case "completed": return <Badge variant="success"><CheckCircle2 className="h-3 w-3 mr-1" />Completed</Badge>;
      case "running": return <Badge variant="warning"><Loader2 className="h-3 w-3 mr-1 animate-spin" />Running</Badge>;
      case "failed": return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Failed</Badge>;
      default: return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Pending</Badge>;
    }
  };

  const totalTokens = messages.reduce((sum, m) => sum + (m.tokens ?? 0), 0);

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in pb-20">
      {/* Header */}
      <div>
        <Link href="/tasks" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors mb-3">
          <ArrowLeft className="h-3 w-3" />
          Back to tasks
        </Link>
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-xl font-bold tracking-tight">{task.title}</h1>
          {statusBadge()}
        </div>
        <p className="text-sm text-muted-foreground">{task.description}</p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <MetricCard icon={Activity} label="Messages" value={messages.length} sublabel={isRunning ? "Live" : "Total"} />
        <MetricCard icon={Zap} label="Tokens" value={totalTokens} sublabel="Generated" />
        <MetricCard icon={Clock} label="Duration" value={
          execution?.started_at
            ? `${Math.round((Date.now() - new Date(execution.started_at).getTime()) / 1000)}s`
            : "--"
        } sublabel={isRunning ? "Running" : "Elapsed"} />
        <MetricCard icon={FileText} label="Status" value={task.status} sublabel={isCompleted ? "Delivered" : isRunning ? "In Progress" : "Pending"} />
      </div>

      {/* Execution Graph */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="text-[10px] text-muted-foreground font-mono mb-3 text-center">Execution Pipeline</div>
        <ExecutionGraph currentNode={currentNode} isComplete={isCompleted} />
      </div>

      {/* Content */}
      <Tabs defaultValue="stream">
        <TabsList>
          <TabsTrigger value="stream">Activity Stream</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="output">Output</TabsTrigger>
        </TabsList>

        <TabsContent value="stream">
          {messages.length === 0 ? (
            isRunning ? (
              <div className="rounded-xl border border-border bg-card p-12 text-center">
                <Loader2 className="h-6 w-6 animate-spin mx-auto mb-3 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">Agents are initializing...</p>
              </div>
            ) : (
              <div className="rounded-xl border border-border bg-card p-12 text-center">
                <p className="text-sm text-muted-foreground">No messages yet.</p>
              </div>
            )
          ) : (
            <div className="rounded-xl border border-border bg-card p-5 space-y-4">
              {messages.map((msg) => (
                <MessageCard key={msg.id} msg={msg} />
              ))}
              {isRunning && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground animate-pulse">
                  <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground" />
                  Processing...
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}

          {isCompleted && messages.length > 0 && <FinalOutputPanel messages={messages} />}
        </TabsContent>

        <TabsContent value="timeline">
          <div className="rounded-xl border border-border bg-card p-5">
            <ActivityFeed
              items={messages.map((m) => ({
                id: m.id,
                role: m.role as AgentRole,
                action: m.message_type === "plan" ? "Planning" : m.message_type === "code" ? "Building" : m.message_type === "review" ? "Reviewing" : m.message_type === "delivery" ? "Delivering" : "Processing",
                detail: extractPreview(m.content).slice(0, 100),
                timestamp: new Date(m.created_at).toLocaleTimeString(),
                status: "completed" as const,
              }))}
            />
          </div>
        </TabsContent>

        <TabsContent value="output">
          {messages.length > 0 ? (
            <div className="space-y-4">
              {messages.filter((m) => m.message_type === "delivery" || m.message_type === "code").map((m) => (
                <div key={m.id} className="rounded-xl border border-border bg-card p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Badge variant={AGENT_CONFIG[m.role as AgentRole]?.badgeVariant ?? "default"}>
                      {AGENT_CONFIG[m.role as AgentRole]?.label ?? m.role}
                    </Badge>
                    <span className="text-xs text-muted-foreground">{m.message_type}</span>
                  </div>
                  <pre className="text-xs font-mono text-muted-foreground whitespace-pre-wrap overflow-x-auto max-h-96">
                    {extractJSON(m.content)}
                  </pre>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-border bg-card p-12 text-center">
              <p className="text-sm text-muted-foreground">No output generated yet.</p>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Error */}
      {task.status === "failed" && task.error_message && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4">
          <div className="flex items-center gap-2 mb-2">
            <XCircle className="h-4 w-4 text-destructive" />
            <span className="text-sm font-semibold text-destructive">Error</span>
          </div>
          <pre className="text-xs text-destructive/80 whitespace-pre-wrap font-mono">{task.error_message}</pre>
        </div>
      )}
    </div>
  );
}
