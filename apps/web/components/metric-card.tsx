"use client";

import { cn } from "@/lib/utils";
import { type LucideIcon } from "lucide-react";
import { motion } from "framer-motion";

interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  sublabel?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  className?: string;
}

export function MetricCard({ icon: Icon, label, value, sublabel, trend, trendValue, className }: MetricCardProps) {
  return (
    <motion.div
      className={cn(
        "rounded-xl border border-border bg-card p-4 hover:border-border-hover transition-all",
        className,
      )}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface">
          <Icon className="h-4 w-4 text-muted-foreground" />
        </div>
        {trend && (
          <span
            className={cn(
              "text-[11px] font-medium",
              trend === "up" && "text-builder",
              trend === "down" && "text-destructive",
              trend === "neutral" && "text-muted-foreground",
            )}
          >
            {trendValue}
          </span>
        )}
      </div>
      <div className="text-2xl font-bold tracking-tight">{value}</div>
      <div className="text-xs text-muted-foreground mt-0.5">{label}</div>
      {sublabel && (
        <div className="text-[10px] text-muted-foreground/60 mt-1">{sublabel}</div>
      )}
    </motion.div>
  );
}
