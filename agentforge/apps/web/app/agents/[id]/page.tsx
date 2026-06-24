"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Play, Loader2, CheckCircle2, XCircle, Clock, Code, MessageSquare, Terminal } from "lucide-react";
import { useAgentStore } from "@/stores/agent-store";
import { api } from "@/lib/api";
import { cn, formatDuration, formatDate } from "@/lib/utils";
import type { Execution } from "@/types";

export default function AgentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { selectedAgent, fetchAgent, isLoading } = useAgentStore();
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [input, setInput] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  useEffect(() => {
    fetchAgent(id);
    api.get<Execution[]>(`/executions?agent_id=${id}`).then((res) => {
      if (res.data) setExecutions(res.data);
    });
  }, [id, fetchAgent]);

  const handleInvoke = async () => {
    if (!input.trim()) return;
    setRunning(true);
    setResult(null);
    const res = await api.post<any>(`/agents/${id}/invoke`, { message: input });
    if (res.data) {
      setResult(res.data.output);
      const execs = await api.get<Execution[]>(`/executions?agent_id=${id}`);
      if (execs.data) setExecutions(execs.data);
    }
    setRunning(false);
  };

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!selectedAgent) {
    return <div className="text-center py-20 text-muted-foreground">Agent not found</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/agents" className="rounded-lg border p-2 hover:bg-accent">
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold">{selectedAgent.name}</h1>
          <p className="text-sm text-muted-foreground">{selectedAgent.slug}</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <div className="rounded-xl border bg-card p-5">
            <h2 className="font-semibold mb-3">Configuration</h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between"><dt className="text-muted-foreground">Provider</dt><dd className="font-medium">{selectedAgent.llm_config.provider}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Model</dt><dd className="font-medium">{selectedAgent.llm_config.model}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Temperature</dt><dd className="font-medium">{selectedAgent.llm_config.temperature}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Max Tokens</dt><dd className="font-medium">{selectedAgent.llm_config.max_tokens}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Tools</dt><dd className="font-medium">{selectedAgent.tools.length > 0 ? selectedAgent.tools.join(", ") : "None"}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Status</dt><dd><span className={cn("rounded-full px-2 py-0.5 text-xs font-medium capitalize", selectedAgent.status === "active" ? "bg-emerald-50 text-emerald-700" : "bg-slate-50 text-slate-600")}>{selectedAgent.status}</span></dd></div>
            </dl>
          </div>

          {selectedAgent.system_prompt && (
            <div className="rounded-xl border bg-card p-5">
              <h2 className="font-semibold mb-2">System Prompt</h2>
              <pre className="whitespace-pre-wrap text-sm text-muted-foreground bg-muted/30 rounded-lg p-3">{selectedAgent.system_prompt}</pre>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border bg-card p-5">
            <h2 className="font-semibold mb-3">Invoke Agent</h2>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Enter your message..."
              className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
              rows={4}
            />
            <button
              onClick={handleInvoke}
              disabled={running || !input.trim()}
              className="mt-3 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              {running ? "Running..." : "Invoke"}
            </button>
            {result && (
              <div className="mt-4 rounded-lg border bg-muted/30 p-3">
                <h3 className="text-sm font-medium mb-1">Response</h3>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">{result}</p>
              </div>
            )}
          </div>

          <div className="rounded-xl border bg-card p-5">
            <h2 className="font-semibold mb-3">Recent Executions</h2>
            {executions.length === 0 ? (
              <p className="text-sm text-muted-foreground">No executions yet</p>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {executions.slice(0, 10).map((exec) => (
                  <div key={exec.id} className="flex items-center justify-between rounded-lg border bg-muted/20 p-2.5 text-sm">
                    <div className="flex items-center gap-2">
                      {exec.status === "completed" ? <CheckCircle2 className="h-4 w-4 text-emerald-500" /> :
                       exec.status === "failed" ? <XCircle className="h-4 w-4 text-red-500" /> :
                       <Clock className="h-4 w-4 text-amber-500" />}
                      <span className="text-xs text-muted-foreground">{formatDate(exec.created_at)}</span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {exec.total_tokens} tokens · {formatDuration(exec.duration_ms)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
