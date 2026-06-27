"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { listTemplates } from "@/lib/api";
import type { Template } from "@/lib/types";
import type { AgentRole } from "@/lib/constants";
import { AGENT_CONFIG } from "@/lib/constants";
import { Loader2, LayoutTemplate, Plus, ChevronRight } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      setTemplates(await listTemplates());
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  const categoryGroups = [
    { label: "Software Engineering", templates: templates.filter((t) => t.category === "engineering" || !t.category) },
    { label: "Startup", templates: templates.filter((t) => t.category === "startup") },
    { label: "Research", templates: templates.filter((t) => t.category === "research") },
  ].filter((g) => g.templates.length > 0);

  const defaultTemplates = !templates.length ? [
    { id: "1", name: "Software Engineering Team", description: "Full-stack development with planning, coding, and review", category: "engineering", roles: [{ role: "team_lead" as AgentRole, model: "gpt-4o-mini" }, { role: "builder" as AgentRole, model: "gpt-4o" }, { role: "reviewer" as AgentRole, model: "gpt-4o-mini" }, { role: "tester" as AgentRole, model: "gpt-4o-mini" }] },
    { id: "2", name: "Startup MVP Team", description: "Fast prototyping with lean models for quick iterations", category: "startup", roles: [{ role: "team_lead" as AgentRole, model: "gpt-4o-mini" }, { role: "builder" as AgentRole, model: "gpt-4o-mini" }, { role: "reviewer" as AgentRole, model: "gpt-4o-mini" }] },
    { id: "3", name: "Code Review Team", description: "Focus on code quality with strong review and testing", category: "engineering", roles: [{ role: "team_lead" as AgentRole, model: "gpt-4o-mini" }, { role: "builder" as AgentRole, model: "gpt-4o" }, { role: "reviewer" as AgentRole, model: "gpt-4o-mini" }] },
  ] : templates;

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Templates</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Pre-configured team structures to jumpstart your work
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin mr-2" />
          Loading templates...
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {defaultTemplates.map((template, i) => (
            <motion.div
              key={template.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.05 }}
            >
              <Link href={`/teams`} className="block group">
                <div className="rounded-xl border border-border bg-card p-5 transition-all hover:border-border-hover hover:bg-surface-hover">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-surface">
                      <LayoutTemplate className="h-5 w-5 text-primary" />
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                  </div>
                  <h3 className="text-sm font-semibold group-hover:text-primary transition-colors mb-1">{template.name}</h3>
                  <p className="text-xs text-muted-foreground mb-3">{template.description}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {template.roles.map((r) => (
                      <Badge key={r.role} variant={AGENT_CONFIG[r.role as AgentRole]?.badgeVariant ?? "default"}>
                        {AGENT_CONFIG[r.role as AgentRole]?.label ?? r.role}
                      </Badge>
                    ))}
                  </div>
                  <div className="mt-2 text-[10px] font-mono text-muted-foreground space-y-0.5">
                    {template.roles.map((r) => (
                      <div key={r.role}>{AGENT_CONFIG[r.role as AgentRole]?.label ?? r.role}: {r.model}</div>
                    ))}
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
