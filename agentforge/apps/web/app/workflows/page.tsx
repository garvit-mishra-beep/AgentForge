"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Workflow as WorkflowIcon, Loader2 } from "lucide-react";
import { useWorkflowStore } from "@/stores/workflow-store";
import { formatDate } from "@/lib/utils";

export default function WorkflowsPage() {
  const { workflows, fetchWorkflows, createWorkflow, isLoading } = useWorkflowStore();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");

  useEffect(() => {
    fetchWorkflows();
  }, [fetchWorkflows]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const wf = await createWorkflow({ name, definition: { nodes: [], edges: [] } });
    if (wf) {
      setName("");
      setShowCreate(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Workflows</h1>
          <p className="text-muted-foreground text-sm">Orchestrate multi-step agent pipelines</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          New Workflow
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
      ) : workflows.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed py-20 text-center">
          <WorkflowIcon className="h-10 w-10 text-muted-foreground mb-4" />
          <h3 className="font-semibold">No workflows yet</h3>
          <p className="text-sm text-muted-foreground mt-1">Create a workflow to orchestrate multiple agents.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {workflows.map((wf) => (
            <Link key={wf.id} href={`/workflows/${wf.id}`} className="rounded-xl border bg-card p-5 hover:shadow-md transition-all">
              <div className="flex items-center gap-3 mb-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <WorkflowIcon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">{wf.name}</h3>
                  <p className="text-xs text-muted-foreground">v{wf.version} · {formatDate(wf.created_at)}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-emerald-700 font-medium capitalize">{wf.status}</span>
                <span className="text-muted-foreground">{wf.definition?.nodes?.length || 0} nodes</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border bg-card p-6 shadow-lg">
            <h2 className="text-lg font-bold mb-4">Create Workflow</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="text-sm font-medium">Name</label>
                <input value={name} onChange={(e) => setName(e.target.value)} className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm" required />
              </div>
              <div className="flex justify-end gap-3">
                <button type="button" onClick={() => setShowCreate(false)} className="rounded-md border px-4 py-2 text-sm hover:bg-accent">Cancel</button>
                <button type="submit" className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
