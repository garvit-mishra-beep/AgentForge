"use client";

import { cn } from "@/lib/utils";
import { EXECUTION_STEPS } from "@/lib/constants";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Loader2 } from "lucide-react";
import type { AgentRole } from "@/lib/constants";
import { AGENT_CONFIG } from "@/lib/constants";

interface ExecutionGraphProps {
  currentNode: string | null;
  isComplete: boolean;
  className?: string;
}

export function ExecutionGraph({ currentNode, isComplete, className }: ExecutionGraphProps) {
  const activeIndex = EXECUTION_STEPS.findIndex((s) => s.node === currentNode);

  return (
    <div className={cn("flex items-center justify-center gap-1", className)}>
      {EXECUTION_STEPS.map((step, i) => {
        const isActive = i === activeIndex;
        const isPast = i < activeIndex || isComplete;
        const agent = step.agent as AgentRole;
        const config = AGENT_CONFIG[agent];

        return (
          <div key={step.node} className="flex items-center gap-1">
            <motion.div
              className="flex flex-col items-center gap-1"
              animate={isActive ? { scale: 1.05 } : { scale: 1 }}
              transition={{ duration: 0.3 }}
            >
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-lg border-2 transition-all duration-300",
                  isPast
                    ? "border-emerald-400/30 bg-emerald-400/10"
                    : isActive
                    ? `${config.border} ${config.bg}`
                    : "border-border bg-surface/50",
                )}
              >
                {isPast ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                ) : isActive ? (
                  <div className={config.text}>
                    <Loader2 className="h-4 w-4 animate-spin" />
                  </div>
                ) : (
                  <div className={cn("h-4 w-4 rounded-full bg-muted-foreground/20")} />
                )}
              </div>
              <span
                className={cn(
                  "text-[10px] font-medium transition-colors",
                  isPast ? "text-emerald-400" : isActive ? config.text : "text-muted-foreground/50",
                )}
              >
                {step.label}
              </span>
            </motion.div>
            {i < EXECUTION_STEPS.length - 1 && (
              <div
                className={cn(
                  "w-8 sm:w-12 h-px transition-colors duration-500",
                  isPast ? "bg-emerald-400/40" : isActive ? "bg-border-hover" : "bg-border",
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
