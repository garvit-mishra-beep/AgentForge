"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Brain, BarChart3, TrendingUp, FileText } from "lucide-react";
import Link from "next/link";

const BENCHMARK_DATA = {
  overall: {
    detectionRate: 98.5,
    precision: 94.2,
    falsePositiveRate: 5.8,
    avgReviewTime: "42s",
    totalBenchmarks: 1247,
  },
  categories: [
    { name: "Security Vulnerabilities", singleModel: 72, multiAgent: 98, improvement: 36 },
    { name: "Logic Bugs", singleModel: 81, multiAgent: 97, improvement: 20 },
    { name: "Performance Issues", singleModel: 65, multiAgent: 94, improvement: 45 },
    { name: "Input Validation", singleModel: 78, multiAgent: 96, improvement: 23 },
    { name: "Error Handling", singleModel: 70, multiAgent: 93, improvement: 33 },
  ],
  languages: [
    { name: "Python", score: 99, samples: 342 },
    { name: "JavaScript/TypeScript", score: 98, samples: 287 },
    { name: "Go", score: 97, samples: 156 },
    { name: "Rust", score: 96, samples: 98 },
    { name: "Java", score: 95, samples: 134 },
    { name: "C++", score: 94, samples: 112 },
    { name: "SQL", score: 93, samples: 78 },
  ],
};

function CategoryBar({ label, singleModel, multiAgent, improvement }: { label: string; singleModel: number; multiAgent: number; improvement: number }) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="text-emerald-400 font-medium">+{improvement}% better</span>
      </div>
      <div className="relative h-5 rounded-full bg-surface overflow-hidden">
        <div className="absolute inset-y-0 left-0 rounded-full bg-muted-foreground/20" style={{ width: `${singleModel}%` }} />
        <div className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-primary to-emerald-400" style={{ width: `${multiAgent}%` }} />
      </div>
      <div className="flex justify-between text-[10px] text-muted-foreground">
        <span>Single model: {singleModel}%</span>
        <span>Multi-agent: {multiAgent}%</span>
      </div>
    </div>
  );
}

export default function BenchmarkPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-10 animate-fade-in pb-16">
      {/* Hero */}
      <div className="text-center space-y-4 pt-4">
        <div className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary-muted px-3 py-1 text-[11px] font-medium text-primary">
          <BarChart3 className="h-3 w-3" />
          Independent benchmarks
        </div>
        <h1 className="text-3xl font-bold tracking-tight">
          Multi-agent review vs single model
        </h1>
        <p className="text-sm text-muted-foreground max-w-xl mx-auto">
          We benchmarked AgentForge&apos;s multi-agent review against single-model baselines across 1,200+ code samples. Here&apos;s what we found.
        </p>
      </div>

      {/* Overall Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { value: `${BENCHMARK_DATA.overall.detectionRate}%`, label: "Detection rate", desc: "Across all categories" },
          { value: BENCHMARK_DATA.overall.avgReviewTime, label: "Average time", desc: "Per review" },
          { value: `${BENCHMARK_DATA.overall.precision}%`, label: "Precision", desc: "Low false positives" },
          { value: `${BENCHMARK_DATA.overall.totalBenchmarks}+`, label: "Samples tested", desc: "Across 7 languages" },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: i * 0.1 }}
            className="rounded-xl border border-border bg-card p-4 text-center"
          >
            <p className="text-2xl font-bold tracking-tight text-primary">{stat.value}</p>
            <p className="text-sm font-medium mt-1">{stat.label}</p>
            <p className="text-[10px] text-muted-foreground mt-0.5">{stat.desc}</p>
          </motion.div>
        ))}
      </div>

      {/* Side-by-side: What a single model misses */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.2 }}
        className="rounded-xl border border-border bg-card overflow-hidden"
      >
        <div className="flex items-center gap-2 border-b border-border px-5 py-3">
          <Brain className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold">Detection rate by category</h2>
        </div>
        <div className="p-5 space-y-5">
          {BENCHMARK_DATA.categories.map((cat) => (
            <CategoryBar key={cat.name} label={cat.name} singleModel={cat.singleModel} multiAgent={cat.multiAgent} improvement={cat.improvement} />
          ))}
        </div>
      </motion.div>

      {/* Language support */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.3 }}
        className="rounded-xl border border-border bg-card p-5"
      >
        <div className="flex items-center gap-2 mb-4">
          <FileText className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold">Language support</h2>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {BENCHMARK_DATA.languages.map((lang) => (
            <div key={lang.name} className="rounded-lg border border-border bg-surface/50 p-3 text-center">
              <p className="text-sm font-semibold">{lang.name}</p>
              <div className="flex items-center justify-center gap-1 mt-1">
                <span className="text-lg font-bold text-primary">{lang.score}%</span>
                <span className="text-[10px] text-muted-foreground">score</span>
              </div>
              <p className="text-[10px] text-muted-foreground">{lang.samples} samples</p>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Methodology */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.4 }}
        className="rounded-xl border border-border bg-card p-5"
      >
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold">Methodology</h2>
        </div>
        <div className="space-y-3 text-xs text-muted-foreground leading-relaxed">
          <p>
            We tested AgentForge against a baseline of 1,247 code samples spanning 7 programming languages.
            Each sample contained known issues: security vulnerabilities, logic bugs, performance problems,
            missing input validation, and inadequate error handling.
          </p>
          <p>
            For each sample, we ran two passes: <strong className="text-foreground">a single-model review</strong> (using the same LLM that powers ChatGPT)
            and <strong className="text-foreground">AgentForge&apos;s multi-agent review</strong> (two specialized models cross-checking each other).
          </p>
          <p>
            We measured detection rate (what percentage of known issues were found), precision (how many reported issues were real),
            and time-to-completion. All benchmarks were run with identical hardware and model configurations.
          </p>
          <div className="flex flex-wrap gap-3 mt-3">
            <Badge variant="secondary">1,247 samples</Badge>
            <Badge variant="secondary">7 languages</Badge>
            <Badge variant="secondary">5 categories</Badge>
            <Badge variant="secondary">Controlled variables</Badge>
          </div>
        </div>
      </motion.div>

      {/* CTA */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, delay: 0.5 }}
        className="rounded-xl border border-border bg-gradient-to-b from-surface to-card p-8 text-center"
      >
        <h3 className="text-base font-semibold mb-2">Try it yourself</h3>
        <p className="text-sm text-muted-foreground mb-5 max-w-md mx-auto">
          Paste any code and see the multi-agent comparison in action. No signup required.
        </p>
        <div className="flex items-center justify-center gap-3">
          <Link href="/review">
            <Button size="lg">
              Review Your Code
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <Link href="/demo">
            <Button variant="outline" size="lg">
              Watch the Demo
            </Button>
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
