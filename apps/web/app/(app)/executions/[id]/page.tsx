"use client";

import { use, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ExecutionGraph } from "@/components/task/execution-graph";
import { MetricCard } from "@/components/ui/metric-card";
import { AGENT_CONFIG, type AgentRole } from "@/lib/constants";
import { DEMO_SCENARIOS, type DemoScenario } from "@/lib/demo-data";
import type { TaskMessage, Task, Execution } from "@/lib/types";
import { getExecutionById, getTask, getTaskMessages } from "@/lib/api";
import {
  CheckCircle2, Loader2, Play, Pause, SkipForward,
  Sparkles, ArrowRight, Clock, Zap,
  FileText, RotateCcw,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

const TYPING_DURATION = 400;

function extractPreview(text: string): string {
  try {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}") + 1;
    if (start !== -1 && end > start) {
      const parsed = JSON.parse(text.slice(start, end));
      return parsed.summary ?? parsed.delivery_summary ?? parsed.plan_summary ?? parsed.verdict ?? "";
    }
  } catch {
    // ignore error
  }
  return text.length > 300 ? text.slice(0, 300) + "..." : text;
}

function extractFindings(text: string): { severity: string; description: string; recommendation: string }[] | null {
  try {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}") + 1;
    if (start !== -1 && end > start) {
      const parsed = JSON.parse(text.slice(start, end));
      return parsed.findings ?? null;
    }
  } catch {
    // ignore error
  }
  return null;
}

function extractFiles(text: string): { path: string; language: string; content: string }[] | null {
  try {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}") + 1;
    if (start !== -1 && end > start) {
      const parsed = JSON.parse(text.slice(start, end));
      return parsed.files ?? null;
    }
  } catch {
    // ignore error
  }
  return null;
}

