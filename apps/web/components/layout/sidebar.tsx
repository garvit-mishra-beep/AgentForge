"use client";

import { cn } from "@/lib/utils";
import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  LayoutDashboard,
  FolderKanban,
  Users,
  ListChecks,
  Activity,
  LayoutTemplate,
  BarChart3,
  Settings,
  ChevronLeft,
  Sparkles,
  Menu,
  Play,
  Zap,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

const NAV_ITEMS: { href: string; label: string; icon: LucideIcon }[] = [
  { href: "/dashboard", label: "Mission Control", icon: LayoutDashboard },
  { href: "/demo", label: "Demo", icon: Play },
  { href: "/review", label: "Quick Review", icon: Zap },
  { href: "/benchmark", label: "Benchmark", icon: BarChart3 },
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/teams", label: "Teams", icon: Users },
  { href: "/tasks", label: "Tasks", icon: ListChecks },
  { href: "/executions", label: "Executions", icon: Activity },
  { href: "/analytics", label: "Analytics", icon: TrendingUp },
  { href: "/templates", label: "Templates", icon: LayoutTemplate },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("agentforge_sidebar_collapsed");
    if (saved !== null) {
      setCollapsed(saved === "true");
    }
  }, []);

  const handleToggleCollapse = () => {
    const nextVal = !collapsed;
    setCollapsed(nextVal);
    localStorage.setItem("agentforge_sidebar_collapsed", String(nextVal));
  };

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  return (
    <TooltipProvider>
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="fixed top-3 left-3 z-[70] flex sm:hidden h-8 w-8 items-center justify-center rounded-lg bg-sidebar text-sidebar-foreground hover:bg-sidebar-hover transition-all cursor-pointer"
      >
        <Menu className="h-4 w-4" />
      </button>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setMobileOpen(false)}
            className="fixed inset-0 z-40 bg-black/50 sm:hidden"
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {mobileOpen && (
          <motion.aside
            initial={{ x: -260 }}
            animate={{ x: 0 }}
            exit={{ x: -260 }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed left-0 top-0 z-50 flex h-full w-52 flex-col border-r border-sidebar-border bg-sidebar sm:hidden"
          >
            <div className="flex h-12 items-center gap-2.5 border-b border-sidebar-border px-3">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-primary">
                <Sparkles className="h-3.5 w-3.5 text-primary-foreground" />
              </div>
              <span className="text-sm font-semibold tracking-tight">AgentForge</span>
            </div>
            <nav className="flex-1 space-y-0.5 p-2">
              {NAV_ITEMS.map((item) => {
                const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex h-9 items-center gap-2.5 rounded-lg px-2.5 text-sm transition-all",
                      isActive ? "bg-sidebar-active text-foreground" : "text-sidebar-foreground hover:bg-sidebar-hover hover:text-sidebar-foreground-hover",
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </motion.aside>
        )}
      </AnimatePresence>

      <aside
        className={cn(
          "hidden sm:flex relative flex-col border-r border-sidebar-border bg-sidebar transition-all duration-200",
          collapsed ? "w-[60px]" : "w-[240px]",
        )}
      >
        <div className={cn(
          "flex h-12 items-center border-b border-sidebar-border px-3",
          collapsed ? "justify-center" : "gap-2.5",
        )}>
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-primary">
            <Sparkles className="h-3.5 w-3.5 text-primary-foreground" />
          </div>
          <AnimatePresence mode="wait">
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: "auto" }}
                exit={{ opacity: 0, width: 0 }}
                className="text-sm font-semibold tracking-tight whitespace-nowrap overflow-hidden"
              >
                AgentForge
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        <nav className="flex-1 space-y-0.5 p-2">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            const Icon = item.icon;

            return collapsed ? (
              <Tooltip key={item.href} delayDuration={300}>
                <TooltipTrigger asChild>
                  <Link
                    href={item.href}
                    className={cn(
                      "flex h-9 w-9 items-center justify-center rounded-lg transition-all",
                      isActive
                        ? "bg-sidebar-active text-foreground"
                        : "text-sidebar-foreground hover:bg-sidebar-hover hover:text-sidebar-foreground-hover",
                    )}
                  >
                    <Icon className="h-4 w-4" />
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="right" sideOffset={8}>
                  {item.label}
                </TooltipContent>
              </Tooltip>
            ) : (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex h-9 items-center gap-2.5 rounded-lg px-2.5 text-sm transition-all",
                  isActive
                    ? "bg-sidebar-active text-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-hover hover:text-sidebar-foreground-hover",
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-sidebar-border p-2">
          <button
            onClick={handleToggleCollapse}
            className={cn(
              "flex h-7 w-full items-center justify-center rounded-lg text-sidebar-foreground hover:bg-sidebar-hover hover:text-sidebar-foreground-hover transition-all cursor-pointer",
              collapsed && "w-11",
            )}
          >
            <ChevronLeft className={cn("h-3.5 w-3.5 transition-transform", collapsed && "rotate-180")} />
          </button>
        </div>
      </aside>
    </TooltipProvider>
  );
}
