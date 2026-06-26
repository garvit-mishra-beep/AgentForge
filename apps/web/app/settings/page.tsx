"use client";

import { use, useEffect, useState } from "react";
import { Separator } from "@/components/ui/separator";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { listApiKeys } from "@/lib/api";
import { PROVIDER_CONFIG, type ProviderName } from "@/lib/constants";
import type { ApiKey } from "@/lib/types";
import { Settings, Globe, Paintbrush, Bell, Key, Server, ChevronRight, ArrowRight, Shield, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

const PROVIDER_ORDER: ProviderName[] = [
  "openai", "anthropic", "google", "openrouter", "groq", "ollama",
];

const SETTINGS_SECTIONS = [
  {
    title: "API Configuration",
    description: "Configure your API endpoint and authentication",
    icon: Server,
    items: [
      { label: "API URL", value: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1" },
      { label: "API Key", value: "••••••••••••••••" },
    ],
  },
  {
    title: "Appearance",
    description: "Customize the look and feel",
    icon: Paintbrush,
    items: [
      { label: "Theme", value: "Dark (default)" },
      { label: "Font Size", value: "Small" },
    ],
  },
  {
    title: "Notifications",
    description: "Manage notification preferences",
    icon: Bell,
    items: [
      { label: "Task Completion", value: "Enabled" },
      { label: "Task Failure", value: "Enabled" },
    ],
  },
  {
    title: "Models",
    description: "Configure available AI models",
    icon: Key,
    items: [
      { label: "Default Provider", value: "Ollama" },
      { label: "Available Models", value: "12" },
    ],
  },
];

export default function SettingsPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listApiKeys().then(setKeys).catch(() => {}).finally(() => setLoading(false));
  }, []);

  function connectedCount(): number {
    return keys.filter((k) => k.is_enabled).length;
  }

  return (
    <div className="space-y-8 animate-fade-in max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Manage your AgentForge configuration
        </p>
      </div>

      <div className="space-y-4">
        {/* Providers Card — links to /settings/providers */}
        <Link href="/settings/providers" className="block">
          <Card className="hover:border-border-hover transition-all cursor-pointer group">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface">
                    <Shield className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <CardTitle className="text-sm">Providers</CardTitle>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Connect AI provider API keys
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={connectedCount() > 0 ? "success" : "outline"} className="text-[10px]">
                    {loading ? "..." : `${connectedCount()}/${PROVIDER_ORDER.length - 1} connected`}
                  </Badge>
                  <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1.5">
                {PROVIDER_ORDER.map((p) => {
                  const key = keys.find((k) => k.provider === p);
                  const config = PROVIDER_CONFIG[p];
                  const isConnected = key?.is_enabled || p === "ollama";
                  return (
                    <span
                      key={p}
                      className={cn(
                        "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-medium border",
                        isConnected
                          ? "border-emerald-400/20 text-emerald-400 bg-emerald-400/5"
                          : "border-border text-muted-foreground bg-surface/50",
                      )}
                    >
                      {isConnected && <CheckCircle2 className="h-2.5 w-2.5" />}
                      {config.label}
                    </span>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </Link>

        {SETTINGS_SECTIONS.map((section) => {
          const Icon = section.icon;
          return (
            <Card key={section.title} className="hover:border-border-hover transition-all">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface">
                    <Icon className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <CardTitle className="text-sm">{section.title}</CardTitle>
                    <p className="text-xs text-muted-foreground mt-0.5">{section.description}</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {section.items.map((item) => (
                    <div key={item.label} className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">{item.label}</span>
                      <div className="flex items-center gap-2">
                        <code className="text-xs font-mono text-foreground bg-surface px-2 py-0.5 rounded">{item.value}</code>
                        <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="text-center text-xs text-muted-foreground py-4">
        AgentForge v0.2.0 — Open source multi-agent AI orchestration
      </div>
    </div>
  );
}
