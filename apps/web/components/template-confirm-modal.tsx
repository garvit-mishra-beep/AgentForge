"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Loader2, CheckCircle2, Sparkles, Users, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AGENT_CONFIG } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { TeamTemplate } from "@/lib/templates";

interface TemplateConfirmModalProps {
  template: TeamTemplate | null;
  open: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  busy: boolean;
}

export function TemplateConfirmModal({ template, open, onConfirm, onCancel, busy }: TemplateConfirmModalProps) {
  if (!template) return null;

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[90] flex items-center justify-center bg-black/60 p-4"
          onClick={busy ? undefined : onCancel}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -8 }}
            transition={{ duration: 0.15 }}
            className="w-full max-w-lg rounded-xl border border-border bg-card shadow-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-muted">
                  <Sparkles className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold">Create Team from Template</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">{template.name}</p>
                </div>
              </div>
              {!busy && (
                <button
                  onClick={onCancel}
                  className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>

            {/* Body */}
            <div className="px-5 py-4 space-y-4">
              <p className="text-xs text-muted-foreground leading-relaxed">{template.description}</p>

              <div className="space-y-2">
                <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">Team Members</p>
                {template.members.map((member) => {
                  const config = AGENT_CONFIG[member.role];
                  const Icon = config.icon;
                  return (
                    <div
                      key={member.role}
                      className="flex items-start gap-3 rounded-lg border border-border bg-surface/50 px-3 py-2.5"
                    >
                      <div className={cn("flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border", config.border, config.bgSurface)}>
                        <Icon className={cn("h-3.5 w-3.5", config.text)} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <Badge variant={config.badgeVariant}>{member.label}</Badge>
                          <code className="text-[10px] font-mono text-muted-foreground truncate">{member.model}</code>
                        </div>
                        <p className="text-[10px] text-muted-foreground mt-0.5">{member.description}</p>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="rounded-lg border border-border bg-surface/30 px-3 py-2">
                <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider mb-1">Use Case</p>
                <p className="text-xs text-muted-foreground">{template.use_case}</p>
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-2 border-t border-border px-5 py-3">
              <Button variant="ghost" onClick={onCancel} disabled={busy}>
                Cancel
              </Button>
              <Button onClick={onConfirm} disabled={busy}>
                {busy ? (
                  <><Loader2 className="h-4 w-4 animate-spin" /> Creating...</>
                ) : (
                  <><CheckCircle2 className="h-4 w-4" /> Create Team</>
                )}
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
