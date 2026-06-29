import * as React from "react";
import { Activity, Sparkles, AlertTriangle, Zap } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  icon?: keyof typeof ICONS;
  className?: string;
}

const ICONS = {
  activity: Activity,
  sparkles: Sparkles,
  warning: AlertTriangle,
  zap: Zap,
};

export function EmptyState({
  title,
  description,
  action,
  icon = "sparkles",
  className,
}: EmptyStateProps) {
  const Icon = ICONS[icon] ?? Sparkles;

  return (
    <div className={className}>
      <div className="flex h-[96px] w-full items-center justify-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <div className="text-center space-y-4">
        <h3 className="text-lg font-semibold">{title}</h3>
        {description && (
          <p className="text-sm text-muted-foreground max-w-xl mx-auto">
            {description}
          </p>
        )}
        {action && (
          <div className="mt-4 space-x-3">
            {typeof action === "string" ? (
              <button className="btn btn-primary">{action}</button>
            ) : (
              action
            )}
          </div>
        )}
      </div>
    </div>
  );
}
