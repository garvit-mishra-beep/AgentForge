"use client";

import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Search, Plus, ChevronRight, Home } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/utils";

const BREADCRUMB_MAP: Record<string, string> = {
  "/": "Home",
  "/dashboard": "Mission Control",
  "/demo": "Demo",
  "/review": "Quick Review",
  "/review/history": "Review History",
  "/benchmark": "Benchmark",
  "/projects": "Projects",
  "/teams": "Teams",
  "/tasks": "Tasks",
  "/executions": "Executions",
  "/templates": "Templates",
  "/analytics": "Analytics",
  "/settings": "Settings",
};

const QUICK_ACTIONS: Record<string, { label: string; href: string }[]> = {
  "/": [
    { label: "New Task", href: "/tasks" },
    { label: "New Team", href: "/teams" },
  ],
  "/teams": [{ label: "New Team", href: "/teams" }],
  "/tasks": [{ label: "New Task", href: "/tasks" }],
  "/projects": [{ label: "New Project", href: "/projects" }],
};

export default function TopBar() {
  const pathname = usePathname();
  const [searchOpen, setSearchOpen] = useState(false);

  const segments = pathname.split("/").filter(Boolean);
  const baseLabel = BREADCRUMB_MAP[`/${segments[0]}`] ?? segments[0] ?? "Mission Control";
  const actions = QUICK_ACTIONS[`/${segments[0]}`] ?? [];

  return (
    <header className="flex h-12 items-center justify-between border-b border-border bg-background/80 backdrop-blur-xl px-4 sm:px-6">
      <div className="flex items-center gap-2 text-sm">
        <Link href="/" className="text-muted-foreground hover:text-foreground transition-colors">
          <Home className="h-4 w-4" />
        </Link>
        {segments.length > 0 && (
          <>
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
            <Link
              href={`/${segments[0]}`}
              className={cn(
                "font-medium transition-colors",
                segments.length === 1 ? "text-foreground" : "text-muted-foreground hover:text-foreground",
              )}
            >
              {baseLabel}
            </Link>
            {segments.length > 1 && (
              <>
                <ChevronRight className="h-3 w-3 text-muted-foreground" />
                <span className="text-foreground font-medium capitalize">
                  {decodeURIComponent(segments[segments.length - 1] ?? "")}
                </span>
              </>
            )}
          </>
        )}
      </div>

      <div className="flex items-center gap-2">
        <AnimatePresence>
          {actions.map((action) => (
            <motion.div
              key={action.href}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
            >
              <Link href={action.href}>
                <Button size="sm" variant="secondary">
                  <Plus className="h-3.5 w-3.5" />
                  {action.label}
                </Button>
              </Link>
            </motion.div>
          ))}
        </AnimatePresence>

        <button
          onClick={() => setSearchOpen(!searchOpen)}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-surface-hover hover:text-foreground transition-all cursor-pointer"
        >
          <Search className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
}
