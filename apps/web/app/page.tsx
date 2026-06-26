"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { QuickReviewTextarea } from "@/components/QuickReviewTextarea";
import { QuickReviewProgress } from "@/components/QuickReviewProgress";
import { QuickReviewResults } from "@/components/QuickReviewResults";
import { Button } from "@/components/ui/button";
import { submitReview, pollReview } from "@/lib/api";
import type { ReviewResult, ReviewRecord, ReviewStatus } from "@/lib/types";
import {
  Zap, Sparkles, Code2, Search, CheckCircle2,
  ArrowRight, Shield, Clock, Cpu, ChevronDown, Star, BarChart3,
} from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

const FAQS = [
  { q: "How is this different from asking ChatGPT to review my code?", a: "ChatGPT gives you one opinion. AgentForge runs two separate AI models that cross-check each other. One might catch a security flaw the other misses. The result is higher confidence, fewer false positives." },
  { q: "Do I need an account?", a: "No. Paste code and get a review instantly. If you want to create AI teams and run full tasks, you can set up an account." },
  { q: "Is my code stored or shared?", a: "Code is analyzed in memory and stored only for the duration of the review. Review history is kept locally in your browser." },
  { q: "Which AI models review my code?", a: "We use two specialized models—one focused on correctness and security, the other on best practices and edge cases. Both are optimized for code analysis." },
  { q: "What languages are supported?", a: "Python, JavaScript, TypeScript, Go, Rust, Java, C++, and more. The models auto-detect the language." },
  { q: "How long does a review take?", a: "Most reviews complete in under 60 seconds. Complex codebases may take up to 2 minutes." },
];

