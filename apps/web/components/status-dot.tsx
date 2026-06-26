"use client";

import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface StatusDotProps {
  status: "active" | "idle" | "error" | "completed" | "pending";
  size?: "sm" | "md" | "lg";
  pulse?: boolean;
}

const dotColors = {
  active: "bg-builder",
  idle: "bg-muted-foreground",
  error: "bg-destructive",
  completed: "bg-emerald-400",
  pending: "bg-amber-400",
};

const sizes = {
  sm: "h-1.5 w-1.5",
  md: "h-2 w-2",
  lg: "h-2.5 w-2.5",
};

export function StatusDot({ status, size = "md", pulse }: StatusDotProps) {
  return (
    <motion.span
      className={cn("inline-block rounded-full", sizes[size], dotColors[status])}
      animate={pulse ? { opacity: [0.5, 1, 0.5] } : undefined}
      transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
    />
  );
}
