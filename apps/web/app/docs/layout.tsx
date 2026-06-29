"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Sparkles, ChevronRight } from "lucide-react";

const DOCS_NAV = [
  {
    title: "Getting Started",
    items: [
      { label: "Introduction", slug: "" },
      { label: "Onboarding Guide", slug: "getting-started/ONBOARDING" },
      { label: "Local Setup", slug: "getting-started/SETUP" },
    ]
  },
  {
    title: "Architecture",
    items: [
      { label: "System Architecture", slug: "architecture/SYSTEM_ARCHITECTURE" },
      { label: "Technical Specification", slug: "architecture/TECH_SPEC" },
      { label: "Database Schema", slug: "architecture/SCHEMA" },
    ]
  },
  {
    title: "Orchestration & API",
    items: [
      { label: "Agent Orchestration", slug: "agents/AGENT_SYSTEM" },
      { label: "API Reference", slug: "api/API_REFERENCE" },
      { label: "GitHub Integration", slug: "integrations/GITHUB" },
    ]
  },
  {
    title: "Development Guides",
    items: [
      { label: "Coding Conventions", slug: "development/CONVENTIONS" },
      { label: "Developer Experience", slug: "development/DX" },
      { label: "FAQ", slug: "development/FAQ" },
      { label: "Glossary", slug: "development/GLOSSARY" },
      { label: "Observability", slug: "development/OBSERVABILITY" },
      { label: "Performance", slug: "development/PERFORMANCE" },
    ]
  },
  {
    title: "Security & Operations",
    items: [
      { label: "Security Model", slug: "security/SECURITY_MODEL" },
      { label: "Incident Runbook", slug: "security/INCIDENT_RUNBOOK" },
      { label: "Data Privacy", slug: "security/DATA_PRIVACY" },
      { label: "Deployment Guide", slug: "deployment/DEPLOYMENT" },
    ]
  },
  {
    title: "Release & Verification",
    items: [
      { label: "Roadmap", slug: "release/ROADMAP" },
      { label: "Release Readiness", slug: "release/V1_RELEASE_READINESS" },
    ]
  }
];

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      {/* Docs Header */}
      <header className="sticky top-0 z-40 w-full border-b border-border bg-background/85 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-2.5">
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
                <Sparkles className="h-3.5 w-3.5 text-primary-foreground" />
              </div>
              <span className="text-sm font-semibold tracking-tight">AgentForge Docs</span>
            </Link>
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
            <span className="text-xs text-muted-foreground font-medium">v1.0 Production-Ready</span>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="text-xs font-medium text-muted-foreground hover:text-foreground transition-colors">
              Go to Dashboard
            </Link>
          </div>
        </div>
      </header>

      {/* Docs Body Layout */}
      <div className="mx-auto w-full max-w-7xl flex-1 flex px-4 sm:px-6 py-6 gap-8">
        {/* Left Navigation Sidebar */}
        <aside className="hidden md:block w-64 shrink-0 overflow-y-auto pr-4 sticky top-20 h-[calc(100vh-8rem)]">
          <div className="space-y-6">
            {DOCS_NAV.map((section) => (
              <div key={section.title} className="space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70 px-2">
                  {section.title}
                </h4>
                <nav className="space-y-0.5">
                  {section.items.map((item) => {
                    const itemPath = item.slug === "" ? "/docs" : `/docs/${item.slug}`;
                    const isActive = pathname === itemPath;
                    return (
                      <Link
                        key={item.slug}
                        href={itemPath}
                        className={cn(
                          "flex h-8 items-center rounded-md px-2.5 text-xs transition-colors",
                          isActive
                            ? "bg-muted font-medium text-foreground"
                            : "text-muted-foreground hover:bg-muted/40 hover:text-foreground"
                        )}
                      >
                        {item.label}
                      </Link>
                    );
                  })}
                </nav>
              </div>
            ))}
          </div>
        </aside>

        {/* Content Panel */}
        <main className="flex-1 min-w-0 max-w-3xl">
          <div className="border border-border rounded-xl bg-card p-6 sm:p-10 shadow-sm">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
