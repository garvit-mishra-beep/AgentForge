"use client";

import { useState, useEffect, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Sparkles, Code2, Bot, ArrowRight,
  CheckCircle2, Server, Cpu, Shield,
  Zap, GitBranch, Users, ChevronRight, Menu, X,
  Github,
} from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import dynamic from "next/dynamic";

const AgentNetwork = dynamic(() => import("@/components/agent/agent-network").then((m) => ({ default: m.AgentNetwork })), { ssr: false });

const NAV_ITEMS = [
  { label: "Features", href: "#features" },
  { label: "Pipeline", href: "#pipeline" },
  { label: "Pricing", href: "#pricing" },
  { label: "Docs", href: "/docs" },
];

const FEATURES = [
  { icon: Cpu, title: "Multi-Agent Orchestration", desc: "Coordinate specialized AI agents â€” Lead, Builder, Reviewer, Tester, Security, DevOps â€” through a LangGraph-powered state graph." },
  { icon: GitBranch, title: "LangGraph State Graph", desc: "Every task flows through a predictable pipeline. Agents pass context, artifacts, and decisions to the next stage automatically." },
  { icon: Zap, title: "Real-Time WebSocket Logs", desc: "Watch your agents collaborate live. Stream tokens, see handoffs, and inspect every decision as it happens." },
  { icon: Server, title: "pgvector Semantic Memory", desc: "Agents remember past tasks, decisions, and code patterns across sessions. Context persists beyond a single conversation." },
  { icon: Users, title: "Human-in-the-Loop Approvals", desc: "Pause the pipeline at critical junctures. Review, approve, or request changes before agents proceed to the next stage." },
  { icon: Shield, title: "Bring Your Own Keys (BYOK)", desc: "Connect your own OpenAI, Anthropic, Google, or OpenRouter API keys. AES-256 encrypted at rest. Zero vendor lock-in." },
];

const PRICING = [
  {
    name: "Starter", price: "Free", tasks: "10 tasks/mo", agents: "2 agents", support: "Community", byok: false, sso: false, featured: false,
  },
  {
    name: "Pro", price: "$29/mo", tasks: "Unlimited", agents: "All 6", support: "Priority", byok: true, sso: false, featured: true,
  },
  {
    name: "Enterprise", price: "Custom", tasks: "Unlimited", agents: "All 6", support: "SLA + Dedicated", byok: true, sso: true, featured: false,
  },
];

const AGENT_NODES = [
  { role: "team_lead" as const, model: "GPT-4o", label: "Team Lead" },
  { role: "builder" as const, model: "Claude Sonnet", label: "Builder" },
  { role: "reviewer" as const, model: "GPT-4o", label: "Reviewer" },
  { role: "tester" as const, model: "Qwen-72B", label: "Tester" },
];

function WaitlistForm() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "done" | "error">("idle");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;
    setStatus("submitting");
    try {
      const res = await fetch("/api/v1/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });
      if (!res.ok) throw new Error("Failed");
      setStatus("done");
    } catch {
      setStatus("error");
    }
  }

  if (status === "done") {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/5 px-5 py-4">
        <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />
        <p className="text-sm text-emerald-400 font-medium">You&apos;re on the list &check;</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2 max-w-md mx-auto">
      <Input
        type="email"
        placeholder="you@company.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="flex-1"
        required
      />
      <Button type="submit" disabled={status === "submitting" || !email.trim()}>
        {status === "submitting" ? "Sending..." : "Reserve your spot"}
      </Button>
    </form>
  );
}

