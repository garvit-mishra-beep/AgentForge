import React, { useState } from "react";
import { Copy, Check } from "lucide-react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const codeVariants = cva(
  "relative overflow-hidden w-full text-sm text-muted-foreground",
  {
    variants: {
      variant: {
        solid: "bg-muted",
        outline: "border border-muted",
        subtle: "bg-muted/50",
      },
    },
    defaultVariants: {
      variant: "solid",
    },
  }
);

interface CodeBlockProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: VariantProps<typeof codeVariants>["variant"];
}

export function CodeBlock({ className, variant, children, ...props }: CodeBlockProps) {
  const [isCopied, setIsCopied] = useState(false);

  const handleCopy = async () => {
    try {
      const text = String(children ?? '');
      await navigator.clipboard.writeText(text.trim());
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <div className={cn(codeVariants({ variant }), className)} {...props}>
      <code className="block p-4 whitespace-pre">{String(children ?? '').trim()}</code>
      <button
        onClick={handleCopy}
        className={`
          absolute left-2 top-2 flex h-6 w-6 items-center justify-center rounded-md
          text-xs opacity-60
      `}
        aria-label="Copy code"
        disabled={isCopied}
      >
        {isCopied ? (
          <Check className="h-3 w-3" />
        ) : (
          <Copy className="h-3 w-3" />
        )}
      </button>
    </div>
  );
}
