"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { QuickReviewTextarea } from "@/components/review/QuickReviewTextarea";
import { QuickReviewProgress } from "@/components/review/QuickReviewProgress";
import { QuickReviewResults } from "@/components/review/QuickReviewResults";
import { Button } from "@/components/ui/button";
import { submitReview, pollReview } from "@/lib/api";
import type { ReviewResult, ReviewRecord, ReviewStatus } from "@/lib/types";
import { Zap, ArrowLeft, Sparkles, Clock } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

export default function ReviewPage() {
  const [reviewState, setReviewState] = useState<"idle" | "busy" | "done" | "error">("idle");
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus>("queued");
  const [reviewResult, setReviewResult] = useState<ReviewResult | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [reviewElapsed, setReviewElapsed] = useState(0);
  const [reviewHistory, setReviewHistory] = useState<ReviewRecord[]>([]);
  const reviewIdRef = useRef<string | null>(null);

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
    <div className="min-h-full">
      <div className="mx-auto max-w-3xl py-8 space-y-6">
        {/* Back link */}
        <div className="flex items-center justify-between">
          <Link
            href="/"
            className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-3 w-3" />
            Back to home
          </Link>
          <Link
            href="/review/history"
            className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <Clock className="h-3 w-3" />
            History
          </Link>
        </div>

        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary-muted px-3 py-1 text-[11px] font-medium text-primary">
            <Sparkles className="h-3 w-3" />
            Multi-agent code review
          </div>
          <h1 className="text-3xl font-bold tracking-tight">
            Quick Review
          </h1>
          <p className="text-sm text-muted-foreground max-w-lg mx-auto">
            Paste code from any AI tool. Two models review it together. Results in under 60 seconds.
          </p>
        </div>

        {/* Review card */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="rounded-xl border border-border bg-card p-5"
        >
          <div className="flex items-center gap-2 mb-4">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary-muted">
              <Zap className="h-3.5 w-3.5 text-primary" />
            </div>
            <div>
              <h2 className="text-sm font-semibold">Paste your code</h2>
              <p className="text-[11px] text-muted-foreground">
                Supports Python, JavaScript, TypeScript, Go, Rust, Java, C++, and more
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
        </motion.div>
      </div>
    </div>
  );
}