function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    function onScroll() { setScrolled(window.scrollY > 20); }
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? "bg-background/80 backdrop-blur-xl border-b border-border" : "bg-transparent"}`}>
      <nav className="mx-auto max-w-6xl px-4 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <span className="text-sm font-bold">AgentForge</span>
        </Link>

        <div className="hidden md:flex items-center gap-6">
          {NAV_ITEMS.map((item) => (
            <Link key={item.label} href={item.href} className="text-xs text-muted-foreground hover:text-foreground transition-colors">
              {item.label}
            </Link>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-2">
          <Link href="/login">
            <Button variant="ghost" size="sm">Sign in</Button>
          </Link>
          <Link href="#waitlist">
            <Button size="sm">Join Waitlist</Button>
          </Link>
        </div>

        <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden text-muted-foreground hover:text-foreground cursor-pointer">
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>

      {mobileOpen && (
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="md:hidden border-t border-border bg-card px-4 py-4 space-y-3">
          {NAV_ITEMS.map((item) => (
            <Link key={item.label} href={item.href} className="block text-sm text-muted-foreground hover:text-foreground" onClick={() => setMobileOpen(false)}>
              {item.label}
            </Link>
          ))}
          <div className="flex gap-2 pt-2 border-t border-border">
            <Link href="/login"><Button variant="ghost" size="sm">Sign in</Button></Link>
            <Link href="#waitlist"><Button size="sm">Join Waitlist</Button></Link>
          </div>
        </motion.div>
      )}
    </header>
  );
}

export default function MarketingPage() {
  return (
    <div className="min-h-screen">
      <Navbar />

      {/* â”€â”€ Hero â”€â”€ */}
      <section className="relative overflow-hidden pt-24 pb-20 sm:pt-32 sm:pb-28">
        <div className="absolute inset-0 bg-grid-subtle opacity-40" />
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-3xl pointer-events-none" />
        <div className="relative mx-auto max-w-5xl px-4 text-center space-y-8">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <div className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary-muted px-3 py-1 text-[11px] font-medium text-primary">
              <Sparkles className="h-3 w-3" />
              Now in Private Beta
            </div>
          </motion.div>

          <motion.h1 initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }} className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-balance leading-[1.1]">
            Ship with an{" "}
            <span className="bg-gradient-to-r from-primary via-builder to-reviewer bg-clip-text text-transparent">AI team</span>
            ,<br />not just a tool.
          </motion.h1>

          <motion.p initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }} className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto">
            AgentForge orchestrates specialized AI agents â€” Planner, Builder, Reviewer, QA, Security, DevOps â€” that collaborate like a real engineering team.
          </motion.p>

          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.3 }} className="flex items-center justify-center gap-3 flex-wrap">
            <Link href="#waitlist">
              <Button size="lg">Get Early Access <ArrowRight className="h-4 w-4" /></Button>
            </Link>
            <Link href="/docs">
              <Button size="lg" variant="outline">Read the Docs &rarr;</Button>
            </Link>
          </motion.div>

          {/* Agent Network Canvas */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.4 }} className="mt-12">
            <div className="rounded-2xl border border-border bg-gradient-to-b from-card to-surface p-6 sm:p-10 shadow-2xl shadow-primary/5">
              <AgentNetwork agents={AGENT_NODES.map((n) => ({ id: n.role, role: n.role, model: n.model, status: "idle" as const }))} />
            </div>
          </motion.div>
        </div>
      </section>

      {/* â”€â”€ How It Works â”€â”€ */}
      <section className="border-t border-border py-20">
        <div className="mx-auto max-w-4xl px-4 text-center">
          <h2 className="text-2xl font-bold tracking-tight mb-3">How It Works</h2>
          <p className="text-sm text-muted-foreground mb-12 max-w-lg mx-auto">Three steps from idea to shipped code, powered by multi-agent collaboration.</p>

          <div className="grid sm:grid-cols-3 gap-8">
            {[
              { step: "01", icon: Users, title: "Define Your Team", desc: "Assign roles + models to agents. Choose from pre-built templates or customize each agent's model, instructions, and capabilities." },
              { step: "02", icon: Code2, title: "Submit a Task", desc: "Describe what to build â€” a JWT auth module, a CRUD API, a React component. Add context, files, or project references." },
              { step: "03", icon: Bot, title: "Agents Ship It", desc: "Plan &rarr; Build &rarr; Review &rarr; Test &rarr; Secure &rarr; Deliver. Watch the pipeline execute with real-time streaming logs." },
            ].map((item, i) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.15 }}
                className="text-center"
              >
                <div className="flex items-center justify-center mb-4">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-card border border-border">
                    <item.icon className="h-6 w-6 text-primary" />
                  </div>
                </div>
                <p className="text-[11px] font-mono text-muted-foreground mb-2">{item.step}</p>
                <h3 className="text-sm font-semibold mb-2">{item.title}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed max-w-xs mx-auto">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* â”€â”€ Pipeline Visualizer â”€â”€ */}
      <section id="pipeline" className="border-t border-border py-20">
        <div className="mx-auto max-w-5xl px-4">
          <div className="text-center mb-10">
            <h2 className="text-2xl font-bold tracking-tight mb-3">Execution Pipeline</h2>
            <p className="text-sm text-muted-foreground max-w-lg mx-auto">Every task flows through a predictable state graph. Click any node to inspect its output.</p>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="rounded-2xl border border-border bg-gradient-to-b from-card to-surface p-8 sm:p-12"
          >
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-6 text-xs font-mono">
              {[
                { label: "User Task", color: "text-muted-foreground", border: "border-muted-foreground/30" },
                { label: "Team Lead", color: "text-lead", border: "border-lead/30" },
                { label: "Builder", color: "text-builder", border: "border-builder/30" },
                { label: "Reviewer", color: "text-reviewer", border: "border-reviewer/30" },
                { label: "Tester", color: "text-tester", border: "border-tester/30" },
              ].map((node, i, arr) => (
                <div key={node.label} className="flex items-center gap-3 sm:gap-6">
                  <div className={`rounded-xl border-2 ${node.border} ${node.color} bg-card px-4 py-3 font-semibold text-sm whitespace-nowrap`}>
                    {node.label}
                  </div>
                  {i < arr.length - 1 && <ChevronRight className="h-4 w-4 text-muted-foreground hidden sm:block" />}
                </div>
              ))}
            </div>
            <div className="mt-6 text-center">
              <span className="text-[10px] text-muted-foreground font-mono">LangGraph State Graph &middot; 6 agent types &middot; Parallel execution</span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* â”€â”€ Features Grid â”€â”€ */}
      <section id="features" className="border-t border-border py-20">
        <div className="mx-auto max-w-5xl px-4">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold tracking-tight mb-3">Everything you need to ship with AI teams</h2>
            <p className="text-sm text-muted-foreground max-w-lg mx-auto">Features designed for engineers who demand control, transparency, and reliability.</p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.3, delay: i * 0.05 }}
                className="rounded-xl border border-border bg-card p-5 hover:border-border-hover transition-all"
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-muted mb-3">
                  <feature.icon className="h-4 w-4 text-primary" />
                </div>
                <h3 className="text-sm font-semibold mb-1.5">{feature.title}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* â”€â”€ Dashboard Preview â”€â”€ */}
      <section className="border-t border-border py-20">
        <div className="mx-auto max-w-5xl px-4">
          <div className="text-center mb-10">
            <h2 className="text-2xl font-bold tracking-tight mb-3">Built for engineers who move fast</h2>
            <p className="text-sm text-muted-foreground max-w-lg mx-auto">A developer-native interface. Keyboard-first. Real-time. No fluff.</p>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="rounded-2xl border border-border overflow-hidden shadow-2xl"
          >
            {/* Browser chrome */}
            <div className="flex items-center gap-1.5 bg-surface px-4 py-3 border-b border-border">
              <span className="h-3 w-3 rounded-full bg-destructive/60" />
              <span className="h-3 w-3 rounded-full bg-warn/60" />
              <span className="h-3 w-3 rounded-full bg-emerald-500/60" />
              <span className="ml-3 text-[10px] text-muted-foreground font-mono">app.agentforge.io &mdash; Mission Control</span>
            </div>

            {/* Mock dashboard */}
            <div className="bg-card p-6 sm:p-8 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="h-5 w-32 rounded bg-surface animate-pulse" />
                  <div className="h-3 w-48 rounded bg-surface/50 animate-pulse mt-2" />
                </div>
                <div className="flex gap-2">
                  <div className="h-8 w-20 rounded-lg bg-surface animate-pulse" />
                  <div className="h-8 w-24 rounded-lg bg-primary/20 animate-pulse" />
                </div>
              </div>

              <div className="grid grid-cols-4 gap-3">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-20 rounded-xl bg-surface animate-pulse" />
                ))}
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="col-span-2 space-y-2">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-10 rounded-lg bg-surface animate-pulse" />
                  ))}
                </div>
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-8 rounded-lg bg-surface animate-pulse" />
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* â”€â”€ Pricing â”€â”€ */}
      <section id="pricing" className="border-t border-border py-20">
        <div className="mx-auto max-w-4xl px-4">
          <div className="text-center mb-10">
            <h2 className="text-2xl font-bold tracking-tight mb-3">Simple, transparent pricing</h2>
            <p className="text-sm text-muted-foreground max-w-lg mx-auto">Start free. Scale when you need to. Enterprise for teams that require more.</p>
          </div>

          <div className="grid sm:grid-cols-3 gap-4">
            {PRICING.map((plan) => (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className={`rounded-xl border p-6 ${plan.featured ? "border-primary/40 bg-card shadow-xl shadow-primary/5" : "border-border bg-card"}`}
              >
                {plan.featured && (
                  <Badge variant="default" className="mb-3">Most Popular</Badge>
                )}
                <h3 className="text-sm font-semibold mb-1">{plan.name}</h3>
                <p className="text-2xl font-bold tracking-tight mb-4">{plan.price}</p>
                <ul className="space-y-2 mb-6">
                  {[
                    { label: plan.tasks, included: true },
                    { label: plan.agents, included: true },
                    { label: `${plan.support} support`, included: true },
                    { label: "BYOK", included: plan.byok },
                    { label: "SSO", included: plan.sso },
                  ].map((feature) => (
                    <li key={feature.label} className={`flex items-center gap-2 text-xs ${feature.included ? "text-muted-foreground" : "text-muted-foreground/40 line-through"}`}>
                      <CheckCircle2 className={`h-3.5 w-3.5 ${feature.included ? "text-primary" : "text-muted-foreground/40"}`} />
                      {feature.label}
                    </li>
                  ))}
                </ul>
                <Link href={plan.name === "Enterprise" ? "#waitlist" : "/register"} className="block">
                  <Button variant={plan.featured ? "default" : "outline"} className="w-full">
                    {plan.name === "Enterprise" ? "Contact Us" : "Get Started"}
                  </Button>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* â”€â”€ Waitlist â”€â”€ */}
      <section id="waitlist" className="border-t border-border py-20">
        <div className="mx-auto max-w-2xl px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="space-y-6"
          >
            <div className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary-muted px-3 py-1 text-[11px] font-medium text-primary">
              <Sparkles className="h-3 w-3" />
              Private Beta
            </div>
            <h2 className="text-2xl font-bold tracking-tight">Reserve your spot</h2>
            <p className="text-sm text-muted-foreground max-w-md mx-auto">
              We&apos;re onboarding beta users now. Join the waitlist and get early access to AgentForge.
            </p>
            <WaitlistForm />
          </motion.div>
        </div>
      </section>

      {/* â”€â”€ Footer â”€â”€ */}
      <footer className="border-t border-border py-12">
        <div className="mx-auto max-w-5xl px-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <span className="text-sm font-semibold">AgentForge</span>
            </div>
            <div className="flex items-center gap-6 text-xs text-muted-foreground">
              <Link href="/review" className="hover:text-foreground transition-colors">Quick Review</Link>
              <Link href="/benchmark" className="hover:text-foreground transition-colors">Benchmark</Link>
              <Link href="/demo" className="hover:text-foreground transition-colors">Demo</Link>
              <Link href="/docs" className="hover:text-foreground transition-colors">Docs</Link>
              <Link href="https://github.com/anonylabs/agentforge" className="hover:text-foreground transition-colors">
                <Github className="h-4 w-4" />
              </Link>
            </div>
          </div>
          <p className="text-center text-xs text-muted-foreground mt-6">
            Built for engineers who move fast. &copy; {new Date().getFullYear()}
          </p>
        </div>
      </footer>
    </div>
  );
}
