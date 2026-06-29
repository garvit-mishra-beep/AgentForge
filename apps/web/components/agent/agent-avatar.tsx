"use client";

import { AGENT_CONFIG, type AgentRole, STATUS_CONFIG, type AgentStatus } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface AgentAvatarProps {
  role: AgentRole;
  status?: AgentStatus;
  size?: "sm" | "md" | "lg" | "xl";
  showLabel?: boolean;
  showStatus?: boolean;
  animated?: boolean;
  model?: string;
}

const sizeMap = {
  sm: { avatar: "h-7 w-7", icon: "h-3.5 w-3.5", badge: "text-[9px]" },
  md: { avatar: "h-9 w-9", icon: "h-4 w-4", badge: "text-[10px]" },
  lg: { avatar: "h-12 w-12", icon: "h-5 w-5", badge: "text-[11px]" },
  xl: { avatar: "h-16 w-16", icon: "h-7 w-7", badge: "text-xs" },
};

export function AgentAvatar({ role, status, size = "md", showLabel, showStatus, animated, model }: AgentAvatarProps) {
  const config = AGENT_CONFIG[role];
  const statusCfg = status ? STATUS_CONFIG[status] : null;
  const Icon = config.icon;
  const s = sizeMap[size];

  return (
    <motion.div
      className="flex flex-col items-center gap-1"
      initial={animated ? { opacity: 0, scale: 0.9 } : undefined}
      animate={animated ? { opacity: 1, scale: 1 } : undefined}
      transition={{ duration: 0.3 }}
    >
      <div className="relative">
        <div
          className={cn(
            "flex items-center justify-center rounded-xl border-2 transition-all duration-300",
            s.avatar,
            status && status !== "idle"
              ? `${config.border} ${config.bgSurface}`
              : "border-border bg-surface/50",
          )}
        >
          <Icon className={cn(s.icon, status && status !== "idle" ? config.text : "text-muted-foreground")} />
        </div>
        {statusCfg && showStatus && (
          <motion.div
            className={cn(
              "absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-background",
              statusCfg.dot,
            )}
            animate={status === "planning" || status === "building" || status === "reviewing" ? { scale: [1, 1.3, 1] } : undefined}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
        )}
      </div>
      {showLabel && (
        <span className={cn("font-semibold", s.badge, status && status !== "idle" ? config.text : "text-muted-foreground")}>
          {config.label}
        </span>
      )}
      {model && (
        <span className={cn("font-mono text-muted-foreground", s.badge === "text-[9px]" ? "text-[8px]" : "text-[9px]")}>
          {model}
        </span>
      )}
    </motion.div>
  );
}
