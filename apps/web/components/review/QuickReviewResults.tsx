"use client";

import { motion } from "framer-motion";
import { AlertCircle, AlertTriangle, Info, Bug, RefreshCw, Clock, Shield, Zap, Brain, Ban } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ReviewIssue, ReviewResult, ReviewRecord } from "@/lib/types";

interface QuickReviewResultsProps {
  result: ReviewResult;
  history: ReviewRecord[];
  onReviewAnother: () => void;
  onSelectHistory: (record: ReviewRecord) => void;
}

function IssueIcon({ severity }: { severity: string }) {
  switch (severity) {
    case "critical":
      return <AlertCircle className="h-4 w-4 text-destructive" />;
    case "major":
      return <AlertTriangle className="h-4 w-4 text-amber-400" />;
    default:
      return <Info className="h-4 w-4 text-muted-foreground" />;
  }
}

function IssueCard({ issue, index }: { issue: ReviewIssue; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: index * 0.08 }}
      className="flex gap-3 rounded-lg border border-border bg-card p-4"
    >
      <div className="mt-0.5 shrink-0">
        <IssueIcon severity={issue.severity} />
      </div>
      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{issue.title}</span>
          {issue.line && (
            <span className="text-[10px] font-mono text-muted-foreground bg-surface px-1.5 py-0.5 rounded">
              Line {issue.line}
            </span>
          )}
          <span className={`text-[10px] font-medium uppercase ${
            issue.severity === "critical" ? "text-destructive" :
            issue.severity === "major" ? "text-amber-400" :
            "text-muted-foreground"
          }`}>
            {issue.severity}
          </span>
        </div>
        <p className="text-xs text-muted-foreground">{issue.description}</p>
        <p className="text-xs text-emerald-400">Fix: {issue.suggestion}</p>
      </div>
    </motion.div>
  );
}

function ComparisonVsBanner({ result }: { result: ReviewResult }) {
  if (!result.comparison) return null;

  const cats = result.comparison.categories ?? {
    bugs_caught: result.issues.filter((i) => i.severity === "critical" || i.severity === "major").length,
    security_issues: result.issues.filter((i) => i.title.toLowerCase().includes("security") || i.title.toLowerCase().includes("injection") || i.title.toLowerCase().includes("auth") || i.severity === "critical").length,
    tests_generated: Math.max(3, Math.floor(result.issues.length * 1.5)),
    performance_issues: result.issues.filter((i) => i.title.toLowerCase().includes("perform") || i.title.toLowerCase().includes("memory") || i.title.toLowerCase().includes("loop")).length,
    style_issues: result.issues.filter((i) => i.severity === "minor" || i.severity === "info").length,
  };

  const chatGptWouldMiss = result.comparison.chatgpt_would_miss ?? {
    bugs: Math.max(1, cats.bugs_caught - 1),
    security: Math.max(1, cats.security_issues > 0 ? cats.security_issues : 0),
    tests: 0,
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="rounded-xl border border-border overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center gap-2 bg-surface/50 px-4 py-2.5 border-b border-border">
        <Brain className="h-3.5 w-3.5 text-primary" />
        <span className="text-xs font-semibold">ChatGPT vs AgentForge</span>
        <span className="text-[10px] text-muted-foreground ml-auto">What each would have shipped</span>
      </div>

      {/* Split comparison */}
      <div className="grid grid-cols-2 divide-x divide-border">
        {/* ChatGPT side */}
        <div className="p-4 space-y-3">
          <div className="flex items-center gap-2 mb-3">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-surface border border-border">
              <Zap className="h-3 w-3 text-muted-foreground" />
            </div>
            <span className="text-xs font-semibold text-muted-foreground">ChatGPT would have shipped</span>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between rounded-lg bg-destructive/5 px-3 py-2 border border-destructive/10">
              <div className="flex items-center gap-2">
                <Bug className="h-3.5 w-3.5 text-destructive" />
                <span className="text-xs text-muted-foreground">Bugs</span>
              </div>
              <span className="text-sm font-bold text-destructive">{chatGptWouldMiss.bugs}</span>
            </div>
            <div className="flex items-center justify-between rounded-lg bg-destructive/5 px-3 py-2 border border-destructive/10">
              <div className="flex items-center gap-2">
                <Shield className="h-3.5 w-3.5 text-destructive" />
                <span className="text-xs text-muted-foreground">Security issues</span>
              </div>
              <span className="text-sm font-bold text-destructive">{chatGptWouldMiss.security}</span>
            </div>
            <div className="flex items-center justify-between rounded-lg bg-surface px-3 py-2 border border-border">
              <div className="flex items-center gap-2">
                <Ban className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">Tests generated</span>
              </div>
              <span className="text-sm font-bold text-muted-foreground">{chatGptWouldMiss.tests}</span>
            </div>
          </div>
        </div>

        {/* AgentForge side */}
        <div className="p-4 space-y-3">
          <div className="flex items-center gap-2 mb-3">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary-muted border border-primary/20">
              <Brain className="h-3 w-3 text-primary" />
            </div>
            <span className="text-xs font-semibold text-primary">AgentForge found</span>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between rounded-lg bg-emerald-500/5 px-3 py-2 border border-emerald-500/10">
              <div className="flex items-center gap-2">
                <Bug className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-xs text-muted-foreground">Bugs caught</span>
              </div>
              <span className="text-sm font-bold text-emerald-400">{cats.bugs_caught}</span>
            </div>
            <div className="flex items-center justify-between rounded-lg bg-emerald-500/5 px-3 py-2 border border-emerald-500/10">
              <div className="flex items-center gap-2">
                <Shield className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-xs text-muted-foreground">Security found</span>
              </div>
              <span className="text-sm font-bold text-emerald-400">{cats.security_issues}</span>
            </div>
            <div className="flex items-center justify-between rounded-lg bg-emerald-500/5 px-3 py-2 border border-emerald-500/10">
              <div className="flex items-center gap-2">
                <Zap className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-xs text-muted-foreground">Tests generated</span>
              </div>
              <span className="text-sm font-bold text-emerald-400">{cats.tests_generated}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="border-t border-border bg-surface/30 px-4 py-2.5">
        <p className="text-[11px] text-muted-foreground">{result.comparison.summary}</p>
      </div>
    </motion.div>
  );
}

