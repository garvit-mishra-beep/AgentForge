"use client";

import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { AGENT_CONFIG, type AgentRole } from "@/lib/constants";

interface ActivityItem {
  id: string;
  role: AgentRole;
  action: string;
  detail?: string;
  timestamp: string;
  status?: "active" | "completed" | "pending";
}

interface ActivityFeedProps {
  items: ActivityItem[];
  className?: string;
}

export function ActivityFeed({ items, className }: ActivityFeedProps) {
  return (
    <div className={cn("space-y-0.5", className)}>
      <AnimatePresence mode="popLayout">
        {items.map((item, i) => {
          const config = AGENT_CONFIG[item.role];
          const isLatest = i === 0;

          return (
            <motion.div
              key={item.id}
              layout
              initial={{ opacity: 0, x: -8, height: 0 }}
              animate={{ opacity: 1, x: 0, height: "auto" }}
              exit={{ opacity: 0, x: 8, height: 0 }}
              transition={{ duration: 0.3, delay: i * 0.05 }}
              className={cn(
                "flex items-start gap-3 rounded-lg px-3 py-2.5 transition-colors",
                isLatest && "bg-surface",
              )}
            >
              {/* Timeline line */}
              <div className="relative flex flex-col items-center pt-1">
                <div
                  className={cn(
                    "h-2 w-2 rounded-full",
                    item.status === "active" && config.text.replace("text-", "bg-"),
                    item.status === "completed" && "bg-emerald-400",
                    (!item.status || item.status === "pending") && "bg-muted-foreground/30",
                  )}
                />
                {i < items.length - 1 && (
                  <div className="mt-1 h-full w-px bg-border" />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0 pb-3">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className={cn("text-xs font-semibold", config.text)}>
                    {config.label}
                  </span>
                  <span className="text-xs text-muted-foreground">{item.action}</span>
                </div>
                {item.detail && (
                  <p className="text-[11px] text-muted-foreground/70 leading-relaxed">
                    {item.detail}
                  </p>
                )}
                <span className="text-[10px] text-muted-foreground/50 mt-1 block">
                  {item.timestamp}
                </span>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
