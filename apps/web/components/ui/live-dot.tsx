import * as React from "react";
import { Dot } from "lucide-react";
import { cn } from "@/lib/utils";

interface LiveDotProps {
  className?: string;
  size?: "sm" | "md" | "lg";
  color?: "default" | "success" | "warning" | "error";
  pulse?: boolean;
}

export function LiveDot({
  className,
  size = "md",
  color = "default",
  pulse = false,
}: LiveDotProps) {
  const sizeMap = {
    sm: "h-2.5 w-2.5",
    md: "h-3 w-3",
    lg: "h-3.5 w-3.5",
  };

  const colorMap = {
    default: "bg-primary",
    success: "bg-success",
    warning: "bg-warning",
    error: "bg-destructive",
  };

  const baseClasses = "flex h-3 w-3 items-center justify-center shrink-0";
  const sizeClass = sizeMap[size];
  const colorClass = colorMap[color];
  const pulseClass = pulse ? "animate-ping" : "";

  return (
    <span
      className={cn(
        baseClasses,
        sizeClass,
        colorClass,
        pulseClass,
        className
      )}
    >
      {pulse ? (
        <Dot className="h-2 w-2 fill-white" />
      ) : (
        <Dot className="h-2 w-2" />
      )}
    </span>
  );
}
