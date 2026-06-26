"use client";

import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { AGENT_CONFIG, type AgentRole } from "@/lib/constants";
import { Badge } from "@/components/ui/badge";

interface ProgressItem {
  id: string;
  role: AgentRole;
  action: string;
  detail?: string;
  tokens?: number;
  timestamp: string;
}

interface ProgressStreamProps {
  items: ProgressItem[];
  className?: string;
}

export function ProgressStream({ items, className }: ProgressStreamProps) {
  return (
    <div className={cn("space-y-3", className)}>
      <AnimatePresence mode="popLayout">
        {items.map((item) => {
          const config = AGENT_CONFIG[item.role];
          const Icon = config.icon;

          return (
            <motion.div
              key={item.id}
              layout
              initial={{ opacity: 0, y: 12, height: 0 }}
              animate={{ opacity: 1, y: 0, height: "auto" }}
              exit={{ opacity: 0, y: -12, height: 0 }}
              transition={{ duration: 0.3 }}
              className="relative pl-6"
            >
              <div className="absolute left-0 top-1 flex items-center justify-center">
                <div className={cn(
                  "flex h-4 w-4 items-center justify-center rounded-full",
                  config.bgSurface,
                )}>
                  <Icon className="h-2.5 w-2.5" style={{ color: config.color }} />
                </div>
              </div>
              <div className={cn(
                "rounded-lg border px-3 py-2",
                "border-border bg-card",
              )}>
                <div className="flex items-center gap-2 mb-0.5">
                  <Badge variant={config.badgeVariant}>{config.label}</Badge>
                  <span className="text-xs text-foreground">{item.action}</span>
                  {item.tokens !== undefined && (
                    <span className="text-[9px] font-mono text-muted-foreground/60 ml-auto">
                      {item.tokens} tok
                    </span>
                  )}
                </div>
                {item.detail && (
                  <p className="text-[11px] text-muted-foreground leading-relaxed">{item.detail}</p>
                )}
                <span className="text-[9px] text-muted-foreground/50 mt-1 block">{item.timestamp}</span>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
