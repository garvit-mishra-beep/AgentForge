"use client";

import { useEffect, useState } from "react";
import { BarChart3, Loader2, Activity, DollarSign, Clock, Zap } from "lucide-react";
import { api } from "@/lib/api";
import { formatDuration, formatCost } from "@/lib/utils";
import type { UsageMetrics } from "@/types";

export default function ObservabilityPage() {
  const [metrics, setMetrics] = useState<UsageMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<UsageMetrics>("/observability/usage").then((res) => {
      if (res.data) setMetrics(res.data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="flex h-96 items-center justify-center"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;
  }

  const cards = [
    { label: "Total Executions", value: metrics?.total_executions || 0, icon: Activity, color: "text-blue-600 bg-blue-50" },
    { label: "Total Tokens", value: (metrics?.total_tokens || 0).toLocaleString(), icon: Zap, color: "text-purple-600 bg-purple-50" },
    { label: "Total Cost", value: formatCost(metrics?.total_cost_usd || 0), icon: DollarSign, color: "text-emerald-600 bg-emerald-50" },
    { label: "Avg Duration", value: formatDuration(metrics?.avg_duration_ms || 0), icon: Clock, color: "text-amber-600 bg-amber-50" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Observability</h1>
        <p className="text-muted-foreground text-sm">Monitor agent usage, cost, and performance</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.label} className="rounded-xl border bg-card p-5">
              <div className="flex items-center gap-3">
                <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${card.color}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{card.label}</p>
                  <p className="text-xl font-bold">{card.value}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="rounded-xl border bg-card p-6">
        <h2 className="font-semibold mb-4">Usage Over Time</h2>
        <div className="flex items-center justify-center h-48 text-muted-foreground text-sm">
          <BarChart3 className="h-6 w-6 mr-2" />
          Detailed charts coming soon
        </div>
      </div>
    </div>
  );
}
