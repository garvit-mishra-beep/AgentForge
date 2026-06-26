"use client";

import { motion } from "framer-motion";
import type { ReviewStatus } from "@/lib/types";

interface StageInfo {
  status: ReviewStatus;
  label: string;
  barWidth: string;
}

const STAGES: StageInfo[] = [
  { status: "queued", label: "Queued...", barWidth: "5%" },
  { status: "analyzing", label: "Analyzing code with single pass...", barWidth: "40%" },
  { status: "reviewing", label: "Multi-agent review in progress...", barWidth: "75%" },
  { status: "completed", label: "Review complete", barWidth: "100%" },
];

function getStageIndex(status: ReviewStatus): number {
  const idx = STAGES.findIndex((s) => s.status === status);
  return idx >= 0 ? idx : 0;
}

interface QuickReviewProgressProps {
  status: ReviewStatus;
  elapsed: number;
}

export function QuickReviewProgress({ status, elapsed }: QuickReviewProgressProps) {
  const activeIndex = getStageIndex(status);

  return (
    <div className="w-full space-y-4 py-6">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">
          {status === "failed" ? "Review failed" : STAGES[activeIndex]?.label ?? "Processing..."}
        </span>
        <span className="font-mono text-xs text-muted-foreground">{elapsed.toFixed(0)}s</span>
      </div>

      <div className="relative h-2 rounded-full bg-surface overflow-hidden">
        <motion.div
          className={`absolute inset-y-0 left-0 rounded-full ${
            status === "failed"
              ? "bg-destructive"
              : "bg-gradient-to-r from-lead via-builder to-reviewer"
          }`}
          initial={{ width: "0%" }}
          animate={{ width: status === "failed" ? "100%" : STAGES[activeIndex]?.barWidth ?? "5%" }}
          transition={{ duration: 0.5 }}
        />
      </div>

      <div className="space-y-2">
        {STAGES.map((stage, i) => {
          const isActive = i === activeIndex;
          const isDone = i < activeIndex;
          const isFailed = status === "failed";

          return (
            <div key={stage.status} className="flex items-center gap-2 text-xs">
              <div
                className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                  isFailed && isActive
                    ? "bg-destructive"
                    : isDone
                      ? "bg-emerald-400"
                      : isActive
                        ? "bg-primary animate-pulse"
                        : "bg-muted-foreground/30"
                }`}
              />
              <span
                className={`${
                  isFailed && isActive
                    ? "text-destructive"
                    : isDone
                      ? "text-emerald-400"
                      : isActive
                        ? "text-foreground"
                        : "text-muted-foreground/50"
                }`}
              >
                {isFailed && isActive ? "Failed" : isDone ? "Done" : stage.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
