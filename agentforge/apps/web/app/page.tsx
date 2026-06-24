"use client";

import { useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Brain, Workflow, BarChart3, ArrowRight } from "lucide-react";
import { useAgentStore } from "@/stores/agent-store";

export default function HomePage() {
  const { agents, fetchAgents, isLoading } = useAgentStore();

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  return (
    <div className="space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-4"
      >
        <h1 className="text-4xl font-bold tracking-tight">AgentForge AI</h1>
        <p className="text-lg text-muted-foreground max-w-2xl">
          Build, deploy, monitor, and scale AI agents from a single platform.
        </p>
      </motion.div>

      <div className="grid gap-6 md:grid-cols-3">
        <Link href="/agents" className="group rounded-xl border bg-card p-6 hover:shadow-md transition-all">
          <Brain className="h-8 w-8 text-primary mb-3" />
          <h3 className="font-semibold text-lg">Agents</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Create and configure AI agents with custom prompts, models, and tools.
          </p>
          <div className="mt-4 flex items-center text-sm text-primary font-medium">
            {isLoading ? "Loading..." : `${agents.length} agents`}
            <ArrowRight className="ml-1 h-3 w-3 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>

        <Link href="/workflows" className="group rounded-xl border bg-card p-6 hover:shadow-md transition-all">
          <Workflow className="h-8 w-8 text-primary mb-3" />
          <h3 className="font-semibold text-lg">Workflows</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Orchestrate multi-step agent pipelines with conditional branching.
          </p>
          <div className="mt-4 flex items-center text-sm text-primary font-medium">
            Get started
            <ArrowRight className="ml-1 h-3 w-3 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>

        <Link href="/observability" className="group rounded-xl border bg-card p-6 hover:shadow-md transition-all">
          <BarChart3 className="h-8 w-8 text-primary mb-3" />
          <h3 className="font-semibold text-lg">Observability</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Monitor token usage, latency, cost, and execution traces.
          </p>
          <div className="mt-4 flex items-center text-sm text-primary font-medium">
            View dashboard
            <ArrowRight className="ml-1 h-3 w-3 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>
      </div>
    </div>
  );
}