function DemoMessageCard({ msg, index, scenario }: { msg: TaskMessage; index: number; scenario: DemoScenario }) {
  const config = AGENT_CONFIG[msg.role as AgentRole];
  if (!config) return null;

  const Icon = config.icon;
  const tokenCount = scenario.tokenCounts[index] ?? 0;
  const preview = extractPreview(msg.content);
  const findings = msg.message_type === "review" ? extractFindings(msg.content) : null;
  const files = msg.message_type === "code" ? extractFiles(msg.content) : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
    >
      <div className="flex items-start gap-3">
        <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border-2 mt-0.5", config.border, config.bg)}>
          <Icon className={cn("h-4 w-4", config.text)} />
        </div>
        <div className="flex-1 min-w-0 space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant={config.badgeVariant}>{config.label}</Badge>
            <code className="text-[10px] text-muted-foreground font-mono truncate max-w-[140px]">{msg.model}</code>
            <span className="text-[10px] text-muted-foreground">
              {new Date(msg.created_at).toLocaleTimeString()}
            </span>
            <span className="text-[9px] font-mono text-muted-foreground/60">{tokenCount} tok</span>
          </div>

          {msg.message_type === "plan" && (
            <div className="rounded-lg border border-lead/20 bg-lead-surface p-3 space-y-2">
              <p className="text-xs text-muted-foreground leading-relaxed">{preview}</p>
            </div>
          )}

          {msg.message_type === "code" && files && (
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground leading-relaxed">{preview}</p>
              {files.map((file, i) => (
                <div key={i} className="rounded-lg border border-border bg-surface/80 overflow-hidden">
                  <div className="flex items-center gap-2 border-b border-border px-3 py-1.5">
                    <FileText className="h-3 w-3 text-muted-foreground" />
                    <span className="text-[10px] font-mono text-muted-foreground">{file.path}</span>
                    <span className="ml-auto text-[10px] font-mono text-muted-foreground/60">{file.language}</span>
                  </div>
                  <pre className="p-3 text-[11px] font-mono leading-relaxed overflow-x-auto max-h-48 text-muted-foreground">
                    <code>{file.content.slice(0, 600)}{file.content.length > 600 ? "..." : ""}</code>
                  </pre>
                </div>
              ))}
            </div>
          )}

          {msg.message_type === "review" && (
            <div className="rounded-lg border border-reviewer/20 bg-reviewer-surface p-3 space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant="reviewer">{preview === "PASS" ? "PASS" : "REVIEW"}</Badge>
              </div>
              {findings && findings.length > 0 && (
                <div className="space-y-1.5">
                  {findings.map((f, i) => (
                    <div key={i} className="flex items-start gap-2 text-[11px] text-muted-foreground">
                      <span className={cn("shrink-0 mt-0.5 font-mono", f.severity === "minor" ? "text-reviewer" : "text-destructive")}>
                        [{f.severity}]
                      </span>
                      <div>
                        <p>{f.description}</p>
                        <p className="text-muted-foreground/60 mt-0.5">&rarr; {f.recommendation}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {msg.message_type === "test" && (
            <div className="rounded-lg border border-tester/20 bg-tester-surface p-3 space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant="tester">PASS</Badge>
                <span className="text-[11px] text-muted-foreground font-mono">87% coverage</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">{preview}</p>
            </div>
          )}

          {msg.message_type === "delivery" && (
            <div className="rounded-lg border border-deliver/20 bg-deliver-surface p-3 space-y-2">
              <div className="flex items-center gap-2">
                <Sparkles className="h-3.5 w-3.5 text-deliver" />
                <span className="text-xs font-semibold text-deliver">Approved</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">{preview}</p>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default function DemoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const isMockScenario = ["jwt-auth", "crud-api", "react-component", "unit-tests", "sql-schema"].includes(id);

  const [scenarioId, setScenarioId] = useState(isMockScenario ? id : "jwt-auth");
  const [phase, setPhase] = useState(0);
  const [revealedMessages, setRevealedMessages] = useState<TaskMessage[]>([]);
  const [isComplete, setIsComplete] = useState(false);
  const [showFinal, setShowFinal] = useState(false);
  const [timerStopped, setTimerStopped] = useState(false);
  const [playing, setPlaying] = useState(true);
  const [speed, setSpeed] = useState(1);
  const bottomRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Real API state
  const [realExecution, setRealExecution] = useState<Execution | null>(null);
  const [realTask, setRealTask] = useState<Task | null>(null);
  const [realMessages, setRealMessages] = useState<TaskMessage[]>([]);
  const [realLoading, setRealLoading] = useState(true);

  const isRealMode = !isMockScenario;

  useEffect(() => {
    if (!isRealMode) return;

    let pollingInterval: ReturnType<typeof setInterval> | null = null;

    async function loadRealData() {
      try {
        const exec = await getExecutionById(id);
        setRealExecution(exec);
        if (exec && exec.task_id) {
          const [t, m] = await Promise.all([
            getTask(exec.task_id).catch(() => null),
            getTaskMessages(exec.task_id).catch<TaskMessage[]>(() => []),
          ]);
          if (t) setRealTask(t);
          setRealMessages(m);

          if (t && (t.status === "completed" || t.status === "failed")) {
            if (pollingInterval) {
              clearInterval(pollingInterval);
              pollingInterval = null;
            }
          }
        }
      } catch (err) {
        console.error(err);
      } finally {
        setRealLoading(false);
      }
    }

    loadRealData();
    pollingInterval = setInterval(loadRealData, 1000);

    return () => {
      if (pollingInterval) clearInterval(pollingInterval);
    };
  }, [id, isRealMode]);

  const scenario = useMemo(
    () => DEMO_SCENARIOS.find((s) => s.id === scenarioId) ?? DEMO_SCENARIOS[0]!,
    [scenarioId],
  ) as DemoScenario;

  const allMessages = scenario.messages;

  // Reset when scenario changes
  useEffect(() => {
    setPhase(0);
    setRevealedMessages([]);
    setIsComplete(false);
    setShowFinal(false);
    setTimerStopped(false);
    setPlaying(true);
  }, [scenarioId]);

  // Auto-advance logic
  useEffect(() => {
    if (!playing || phase >= allMessages.length || timerStopped) return;

    const msgDelay = phase === 0 ? 600 : (() => {
      const delays = [scenario.timing.planDelay, scenario.timing.builderDelay, scenario.timing.reviewerDelay, scenario.timing.testerDelay, scenario.timing.deliverDelay];
      return delays.slice(0, phase).reduce((a, b) => a + b, 0) + TYPING_DURATION;
    })();

    const adjustedDelay = msgDelay / speed;

    const msg = allMessages[phase];
    if (!msg) return;

    timeoutRef.current = setTimeout(() => {
      setRevealedMessages((prev) => [...prev, msg]);
      setPhase((p) => p + 1);

      if (phase === allMessages.length - 1) {
        setTimerStopped(true);
        setTimeout(() => {
          setIsComplete(true);
          setTimeout(() => setShowFinal(true), 300);
        }, 500);
      }
    }, adjustedDelay);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [phase, playing, timerStopped, allMessages, scenario.timing, speed]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [revealedMessages]);

  const handleNext = useCallback(() => {
    if (phase >= allMessages.length) return;
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    const msg = allMessages[phase];
    if (!msg) return;
    setRevealedMessages((prev) => [...prev, msg]);
    setPhase((p) => p + 1);
    if (phase === allMessages.length - 1) {
      setTimerStopped(true);
      setTimeout(() => {
        setIsComplete(true);
        setTimeout(() => setShowFinal(true), 300);
      }, 500);
    }
  }, [phase, allMessages]);

  const handleReplay = useCallback(() => {
    setPhase(0);
    setRevealedMessages([]);
    setIsComplete(false);
    setShowFinal(false);
    setTimerStopped(false);
    setPlaying(true);
  }, []);

  const totalTokens = scenario.tokenCounts.reduce((a, b) => a + b, 0);

  if (isRealMode && realLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 pb-20 mt-10">
        <div className="space-y-4 animate-pulse">
          <div className="h-6 w-48 rounded-lg bg-surface" />
          <div className="h-4 w-72 rounded-lg bg-surface" />
          <div className="flex gap-3">
            {[1, 2, 3, 4].map((i) => <div key={i} className="flex-1 h-20 rounded-xl bg-surface" />)}
          </div>
          <div className="h-24 rounded-xl bg-surface" />
        </div>
      </div>
    );
  }

  if (isRealMode && !realExecution) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 text-center py-20 mt-10">
        <h1 className="text-xl font-bold">Execution Not Found</h1>
        <p className="text-muted-foreground text-sm">We couldn&apos;t load execution details for ID {id}.</p>
        <Link href="/">
          <Button className="mt-4">Back to Home</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in pb-20">
      {/* Header */}
      <div>
        <Link href="/" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors mb-3">
          &larr; Back to home
        </Link>

        {/* Scenario tabs */}
        {!isRealMode && (
          <div className="flex items-center gap-2 mb-4 flex-wrap">
            {DEMO_SCENARIOS.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => setScenarioId(s.id)}
                className={cn(
                  "rounded-lg px-3 py-1.5 text-xs font-medium transition-all cursor-pointer",
                  scenarioId === s.id
                    ? "bg-primary-muted text-primary border border-primary/30"
                    : "text-muted-foreground hover:text-foreground border border-transparent hover:border-border",
                )}
              >
                {s.title}
              </button>
            ))}
          </div>
        )}

        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-xl font-bold tracking-tight">{isRealMode ? (realTask?.title ?? "Execution Detail") : scenario.title}</h1>
          <Badge variant={isRealMode ? (realTask?.status === "completed" ? "success" : realTask?.status === "failed" ? "destructive" : "warning") : (isComplete ? "success" : "warning")} className="gap-1">
            {isRealMode ? (
              realTask?.status === "completed" ? <><CheckCircle2 className="h-3 w-3" /> Completed</> :
              realTask?.status === "failed" ? <><CheckCircle2 className="h-3 w-3" /> Failed</> :
              <><Loader2 className="h-3 w-3 animate-spin" /> Running</>
            ) : (
              isComplete ? <><CheckCircle2 className="h-3 w-3" /> Completed</> : <><Loader2 className="h-3 w-3 animate-spin" /> Running</>
            )}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          {isRealMode ? (realTask?.description ?? "Details of current task execution") : scenario.description}
        </p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <MetricCard icon={Zap} label="Total Tokens" value={isRealMode ? (realExecution?.total_tokens ?? 0) : (isComplete ? totalTokens : "...")} sublabel="Generated" />
        <MetricCard icon={Clock} label="Duration" value={isRealMode ? (realExecution?.completed_at ? `${Math.round((new Date(realExecution.completed_at).getTime() - new Date(realExecution.started_at).getTime()) / 1000)}s` : "Live") : (isComplete ? "~12s" : "Live")} sublabel={isRealMode ? (realExecution?.completed_at ? "Completed" : "Running") : (isComplete ? "Completed" : "Running")} />
        <MetricCard icon={Sparkles} label="Messages" value={isRealMode ? realMessages.length : revealedMessages.length} sublabel={isRealMode ? "Received" : `of ${allMessages.length}`} />
        <MetricCard icon={Play} label="Status" value={isRealMode ? (realTask?.status ?? "pending") : (isComplete ? "Done" : phase > 0 ? "Active" : "Starting")} sublabel={isRealMode ? "State" : (isComplete ? "Delivered" : "In Progress")} />
      </div>

      {/* Execution Pipeline */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="text-[10px] text-muted-foreground font-mono mb-3 text-center">Agent Pipeline</div>
        <ExecutionGraph
          currentNode={isRealMode ? (realExecution?.current_node ?? null) : (isComplete ? "team_lead_deliver" : phase > 3 ? "reviewer" : phase > 2 ? "builder" : phase > 1 ? "team_lead_plan" : null)}
          isComplete={isRealMode ? (realExecution?.status === "completed") : isComplete}
        />
      </div>

      {/* Controls / Status Info */}
      {!isRealMode ? (
        <div className="flex items-center justify-between gap-3 rounded-xl border border-border bg-card p-3">
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => setPlaying((p) => !p)}
              disabled={isComplete}
              className="gap-1.5"
            >
              {playing ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
              {playing ? "Pause" : "Play"}
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={handleNext}
              disabled={isComplete || phase >= allMessages.length}
              className="gap-1.5"
            >
              <SkipForward className="h-3.5 w-3.5" />
              Skip
            </Button>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 rounded-lg bg-surface p-0.5">
              {[1, 2, 3].map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setSpeed(s)}
                  className={cn(
                    "px-2 py-1 text-[11px] font-medium rounded-md transition-all cursor-pointer",
                    speed === s ? "bg-primary-muted text-primary" : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {s}x
                </button>
              ))}
            </div>
            <Button size="sm" variant="secondary" onClick={handleReplay} className="gap-1.5">
              <RotateCcw className="h-3.5 w-3.5" />
              Replay
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-between gap-3 rounded-xl border border-border bg-card p-3.5 px-5">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className={cn("animate-ping absolute inline-flex h-full w-full rounded-full opacity-75", (realTask?.status === "completed" || realTask?.status === "failed") ? "bg-emerald-400" : "bg-sky-400")}></span>
              <span className={cn("relative inline-flex rounded-full h-2 w-2", (realTask?.status === "completed" || realTask?.status === "failed") ? "bg-emerald-500" : "bg-sky-500")}></span>
            </span>
            <span className="text-xs font-medium text-muted-foreground">
              {realTask?.status === "completed" ? "Execution Complete" : realTask?.status === "failed" ? "Execution Failed" : "Streaming execution logs in real-time"}
            </span>
          </div>
          {realTask?.error_message && (
            <span className="text-xs text-destructive font-mono truncate max-w-sm">
              Error: {realTask.error_message}
            </span>
          )}
        </div>
      )}

      {/* Progress bar (clickable to advance in simulation mode) */}
      {!isRealMode && (
        <div
          className="relative h-1.5 rounded-full bg-surface overflow-hidden cursor-pointer group"
          onClick={handleNext}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") handleNext(); }}
        >
          <div
            className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-lead via-builder via-reviewer to-deliver transition-all duration-700 ease-out group-hover:opacity-80"
            style={{ width: `${(revealedMessages.length / allMessages.length) * 100}%` }}
          />
        </div>
      )}

      {/* Activity Stream */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold">
            Activity Stream
            {(!isRealMode ? revealedMessages.length > 0 : realMessages.length > 0) && (
              <span className="text-muted-foreground font-normal ml-1">({isRealMode ? realMessages.length : revealedMessages.length} messages)</span>
            )}
          </h2>
          {(!isRealMode ? !isComplete : (realTask?.status === "pending" || realTask?.status === "running")) && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              Live
            </div>
          )}
        </div>

        {(!isRealMode ? revealedMessages.length === 0 : realMessages.length === 0) ? (
          <div className="rounded-xl border border-border bg-card p-12 text-center">
            <Play className="h-5 w-5 mx-auto mb-2 text-muted-foreground" />
            <p className="text-xs text-muted-foreground">{isRealMode ? "Waiting for execution output..." : "Starting demo execution..."}</p>
          </div>
        ) : (
          <div className="space-y-4">
            {(!isRealMode ? revealedMessages : realMessages).map((msg, i) => (
              <div key={msg.id} onClick={!isRealMode && i === revealedMessages.length - 1 && !isComplete ? handleNext : undefined} className={!isRealMode && i === revealedMessages.length - 1 && !isComplete ? "cursor-pointer" : ""}>
                <DemoMessageCard msg={msg} index={i} scenario={isRealMode ? { tokenCounts: [] } as any : scenario} />
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Final Output */}
      {(!isRealMode ? showFinal : (realTask?.status === "completed")) && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-deliver/20 bg-deliver-surface/30 p-5"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              <span className="text-sm font-semibold">Final Delivery</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-emerald-400">
              <CheckCircle2 className="h-3.5 w-3.5" />
              {isRealMode ? "Completed successfully" : "Completed in ~12 seconds"}
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
            <Zap className="h-3 w-3" />
            Total: {isRealMode ? (realExecution?.total_tokens ?? 0) : totalTokens} tokens generated
          </div>
          <pre className="rounded-lg border border-deliver/20 bg-surface/50 p-4 text-xs leading-relaxed overflow-x-auto whitespace-pre-wrap font-mono text-muted-foreground">
            {(() => {
              const delivery = (!isRealMode ? revealedMessages : realMessages).find((m) => m.message_type === "delivery");
              if (!delivery) return "";
              try {
                const start = delivery.content.indexOf("{");
                const end = delivery.content.lastIndexOf("}") + 1;
                if (start !== -1 && end > start) {
                  return JSON.stringify(JSON.parse(delivery.content.slice(start, end)), null, 2);
                }
              } catch { }
              return delivery.content;
            })()}
          </pre>
        </motion.div>
      )}

      {/* CTA */}
      {(!isRealMode ? isComplete : (realTask?.status === "completed" || realTask?.status === "failed")) && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="rounded-xl border border-border bg-gradient-to-b from-surface to-card p-8 text-center"
        >
          <h3 className="text-base font-semibold mb-2">That&apos;s how AgentForge works.</h3>
          <p className="text-sm text-muted-foreground mb-5 max-w-md mx-auto">
            Define a task. Your AI team plans, builds, reviews, tests, and delivers. All in under 60 seconds.
          </p>
          <div className="flex items-center justify-center gap-3">
            <Link href="/dashboard">
              <Button size="lg">
                Build Your Team
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/">
              <Button variant="outline" size="lg">
                Back to home
              </Button>
            </Link>
          </div>
        </motion.div>
      )}
    </div>
  );
}
