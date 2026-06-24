"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  Brain,
  Workflow,
  BarChart3,
  Settings,
  Home,
  FileText,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Home", icon: Home },
  { href: "/agents", label: "Agents", icon: Brain },
  { href: "/workflows", label: "Workflows", icon: Workflow },
  { href: "/observability", label: "Observability", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r bg-card">
      <div className="flex h-14 items-center gap-2 border-b px-6">
        <Brain className="h-6 w-6 text-primary" />
        <span className="font-bold text-lg">AgentForge</span>
      </div>
      <nav className="space-y-1 p-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="absolute bottom-4 left-4 right-4">
        <div className="rounded-lg border bg-muted/50 p-3 text-xs text-muted-foreground">
          <FileText className="mb-1 h-4 w-4" />
          <p className="font-medium">AgentForge AI v0.1.0</p>
          <p>Build, Deploy, Scale AI Agents</p>
        </div>
      </div>
    </aside>
  );
}
