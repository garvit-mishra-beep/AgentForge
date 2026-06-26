"use client";

import { use, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { getTeam, addTeamMember, removeTeamMember, listApiKeys } from "@/lib/api";
import type { Team, ApiKey } from "@/lib/types";
import type { AgentRole, ProviderName } from "@/lib/constants";
import { AGENT_CONFIG, PROVIDER_CONFIG } from "@/lib/constants";
import { OrgChart } from "@/components/org-chart";
import { ArrowLeft, Loader2, Plus, Trash2, Check, Sparkles, Shield } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { useToast } from "@/components/ui/toast";

function buildModelsFromEnabledProviders(apiKeys: ApiKey[]): { name: string; size: string; tag: string; provider: string }[] {
  const enabled: ProviderName[] = apiKeys
    .filter((k) => k.is_enabled)
    .map((k) => k.provider as ProviderName);
  // Ollama is always available (no key needed)
  if (!enabled.includes("ollama")) enabled.push("ollama");

  const models: { name: string; size: string; tag: string; provider: string }[] = [];
  for (const provider of enabled) {
    const config = PROVIDER_CONFIG[provider];
    if (config) {
      for (const m of config.models) {
        models.push({ ...m, provider: config.label });
      }
    }
  }
  return models;
}

const ALL_ROLES: AgentRole[] = ["team_lead", "builder", "reviewer", "tester"];

export default function TeamDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { toast } = useToast();
  const { id } = use(params);
  const [team, setTeam] = useState<Team | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedRole, setSelectedRole] = useState<AgentRole | null>(null);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);

  const filteredModels = useMemo(() => buildModelsFromEnabledProviders(apiKeys), [apiKeys]);

  async function load() {
    try {
      const [t, k] = await Promise.all([getTeam(id), listApiKeys().catch(() => [] as ApiKey[])]);
      setTeam(t);
      setApiKeys(k);
    } catch {
      toast("Failed to load team", { type: "error" });
    }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, [id]);

  async function handleAssign(role: string, model: string) {
    try {
      await addTeamMember(id, { role, model });
      toast(`${role} assigned to ${model}`, { type: "success" });
      await load();
    } catch (err) {
      toast("Failed to assign model", { type: "error" });
    }
  }

  async function handleRemove(memberId: string) {
    try {
      await removeTeamMember(id, memberId);
      toast("Model removed", { type: "success" });
      await load();
    } catch (err) {
      toast("Failed to remove model", { type: "error" });
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        Loading team...
      </div>
    );
  }

  if (!team) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <p className="text-sm">Team not found</p>
        <Link href="/teams" className="text-primary text-sm mt-2 hover:underline">Back to teams</Link>
      </div>
    );
  }

  const roleMap = Object.fromEntries(team.members.map((m) => [m.role, m]));
  const isComplete = team.members.length >= 3;

  return (
    <div className="space-y-8">
      <div>
        <Link href="/teams" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors mb-3">
          <ArrowLeft className="h-3 w-3" />
          Back to teams
        </Link>
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-xl font-bold tracking-tight">{team.name}</h1>
          {isComplete ? (
            <Badge variant="success">Ready</Badge>
          ) : (
            <Badge variant="warning">{team.members.length}/{ALL_ROLES.length} roles</Badge>
          )}
        </div>
        {team.description && (
          <p className="text-sm text-muted-foreground">{team.description}</p>
        )}
      </div>

      {/* Org Chart */}
      <div className="rounded-xl border border-border bg-card p-8">
        <OrgChart
          nodes={team.members.map((m) => ({
            role: m.role as AgentRole,
            model: m.model,
          }))}
          interactive
          onNodeClick={(role) => setSelectedRole(role)}
        />
      </div>

      {/* Role Assignment */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {ALL_ROLES.map((roleKey) => {
          const member = roleMap[roleKey];
          const config = AGENT_CONFIG[roleKey];
          const Icon = config.icon;
          const isSelected = selectedRole === roleKey;

          return (
            <motion.div
              key={roleKey}
              layout
              className={cn(
                "rounded-xl border p-4 transition-all",
                isSelected ? "border-primary/40 bg-surface" : "border-border bg-card",
                "hover:border-border-hover",
              )}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className={cn(
                  "flex h-9 w-9 items-center justify-center rounded-lg border-2",
                  config.border, config.bgSurface,
                )}>
                  <Icon className={cn("h-4 w-4", config.text)} />
                </div>
                <div>
                  <Badge variant={config.badgeVariant}>{config.label}</Badge>
                  <p className="text-[10px] text-muted-foreground mt-0.5">
                    {roleKey === "team_lead" ? "Coordinates the team" : roleKey === "builder" ? "Writes code" : roleKey === "reviewer" ? "Reviews output" : "Tests code"}
                  </p>
                </div>
              </div>

              {member ? (
                <div className="flex items-center justify-between rounded-lg border border-border bg-surface/50 px-3 py-2 mb-3">
                  <div className="flex items-center gap-2 min-w-0">
                    <Check className={cn("h-3.5 w-3.5 shrink-0", config.text)} />
                    <code className="text-xs font-mono truncate">{member.model}</code>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemove(member.id)}
                    className="text-muted-foreground hover:text-destructive transition-colors cursor-pointer shrink-0 ml-2"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ) : (
                <p className="text-xs text-muted-foreground mb-3">No model assigned</p>
              )}

              <div className="space-y-1.5">
                <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">Select Model</p>
                <div className="flex flex-wrap gap-1.5">
                  {filteredModels.length === 0 && (
                    <p className="text-[10px] text-muted-foreground w-full">No providers enabled. <Link href="/settings/providers" className="text-primary hover:underline">Add API keys</Link></p>
                  )}
                  {filteredModels.map((m) => (
                    <button
                      key={m.name}
                      type="button"
                      onClick={() => handleAssign(roleKey, m.name)}
                      className={cn(
                        "flex items-center gap-1 rounded-lg border px-2 py-1 text-[10px] transition-all cursor-pointer",
                        member?.model === m.name
                          ? `${config.border} ${config.bgSurface} ${config.text}`
                          : "border-border text-muted-foreground hover:border-border-hover hover:text-foreground",
                      )}
                    >
                      <code className="font-mono">{m.name}</code>
                      <span className="opacity-60">({m.size})</span>
                      {"provider" in m && (
                        <span className="ml-0.5 text-[8px] opacity-50 font-sans">{m.provider}</span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      <Separator />

      <div className="flex gap-2">
        <Link href={`/tasks?team=${team.id}`}>
          <Button disabled={!isComplete}>
            <Sparkles className="h-4 w-4" />
            Create Task with This Team
          </Button>
        </Link>
      </div>
    </div>
  );
}
