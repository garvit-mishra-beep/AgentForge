import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const kbdVariants = cva(
  "inline-flex items-center justify-center rounded-sm border border-border bg-input px-2 py-1.5 text-xs font-semibold ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "",
        outline: "border-border",
        soft: "bg-muted",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

interface KbdProps extends React.HTMLAttributes<HTMLElement> {
  variant?: VariantProps<typeof kbdVariants>["variant"];
}

export function Kbd({ className, variant, children, ...props }: KbdProps) {
  return (
    <kbd
      className={cn(kbdVariants({ variant }), className)}
      {...props}
    >
      {children}
    </kbd>
  );
}