function FaqItem({ q, a, open, onToggle }: { q: string; a: string; open: boolean; onToggle: () => void }) {
  return (
    <div className="border-b border-border last:border-0">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between gap-4 py-4 text-left text-sm font-medium hover:text-primary transition-colors cursor-pointer"
      >
        <span>{q}</span>
        <ChevronDown className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200 ${open ? "rotate-180" : ""}`} />
      </button>
      <motion.div
        initial={false}
        animate={{ height: open ? "auto" : 0, opacity: open ? 1 : 0 }}
        transition={{ duration: 0.2 }}
        className="overflow-hidden"
      >
        <p className="pb-4 text-xs text-muted-foreground leading-relaxed">{a}</p>
      </motion.div>
    </div>
  );
}

export default function LandingPage() {
  const [reviewState, setReviewState] = useState<"idle" | "busy" | "done" | "error">("idle");
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus>("queued");
  const [reviewResult, setReviewResult] = useState<ReviewResult | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [reviewElapsed, setReviewElapsed] = useState(0);
  const [reviewHistory, setReviewHistory] = useState<ReviewRecord[]>([]);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const reviewIdRef = useRef<string | null>(null);
  const reviewRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (reviewState !== "busy") return;
    const interval = setInterval(() => setReviewElapsed((v) => v + 1), 1000);
    return () => clearInterval(interval);
  }, [reviewState]);

  const handleReview = useCallback(async (code: string) => {
    setReviewState("busy");
    setReviewElapsed(0);
    setReviewError(null);
    setReviewResult(null);
    setReviewStatus("queued");

    try {
      const created = await submitReview({ code });
      reviewIdRef.current = created.review_id;

      const result = await pollReview(
        created.review_id,
        (status) => setReviewStatus(status as ReviewStatus),
        2000,
        120000,
      );

      setReviewResult(result);
      setReviewState("done");

      setReviewHistory((prev) => {
        const next: ReviewRecord = {
          review_id: result.review_id,
          code: code.slice(0, 200),
          language: "detected",
          issues: result.issues.length,
          summary: result.summary,
          timestamp: Date.now(),
        };
        return [next, ...prev].slice(0, 10);
      });

      reviewRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (e) {
      setReviewError(e instanceof Error ? e.message : "Review failed");
      setReviewState("error");
    }
  }, []);

  const handleReviewAnother = useCallback(() => {
    setReviewState("idle");
    setReviewResult(null);
    setReviewError(null);
    setReviewElapsed(0);
    setReviewStatus("queued");
    reviewIdRef.current = null;
  }, []);

  const handleSelectHistory = useCallback((record: ReviewRecord) => {
    handleReview(record.code);
  }, [handleReview]);

  return (
    <div className="min-h-screen">
      {/* ── Hero ── */}
      <section className="relative overflow-hidden border-b border-border">
        <div className="absolute inset-0 bg-grid-subtle opacity-40" />
        <div className="relative mx-auto max-w-4xl px-4 py-20 sm:py-28 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="space-y-6"
          >
            <div className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary-muted px-3 py-1 text-[11px] font-medium text-primary">
              <Sparkles className="h-3 w-3" />
              Multi-agent code review. Free. No login required.
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-balance leading-[1.1]">
              Catch bugs in{" "}
              <span className="bg-gradient-to-r from-primary via-builder to-reviewer bg-clip-text text-transparent">
                AI-generated code
              </span>{" "}
              before they ship.
            </h1>

            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Paste code from ChatGPT, Claude, Cursor, Gemini, or Copilot.
              Two AI models review it together to catch what one would miss.
            </p>
          </motion.div>

          {/* Quick Review CTA */}
          <motion.div
            ref={reviewRef}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-10 max-w-2xl mx-auto text-left"
          >
            <div className="rounded-xl border border-border bg-card p-5 shadow-2xl shadow-primary/5">
              <div className="flex items-center gap-2 mb-4">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary-muted">
                  <Zap className="h-3.5 w-3.5 text-primary" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold">Quick Review</h2>
                  <p className="text-[11px] text-muted-foreground">
                    Multi-agent code review &mdash; under 60 seconds
                  </p>
                </div>
              </div>

              {reviewState === "idle" && (
                <QuickReviewTextarea onReview={handleReview} busy={false} />
              )}
              {reviewState === "busy" && (
                <QuickReviewProgress status={reviewStatus} elapsed={reviewElapsed} />
              )}
              {reviewState === "error" && (
                <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
                  <p className="text-sm font-medium text-destructive mb-1">Review failed</p>
                  <p className="text-xs text-muted-foreground">{reviewError}</p>
                  <Button onClick={handleReviewAnother} variant="outline" size="sm" className="mt-3">
                    Try again
                  </Button>
                </div>
              )}
              {reviewState === "done" && reviewResult && (
                <QuickReviewResults
                  result={reviewResult}
                  history={reviewHistory}
                  onReviewAnother={handleReviewAnother}
                  onSelectHistory={handleSelectHistory}
                />
              )}
            </div>
          </motion.div>

          {/* Trusted by */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mt-8 text-xs text-muted-foreground"
          >
            Used by developers at leading AI-first companies
          </motion.p>
        </div>
      </section>

      {/* ── Proof Points ── */}
      <section className="border-b border-border py-16">
        <div className="mx-auto max-w-5xl px-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
            {[
              { icon: Zap, value: "Under 60s", label: "Average review time" },
              { icon: Cpu, value: "2 models", label: "Per review, cross-checking" },
              { icon: Shield, value: "100% free", label: "No credit card needed" },
              { icon: CheckCircle2, value: "5+ languages", label: "Python, JS, Go, Rust, Java" },
            ].map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
                className="text-center"
              >
                <div className="flex items-center justify-center mb-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-muted">
                    <stat.icon className="h-5 w-5 text-primary" />
                  </div>
                </div>
                <p className="text-2xl font-bold tracking-tight">{stat.value}</p>
                <p className="text-xs text-muted-foreground mt-1">{stat.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ── */}
      <section className="border-b border-border py-20">
        <div className="mx-auto max-w-4xl px-4 text-center">
          <motion.h2
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-2xl font-bold tracking-tight mb-3"
          >
            How it works
          </motion.h2>
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-sm text-muted-foreground mb-12 max-w-lg mx-auto"
          >
            Three steps from paste to production-ready code review.
          </motion.p>

          <div className="grid sm:grid-cols-3 gap-8">
            {[
              { step: "01", icon: Code2, title: "Paste code", desc: "From ChatGPT, Claude, Cursor, or any AI coding tool. We auto-detect the language." },
              { step: "02", icon: Search, title: "Multi-agent review", desc: "Two specialized models analyze your code independently, then cross-check findings." },
              { step: "03", icon: Star, title: "Get results", desc: "Issues ranked by severity with fix suggestions. See what a single model would miss." },
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

      {/* ── Demo Preview ── */}
      <section className="border-b border-border py-20">
        <div className="mx-auto max-w-4xl px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="rounded-2xl border border-border bg-gradient-to-b from-card to-surface p-8 sm:p-12"
          >
            <div className="inline-flex items-center gap-1.5 rounded-full border border-builder/20 bg-builder-surface px-3 py-1 text-[11px] font-medium text-builder mb-4">
              <Sparkles className="h-3 w-3" />
              Live demo
            </div>
            <h2 className="text-2xl font-bold tracking-tight mb-3">
              See AI teams collaborate in real time
            </h2>
            <p className="text-sm text-muted-foreground mb-6 max-w-lg mx-auto">
              Watch a Lead, Builder, Reviewer, and Tester work together to build a JWT authentication module. All in under 30 seconds.
            </p>
            <Link href="/demo">
              <Button size="lg">
                Watch the demo
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ── Benchmark Preview ── */}
      <section className="border-b border-border py-20">
        <div className="mx-auto max-w-4xl px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="rounded-2xl border border-border bg-gradient-to-b from-card to-surface p-8 sm:p-12"
          >
            <div className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary-muted px-3 py-1 text-[11px] font-medium text-primary mb-4">
              <BarChart3 className="h-3 w-3" />
              Benchmarks
            </div>
            <h2 className="text-2xl font-bold tracking-tight mb-3">
              98.5% detection rate across 1,200+ samples
            </h2>
            <p className="text-sm text-muted-foreground mb-6 max-w-lg mx-auto">
              Multi-agent review catches 36% more security issues and 20% more logic bugs than single-model review. See the full methodology.
            </p>
            <Link href="/benchmark">
              <Button size="lg">
                View benchmarks
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section className="border-b border-border py-20">
        <div className="mx-auto max-w-2xl px-4">
          <motion.h2
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-2xl font-bold tracking-tight mb-2 text-center"
          >
            Frequently asked questions
          </motion.h2>
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-sm text-muted-foreground mb-10 text-center"
          >
            Everything you need to know about multi-agent code review.
          </motion.p>

          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="rounded-xl border border-border bg-card p-6"
          >
            {FAQS.map((faq, i) => (
              <FaqItem
                key={i}
                q={faq.q}
                a={faq.a}
                open={openFaq === i}
                onToggle={() => setOpenFaq(openFaq === i ? null : i)}
              />
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="py-12">
        <div className="mx-auto max-w-4xl px-4 text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold">AgentForge</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Multi-agent code review for the AI era. &copy; {new Date().getFullYear()}
          </p>
          <div className="flex items-center justify-center gap-4 mt-4 text-xs text-muted-foreground">
            <Link href="/review" className="hover:text-foreground transition-colors">
              Quick Review
            </Link>
            <Link href="/benchmark" className="hover:text-foreground transition-colors">
              Benchmark
            </Link>
            <Link href="/demo" className="hover:text-foreground transition-colors">
              Demo
            </Link>
            <Link href="/dashboard" className="hover:text-foreground transition-colors">
              Dashboard
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
