"use client";

import { cn } from "@/lib/utils";
import { AGENT_CONFIG, type AgentRole, type AgentStatus } from "@/lib/constants";
import { motion } from "framer-motion";
import { ChevronRight } from "lucide-react";
import { STATUS_CONFIG } from "@/lib/constants";
import { Badge } from "@/components/ui/badge";

interface OrgNode {
  role: AgentRole;
  model: string;
  status?: AgentStatus;
  currentTask?: string;
  tokensUsed?: number;
}

interface OrgChartProps {
  nodes: OrgNode[];
  className?: string;
  interactive?: boolean;
  onNodeClick?: (role: AgentRole) => void;
}

export function OrgChart({ nodes, className, interactive, onNodeClick }: OrgChartProps) {
  if (nodes.length === 0) {
    return (
      <div className={cn("flex items-center justify-center py-12 text-sm text-muted-foreground", className)}>
        No agents configured
      </div>
    );
  }

  const nodeMap = new Map(nodes.map((n) => [n.role, n]));
  const lead = nodeMap.get("team_lead");
  const executors = ["builder", "reviewer", "tester"] as AgentRole[];
  const executorNodes = executors.map((r) => nodeMap.get(r)).filter(Boolean) as OrgNode[];

  return (
    <div className={cn("flex flex-col items-center gap-6", className)}>
      {/* Lead layer */}
      {lead && (
        <motion.div
          className="flex flex-col items-center"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <OrgChartNode
            node={lead}
            isLead
            interactive={interactive}
            onClick={() => onNodeClick?.("team_lead")}
          />
        </motion.div>
      )}

      {/* Connector lines */}
      {lead && executorNodes.length > 0 && (
        <div className="flex items-center justify-center gap-2">
          {executorNodes.map((_, i) => (
            <div key={i} className="flex flex-col items-center">
              <div className="h-4 w-px bg-border" />
              <ChevronRight className="h-3 w-3 text-muted-foreground -mt-1 -mb-1 rotate-90" />
            </div>
          ))}
        </div>
      )}

      {/* Execution layer */}
      {executorNodes.length > 0 && (
        <div className="flex items-start gap-4">
          {executorNodes.map((node, i) => (
            <motion.div
              key={node.role}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: i * 0.1 }}
            >
              <OrgChartNode
                node={node}
                interactive={interactive}
                onClick={() => onNodeClick?.(node.role)}
              />
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}

function OrgChartNode({
  node,
  isLead,
  interactive,
  onClick,
}: {
  node: OrgNode;
  isLead?: boolean;
  interactive?: boolean;
  onClick?: () => void;
}) {
  const config = AGENT_CONFIG[node.role];
  const statusCfg = node.status ? STATUS_CONFIG[node.status] : null;
  const Icon = config.icon;

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!interactive}
      className={cn(
        "flex flex-col items-center gap-2 rounded-xl border border-border bg-card p-4 transition-all",
        interactive && "cursor-pointer hover:border-border-hover hover:bg-surface-hover",
        isLead && "px-6 py-4",
        !interactive && "cursor-default",
      )}
    >
      <div className={cn(
        "flex items-center justify-center rounded-xl border-2",
        isLead ? "h-14 w-14" : "h-12 w-12",
        node.status && node.status !== "idle"
          ? `${config.border} ${config.bgSurface}`
          : "border-border bg-surface/50",
      )}>
        <Icon className={cn("h-6 w-6", node.status && node.status !== "idle" ? config.text : "text-muted-foreground")} />
      </div>
      <div className="text-center">
        <div className="flex items-center justify-center gap-1.5 mb-0.5">
          <Badge variant={config.badgeVariant}>{config.label}</Badge>
          {statusCfg && (
            <span className={cn("text-[10px] font-medium", statusCfg.color)}>
              {statusCfg.label}
            </span>
          )}
        </div>
        <code className={cn("block font-mono", isLead ? "text-xs" : "text-[11px]", "text-muted-foreground")}>
          {node.model}
        </code>
        {node.currentTask && (
          <p className="text-[10px] text-muted-foreground/70 mt-1 truncate max-w-[120px]">
            {node.currentTask}
          </p>
        )}
      </div>
    </button>
  );
}