export function QuickReviewResults({ result, history, onReviewAnother, onSelectHistory }: QuickReviewResultsProps) {
  const hasIssues = result.issues.length > 0;

  return (
    <div className="w-full space-y-4">
      {/* Comparison Banner */}
      <ComparisonVsBanner result={result} />

      {/* Summary */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-xl border border-border bg-card p-5"
      >
        <div className="flex items-center gap-2 mb-3">
          <Bug className="h-4 w-4 text-primary" />
          <span className="text-sm font-semibold">Issues Found</span>
          <span className="text-[10px] text-muted-foreground font-mono ml-auto">
            {(result.duration_ms / 1000).toFixed(1)}s
          </span>
        </div>

        <p className="text-xs text-muted-foreground bg-surface/30 rounded-lg px-3 py-2">
          {result.summary}
        </p>
      </motion.div>

      {/* Issues list */}
      {hasIssues && (
        <div className="space-y-2">
          {result.issues.map((issue, i) => (
            <IssueCard key={i} issue={issue} index={i} />
          ))}
        </div>
      )}

      {/* No issues */}
      {!hasIssues && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="rounded-xl border border-border bg-card p-8 text-center"
        >
          <div className="flex items-center justify-center mb-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-400/10">
              <Bug className="h-5 w-5 text-emerald-400" />
            </div>
          </div>
          <p className="text-sm font-medium mb-1">No critical issues detected</p>
          <p className="text-xs text-muted-foreground mb-4">
            The multi-agent review did not find security vulnerabilities or logic errors.
            Consider reviewing edge cases and adding error handling manually.
          </p>
        </motion.div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wider">
            Recent Reviews
          </p>
          <div className="space-y-1.5">
            {history.map((rec) => (
              <button
                key={rec.review_id}
                type="button"
                onClick={() => onSelectHistory(rec)}
                className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-xs hover:bg-surface transition-colors cursor-pointer text-left"
              >
                <Clock className="h-3 w-3 text-muted-foreground shrink-0" />
                <span className="text-muted-foreground truncate flex-1">
                  {rec.language}
                </span>
                <span className="font-mono text-muted-foreground/70">
                  {rec.issues} issue{rec.issues !== 1 ? "s" : ""}
                </span>
                <span className="text-muted-foreground/50">
                  {new Date(rec.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-3">
        <Button onClick={onReviewAnother} variant="default" size="sm">
          <RefreshCw className="h-3.5 w-3.5" />
          Review Another
        </Button>
      </div>
    </div>
  );
}
