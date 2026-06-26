"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { listTeams, createTeam, createTeamFromTemplate } from "@/lib/api";
import type { Team } from "@/lib/types";
import type { AgentRole } from "@/lib/constants";
import { AGENT_CONFIG } from "@/lib/constants";
import { TEAM_TEMPLATES, type TeamTemplate } from "@/lib/templates";
import { TemplateConfirmModal } from "@/components/template-confirm-modal";
import { Plus, Users, Loader2, ChevronRight, Check, LayoutTemplate, ArrowRight } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { useToast } from "@/components/ui/toast";

export default function TeamsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  // Template confirm modal state
  const [selectedTemplate, setSelectedTemplate] = useState<TeamTemplate | null>(null);
  const [templateBusy, setTemplateBusy] = useState(false);

  async function load() {
    setLoading(true);
    try {
      setTeams(await listTeams());
    } catch {
      toast("Failed to load teams", { type: "error", description: "Check that the API server is running." });
    }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate() {
    if (!name.trim()) return;
    setBusy(true);
    try {
      const team = await createTeam({ name: name.trim() });
      toast(`Team "${name}" created`, { type: "success" });
      setName("");
      setShowCreate(false);
      router.push(`/teams/${team.id}`);
    } catch (err) {
      toast("Failed to create team", { type: "error", description: "Check API connection." });
    }
    finally { setBusy(false); }
  }

  function applyTemplate(template: TeamTemplate) {
    setSelectedTemplate(template);
  }

  async function handleTemplateConfirm() {
    if (!selectedTemplate) return;
    setTemplateBusy(true);
    try {
      const team = await createTeamFromTemplate({
        name: selectedTemplate.name,
        description: selectedTemplate.description,
        use_case: selectedTemplate.use_case,
        members: selectedTemplate.members.map((m) => ({
          role: m.role,
          model: m.model,
          instructions: m.instructions,
        })),
      });
      toast(`Team "${selectedTemplate.name}" created`, { type: "success", description: `All ${selectedTemplate.members.length} roles assigned.` });
      setSelectedTemplate(null);
      router.push(`/teams/${team.id}`);
    } catch (err) {
      toast("Failed to create from template", { type: "error", description: "Check API connection." });
    }
    finally { setTemplateBusy(false); }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Template confirm modal */}
      <TemplateConfirmModal
        template={selectedTemplate}
        open={selectedTemplate !== null}
        onConfirm={handleTemplateConfirm}
        onCancel={() => setSelectedTemplate(null)}
        busy={templateBusy}
      />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Teams</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Build and manage your AI organizations
          </p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)}>
          <Plus className="h-4 w-4" />
          New Team
        </Button>
      </div>

      {showCreate && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-primary/30 bg-card p-5 space-y-5"
        >
          <div>
            <h3 className="text-sm font-semibold mb-3">Choose a Template</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {TEAM_TEMPLATES.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => applyTemplate(t)}
                  className="group relative rounded-xl border border-border bg-surface p-4 text-left transition-all hover:border-border-hover hover:bg-surface-hover cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h4 className="text-sm font-semibold group-hover:text-primary transition-colors">{t.name}</h4>
                      <p className="text-xs text-muted-foreground mt-0.5">{t.description}</p>
                    </div>
                    <LayoutTemplate className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors shrink-0" />
                  </div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {t.members.map((m) => (
                      <Badge key={m.role} variant={AGENT_CONFIG[m.role].badgeVariant}>
                        {m.label}
                      </Badge>
                    ))}
                  </div>
                </button>
              ))}
            </div>
          </div>
          <Separator />
          <div className="space-y-3">
            <Input
              placeholder="Or type a custom team name..."
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={busy || !name.trim()}>
                {busy ? <Loader2 className="h-3 w-3 animate-spin" /> : <Check className="h-3 w-3" />}
                Create Team
              </Button>
              <Button variant="ghost" onClick={() => { setShowCreate(false); setName(""); }}>
                Cancel
              </Button>
            </div>
          </div>
        </motion.div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin mr-2" />
          Loading teams...
        </div>
      ) : teams.length === 0 && !showCreate ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary-muted">
            <Users className="h-6 w-6 text-primary" />
          </div>
          <h3 className="text-sm font-semibold mb-1">No AI teams yet</h3>
          <p className="text-sm text-muted-foreground mb-4 max-w-xs">
            Choose a template to get a fully configured team instantly, or build from scratch.
          </p>
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4" />
            Create Team
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {teams.map((team, i) => {
            const isComplete = team.members.length >= 3;

            return (
              <motion.div
                key={team.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: i * 0.05 }}
              >
                <Link href={`/teams/${team.id}`} className="block group">
                  <div className="rounded-xl border border-border bg-card p-5 transition-all hover:border-border-hover">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <div className="flex items-center gap-2 mb-0.5">
                          <h3 className="text-sm font-semibold group-hover:text-primary transition-colors">
                            {team.name}
                          </h3>
                          {isComplete ? (
                            <Badge variant="success">Ready</Badge>
                          ) : (
                            <Badge variant="warning">{team.members.length}/4 roles</Badge>
                          )}
                        </div>
                        {team.description && (
                          <p className="text-xs text-muted-foreground mt-0.5">{team.description}</p>
                        )}
                      </div>
                      <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors shrink-0" />
                    </div>

                    <div className="space-y-1.5">
                      {team.members.length === 0 ? (
                        <p className="text-xs text-muted-foreground">No roles assigned yet</p>
                      ) : (
                        team.members.map((m) => {
                          const config = AGENT_CONFIG[m.role as AgentRole];
                          const Icon = config.icon;
                          return (
                            <div key={m.id} className="flex items-center gap-2 rounded-lg border border-border bg-surface/50 px-3 py-2">
                              <Icon className="h-3.5 w-3.5" style={{ color: config.color }} />
                              <Badge variant={config.badgeVariant}>{config.label}</Badge>
                              <code className="text-[10px] font-mono text-muted-foreground flex-1 truncate">{m.model}</code>
                            </div>
                          );
                        })
                      )}
                    </div>

                    <div className="mt-4">
                      <Button variant="outline" size="sm" className="w-full">
                        {isComplete ? "Configure Team" : "Assign Roles"}
                        <ArrowRight className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
