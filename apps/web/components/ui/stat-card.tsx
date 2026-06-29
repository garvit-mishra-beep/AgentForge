import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const statCardVariants = cva(
  "flex w-full flex-col items-start gap-4 p-6 rounded-lg border border-border bg-background",
  {
    variants: {
      variant: {
        default: "",
        outline: "border-border",
        faint: "bg-muted/50",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

interface StatCardProps extends React.HTMLAttributes<HTMLElement> {
  title: string;
  value: string | number;
  variant?: VariantProps<typeof statCardVariants>;
  trend?: {
    value: number | string;
    isPositive: boolean;
  };
  icon?: React.ReactNode;
  className?: string;
}

export function StatCard({
  className,
  variant,
  title,
  value,
  trend,
  icon,
  ...props
}: StatCardProps) {
  return (
    <div className={cn(statCardVariants(variant), className)} {...props}>
      {icon && (
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-muted/50">
          {icon}
        </div>
      )}
      <div className="flex w-full flex-col items-start gap-2">
        <h3 className="text-sm font-semibold text-muted-foreground">{title}</h3>
        <p className="text-2xl font-semibold">{value}</p>
        {trend && (
          <div className="flex items-center gap-2 text-sm">
            <span className={trend.isPositive ? "text-success" : "text-destructive"}>
              {trend.isPositive ? '+' : '-'}{trend.value}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
