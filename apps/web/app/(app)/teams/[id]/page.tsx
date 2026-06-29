"use client";

import { use, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { getTeam, addTeamMember, removeTeamMember, listApiKeys, updateTeamMember } from "@/lib/api";
import type { Team, ApiKey } from "@/lib/types";
import type { AgentRole, ProviderName } from "@/lib/constants";
import { AGENT_CONFIG, PROVIDER_CONFIG } from "@/lib/constants";
import { OrgChart } from "@/components/agent/org-chart";
import { ArrowLeft, Loader2, Check, Sparkles } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/toast";

function buildModelsFromEnabledProviders(apiKeys: ApiKey[]): { name: string; size: string; tag: string; provider: string }[] {
  const enabled: ProviderName[] = apiKeys
    .filter((k) => k.is_enabled)
    .map((k) => k.provider as ProviderName);

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
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [selectedModels, setSelectedModels] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

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

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (team) {
      const initial: Record<string, string> = {};
      for (const m of team.members) {
        initial[m.role] = m.model;
      }
      setSelectedModels(initial);
    }
  }, [team]);

  const roleMap = useMemo(() => {
    if (!team) return {};
    return Object.fromEntries(team.members.map((m) => [m.role, m]));
  }, [team]);

  async function handleSave() {
    if (!team) return;
    setSaving(true);
    try {
      const promises = [];
      for (const role of ALL_ROLES) {
        const originalMember = roleMap[role];
        const newModel = selectedModels[role];

        if (newModel && newModel !== "none") {
          if (!originalMember) {
            promises.push(addTeamMember(id, { role, model: newModel }));
          } else if (originalMember.model !== newModel) {
            promises.push(updateTeamMember(id, originalMember.id, { model: newModel }));
          }
        } else {
          if (originalMember) {
            promises.push(removeTeamMember(id, originalMember.id));
          }
        }
      }

      await Promise.all(promises);
      toast("Team configurations saved successfully", { type: "success" });
      await load();
    } catch {
      toast("Failed to save team configurations", { type: "error" });
    } finally {
      setSaving(false);
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
          onNodeClick={() => {}}
        />
      </div>

      {/* Role Assignment Table */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full text-left border-collapse text-sm">
          <thead>
            <tr className="border-b border-border bg-surface/50 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <th className="px-5 py-3">Role</th>
              <th className="px-5 py-3">Description</th>
              <th className="px-5 py-3">Model Assignment</th>
              <th className="px-5 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {ALL_ROLES.map((roleKey) => {
              const config = AGENT_CONFIG[roleKey];
              const Icon = config.icon;
              const currentModel = selectedModels[roleKey] || "none";
              const isAssigned = currentModel && currentModel !== "none";

              return (
                <tr key={roleKey} className="hover:bg-surface/30 transition-colors">
                  <td className="px-5 py-4 font-medium whitespace-nowrap">
                    <div className="flex items-center gap-2.5">
                      <div className={cn(
                        "flex h-7 w-7 items-center justify-center rounded-lg border",
                        config.border, config.bgSurface,
                      )}>
                        <Icon className={cn("h-3.5 w-3.5", config.text)} />
                      </div>
                      <Badge variant={config.badgeVariant}>{config.label}</Badge>
                    </div>
                  </td>
                  <td className="px-5 py-4 text-xs text-muted-foreground">
                    {roleKey === "team_lead" ? "Coordinates the team, splits tasks, and reviews progress."
                      : roleKey === "builder" ? "Implements the plan, writes code, and writes scripts."
                      : roleKey === "reviewer" ? "Analyses code quality, reports issues, and validates syntax."
                      : "Runs automated checks, verifies imports, and executes tests."}
                  </td>
                  <td className="px-5 py-4">
                    <select
                      value={currentModel}
                      onChange={(e) => setSelectedModels(prev => ({ ...prev, [roleKey]: e.target.value }))}
                      className="w-full max-w-[240px] rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs text-foreground outline-none focus:border-primary/50 font-mono transition-all cursor-pointer"
                    >
                      <option value="none">None (Disabled)</option>
                      {filteredModels.map((m) => (
                        <option key={m.name} value={m.name}>
                          {m.name} ({m.size})
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-5 py-4 whitespace-nowrap">
                    {isAssigned ? (
                      <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                        <Check className="h-3.5 w-3.5" />
                        Active
                      </span>
                    ) : (
                      <span className="text-xs text-muted-foreground">Idle</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <Separator />

      <div className="flex items-center justify-between pt-2">
        <div className="flex gap-2">
          <Link href={`/tasks?team=${team.id}`}>
            <Button disabled={!isComplete || saving}>
              <Sparkles className="h-4 w-4" />
              Create Task with This Team
            </Button>
          </Link>
        </div>
        <Button onClick={handleSave} disabled={saving} className="px-6">
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
          Save Changes
        </Button>
      </div>
    </div>
  );
}
