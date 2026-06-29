"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Clock, Search, Star, Download, Trash2, ArrowLeft, Bug, ChevronRight } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { ReviewRecord } from "@/lib/types";
import { FormattedDate } from "@/components/ui/formatted-date";


const STORAGE_KEY = "agentforge-review-history";

function loadHistory(): ReviewRecord[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as ReviewRecord[];
  } catch {
    return [];
  }
}

function saveHistory(records: ReviewRecord[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
}

export default function ReviewHistoryPage() {
  const [records, setRecords] = useState<ReviewRecord[]>([]);
  const [search, setSearch] = useState("");
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setRecords(loadHistory());
    try {
      const favRaw = localStorage.getItem("agentforge-review-favorites");
      if (favRaw) setFavorites(new Set(JSON.parse(favRaw)));
    } catch {}
    setLoading(false);
  }, []);

  const filtered = useMemo(() => {
    if (!search.trim()) return records;
    const q = search.toLowerCase();
    return records.filter((r) =>
      r.code.toLowerCase().includes(q) ||
      r.language.toLowerCase().includes(q) ||
      r.summary.toLowerCase().includes(q),
    );
  }, [records, search]);

  const toggleFavorite = useCallback((id: string) => {
    setFavorites((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      localStorage.setItem("agentforge-review-favorites", JSON.stringify([...next]));
      return next;
    });
  }, []);

  const handleExport = useCallback(() => {
    const data = JSON.stringify(records, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `agentforge-reviews-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [records]);

  const handleDelete = useCallback((id: string) => {
    const next = records.filter((r) => r.review_id !== id);
    setRecords(next);
    saveHistory(next);
  }, [records]);

  const handleClearAll = useCallback(() => {
    setRecords([]);
    saveHistory([]);
  }, []);

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <Link href="/review" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors mb-3">
          <ArrowLeft className="h-3 w-3" />
          Back to review
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Review History</h1>
            <p className="text-sm text-muted-foreground mt-1">
              {records.length} saved review{records.length !== 1 ? "s" : ""}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {records.length > 0 && (
              <>
                <Button size="sm" variant="secondary" onClick={handleExport}>
                  <Download className="h-3.5 w-3.5" />
                  Export
                </Button>
                <Button size="sm" variant="ghost" onClick={handleClearAll} className="text-destructive">
                  <Trash2 className="h-3.5 w-3.5" />
                  Clear all
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search reviews by code, language, or summary..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* List */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-card p-12 text-center">
          <div className="flex items-center justify-center mb-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-muted">
              <Clock className="h-5 w-5 text-primary" />
            </div>
          </div>
          <p className="text-sm font-medium mb-1">
            {search ? "No reviews match your search" : "No review history yet"}
          </p>
          <p className="text-xs text-muted-foreground mb-4">
            {search ? "Try a different search term." : "Reviews you submit will appear here automatically."}
          </p>
          {!search && (
            <Link href="/review">
              <Button size="sm">
                Review Your First Code
              </Button>
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((record, i) => (
            <motion.div
              key={record.review_id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: i * 0.03 }}
              className="group rounded-xl border border-border bg-card p-4 hover:border-border-hover transition-all"
            >
              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-muted mt-0.5">
                  <Bug className="h-4 w-4 text-primary" />
                </div>
                <div className="flex-1 min-w-0 space-y-1.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="secondary">{record.language}</Badge>
                    <span className="text-[10px] font-mono text-muted-foreground">
                      {record.issues} issue{record.issues !== 1 ? "s" : ""}
                    </span>
                    <span className="text-[10px] text-muted-foreground">
                      <FormattedDate date={record.timestamp} type="datetime" options={{ month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }} />
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2">{record.summary}</p>
                  {record.code && (
                    <pre className="text-[10px] font-mono text-muted-foreground/60 truncate max-w-full bg-surface/50 rounded px-2 py-1">
                      {record.code.slice(0, 120)}
                    </pre>
                  )}
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <button
                    type="button"
                    onClick={() => toggleFavorite(record.review_id)}
                    className={cn(
                      "flex h-7 w-7 items-center justify-center rounded-md transition-colors cursor-pointer",
                      favorites.has(record.review_id)
                        ? "text-amber-400 hover:text-amber-300"
                        : "text-muted-foreground hover:text-foreground opacity-0 group-hover:opacity-100",
                    )}
                  >
                    <Star className="h-3.5 w-3.5" fill={favorites.has(record.review_id) ? "currentColor" : "none"} />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(record.review_id)}
                    className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:text-destructive transition-colors opacity-0 group-hover:opacity-100 cursor-pointer"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                  <ChevronRight className="h-4 w-4 text-muted-foreground/40" />
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
