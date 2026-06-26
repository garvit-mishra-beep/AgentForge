"use client";

import { cn } from "@/lib/utils";
import { AGENT_CONFIG, type AgentRole, type AgentStatus } from "@/lib/constants";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";

interface AgentNetworkProps {
  agents: {
    id: string;
    role: AgentRole;
    model: string;
    status: AgentStatus;
    current_task?: string;
    tokens_used?: number;
  }[];
  className?: string;
}

export function AgentNetwork({ agents, className }: AgentNetworkProps) {
  if (agents.length === 0) return null;

  return (
    <div className={cn("space-y-2", className)}>
      {agents.map((agent, i) => {
        const config = AGENT_CONFIG[agent.role];
        const Icon = config.icon;
        const isActive = agent.status !== "idle";

        return (
          <motion.div
            key={agent.id}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: i * 0.05 }}
            className={cn(
              "flex items-center gap-3 rounded-lg border px-3 py-2.5 transition-all",
              isActive ? `${config.border} ${config.bgSurface}` : "border-border bg-card",
            )}
          >
            <div className={cn(
              "flex h-8 w-8 items-center justify-center rounded-lg border-2",
              isActive ? `${config.border} ${config.bg}` : "border-border bg-surface/50",
            )}>
              <Icon className={cn("h-4 w-4", isActive ? config.text : "text-muted-foreground")} />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <Badge variant={config.badgeVariant}>{config.label}</Badge>
                <span className={cn(
                  "text-[10px] font-medium",
                  isActive ? config.text : "text-muted-foreground",
                )}>
                  {agent.status.charAt(0).toUpperCase() + agent.status.slice(1)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <code className="text-[10px] font-mono text-muted-foreground truncate">{agent.model}</code>
                {agent.tokens_used !== undefined && (
                  <span className="text-[9px] font-mono text-muted-foreground/60">
                    {agent.tokens_used} tok
                  </span>
                )}
              </div>
              {agent.current_task && (
                <p className="text-[10px] text-muted-foreground/70 mt-0.5 truncate">
                  {agent.current_task}
                </p>
              )}
            </div>

            {isActive && (
              <motion.div
                className="flex gap-0.5"
                animate={{ opacity: [0.4, 1, 0.4] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                <span className={cn("h-1 w-1 rounded-full", config.text.replace("text-", "bg-"))} />
                <span className={cn("h-1 w-1 rounded-full", config.text.replace("text-", "bg-"))} />
                <span className={cn("h-1 w-1 rounded-full", config.text.replace("text-", "bg-"))} />
              </motion.div>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}
