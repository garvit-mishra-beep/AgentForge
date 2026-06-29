import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

const badgeVariants = {
  default: "bg-primary/10 text-primary border-primary/20",
  secondary: "bg-secondary text-secondary-foreground",
  destructive: "bg-destructive/10 text-destructive border-destructive/20",
  success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  warning: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  lead: "bg-lead-muted text-lead border-lead/20",
  builder: "bg-builder-muted text-builder border-builder/20",
  reviewer: "bg-reviewer-muted text-reviewer border-reviewer/20",
  deliver: "bg-deliver-muted text-deliver border-deliver/20",
  tester: "bg-tester-muted text-tester border-tester/20",
  outline: "text-foreground border-border",
} as const;

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: keyof typeof badgeVariants;
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium leading-none transition-colors",
        badgeVariants[variant],
        className,
      )}
      {...props}
    />
  );
}

export { Badge, type BadgeProps };
