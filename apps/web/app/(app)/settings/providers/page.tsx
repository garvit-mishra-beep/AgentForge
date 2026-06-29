"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import {
  listApiKeys, createApiKey, updateApiKey, deleteApiKey, validateApiKey,
} from "@/lib/api";
import { PROVIDER_CONFIG, type ProviderName } from "@/lib/constants";
import type { ApiKey } from "@/lib/types";
import {
  Loader2, CheckCircle2, XCircle, Trash2, Plus, Key,
  Check, AlertTriangle, ArrowLeft, ExternalLink, Shield,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

type ConnectionState = "loading" | "connected" | "not_connected" | "error";

const PROVIDER_ORDER: ProviderName[] = [
  "openai", "anthropic", "google", "openrouter", "groq",
];

export default function ProvidersPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [addModal, setAddModal] = useState<ProviderName | null>(null);
  const [newKey, setNewKey] = useState("");
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{ valid: boolean; message: string } | null>(null);

  async function load() {
    try {
      setKeys(await listApiKeys());
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  function getState(provider: ProviderName): ConnectionState {
    if (loading) return "loading";
    const key = keys.find((k) => k.provider === provider);
    if (!key) return "not_connected";
    return key.is_enabled ? "connected" : "error";
  }

  function getKey(provider: ProviderName): ApiKey | undefined {
    return keys.find((k) => k.provider === provider);
  }

  async function handleToggle(key: ApiKey) {
    try {
      await updateApiKey(key.id, { is_enabled: !key.is_enabled });
      await load();
    } catch { /* ignore */ }
  }

  async function handleDelete(id: string) {
    setDeleting(id);
    try {
      await deleteApiKey(id);
      await load();
    } catch { /* ignore */ }
    finally { setDeleting(null); }
  }

  async function handleValidate() {
    if (!addModal || !newKey.trim()) return;
    setValidating(true);
    setValidationResult(null);
    try {
      const result = await validateApiKey({ provider: addModal, key: newKey.trim() });
      setValidationResult({ valid: result.valid, message: result.message });
    } catch {
      setValidationResult({ valid: false, message: "Validation request failed" });
    }
    finally { setValidating(false); }
  }

  async function handleSave() {
    if (!addModal || !newKey.trim() || !validationResult?.valid) return;
    setSaving(addModal);
    try {
      await createApiKey({ provider: addModal, key: newKey.trim() });
      setAddModal(null);
      setNewKey("");
      setValidationResult(null);
      await load();
    } catch { /* ignore */ }
    finally { setSaving(null); }
  }

  return (
    <div className="space-y-8 animate-fade-in max-w-4xl">
      <div>
        <Link href="/settings" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors mb-3">
          <ArrowLeft className="h-3 w-3" />
          Back to Settings
        </Link>
        <h1 className="text-2xl font-bold tracking-tight">Providers</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Connect your AI provider API keys. Keys are encrypted at rest with AES-256-GCM.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {PROVIDER_ORDER.map((provider) => {
          const config = PROVIDER_CONFIG[provider];
          const Icon = config.icon;
          const state = getState(provider);
          const key = getKey(provider);

          return (
            <motion.div
              key={provider}
              layout
              className={cn(
                "rounded-xl border p-5 transition-all",
                state === "connected" ? "border-emerald-400/20 bg-emerald-400/[0.02]" :
                  state === "error" ? "border-amber-400/20 bg-amber-400/[0.02]" :
                  "border-border bg-card hover:border-border-hover",
              )}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-xl",
                    "bg-surface border border-border",
                  )}>
                    <Icon className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold">{config.label}</p>
                    <Badge variant={
                      state === "connected" ? "success" :
                      state === "error" ? "warning" :
                      "outline"
                    } className="mt-0.5">
                      {state === "loading" ? "..." :
                       state === "connected" ? "Connected" :
                       state === "error" ? "Disabled" : "Not Connected"}
                    </Badge>
                  </div>
                </div>
              </div>

              {key && (
                <div className="flex items-center gap-2 rounded-lg border border-border bg-surface/50 px-3 py-2 mb-3">
                  <Key className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  <code className="text-xs font-mono text-muted-foreground truncate">{key.key_preview}</code>
                  {key.is_enabled ? (
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 ml-auto shrink-0" />
                  ) : (
                    <XCircle className="h-3.5 w-3.5 text-amber-400 ml-auto shrink-0" />
                  )}
                </div>
              )}



              <div className="flex items-center gap-2">
                {key ? (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleToggle(key)}
                      className="text-xs"
                    >
                      {key.is_enabled ? "Disable" : "Enable"}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => { setAddModal(provider); setNewKey(""); setValidationResult(null); }}
                      className="text-xs"
                    >
                      Update Key
                    </Button>
                    <button
                      type="button"
                      onClick={() => handleDelete(key.id)}
                      disabled={deleting === key.id}
                      className="ml-auto text-muted-foreground hover:text-destructive transition-colors cursor-pointer"
                    >
                      {deleting === key.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                    </button>
                  </>
                ) : (
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => { setAddModal(provider); setNewKey(""); setValidationResult(null); }}
                    className="text-xs gap-1"
                  >
                    <Plus className="h-3 w-3" />
                    Add Key
                  </Button>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      <AnimatePresence>
        {addModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-2xl"
            >
              <div className="flex items-center gap-3 mb-5">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-surface border border-border">
                  {(() => {
                    const ModalIcon = PROVIDER_CONFIG[addModal].icon;
                    return <ModalIcon className="h-4 w-4 text-muted-foreground" />;
                  })()}
                </div>
                <div>
                  <h3 className="text-sm font-semibold">{PROVIDER_CONFIG[addModal].label}</h3>
                  <p className="text-[11px] text-muted-foreground">Paste your API key below</p>
                </div>
              </div>

              <div className="space-y-3">
                <Input
                  type="password"
                  placeholder={
                    addModal === "openai" ? "sk-..." :
                    addModal === "anthropic" ? "sk-ant-..." :
                    addModal === "google" ? "AIza..." :
                    addModal === "openrouter" ? "sk-or-..." :
                    addModal === "groq" ? "gsk_..." :
                    "Paste your API key"
                  }
                  value={newKey}
                  onChange={(e) => { setNewKey(e.target.value); setValidationResult(null); }}
                  className="font-mono text-xs"
                  autoFocus
                />

                {validationResult && (
                  <div className={cn(
                    "flex items-start gap-2 rounded-lg p-3 text-xs",
                    validationResult.valid ? "bg-emerald-400/10 border border-emerald-400/20" : "bg-destructive/10 border border-destructive/20",
                  )}>
                    {validationResult.valid ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
                    )}
                    <div>
                      <p className={validationResult.valid ? "text-emerald-400" : "text-destructive"}>
                        {validationResult.valid ? "Key validated" : "Validation failed"}
                      </p>
                      <p className="text-muted-foreground mt-0.5">{validationResult.message}</p>
                    </div>
                  </div>
                )}

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleValidate}
                    disabled={!newKey.trim() || validating}
                    className="text-xs"
                  >
                    {validating ? <Loader2 className="h-3 w-3 animate-spin" /> : <Check className="h-3 w-3" />}
                    Validate
                  </Button>
                  <Button
                    variant="default"
                    size="sm"
                    onClick={handleSave}
                    disabled={!validationResult?.valid || saving === addModal}
                    className="text-xs gap-1"
                  >
                    {saving === addModal ? <Loader2 className="h-3 w-3 animate-spin" /> : <ExternalLink className="h-3 w-3" />}
                    Save Key
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => { setAddModal(null); setValidationResult(null); }}
                    className="text-xs ml-auto"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <Separator />

      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-2 mb-3">
          <Shield className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-semibold">Security</span>
        </div>
        <ul className="space-y-1.5 text-xs text-muted-foreground">
          <li className="flex items-center gap-2">
            <CheckCircle2 className="h-3 w-3 text-emerald-400 shrink-0" />
            All keys encrypted at rest with AES-256-GCM
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="h-3 w-3 text-emerald-400 shrink-0" />
            Raw keys are never exposed after save â€” only masked previews shown
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="h-3 w-3 text-emerald-400 shrink-0" />
            Keys validated against provider API before storage
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="h-3 w-3 text-emerald-400 shrink-0" />
            Each key is decrypted only when needed at task runtime
          </li>
        </ul>
      </div>
    </div>
  );
}
