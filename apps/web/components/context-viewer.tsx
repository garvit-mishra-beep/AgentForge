"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  getContextSummary,
  parseAllFileContexts,
  getFileContext,
  deleteFileContext,
} from "@/lib/api";
import type { ContextSummaryItem, CodeChunkItem } from "@/lib/api";
import {
  Loader2, FolderSearch, FileCode, Braces, ArrowRight,
  ChevronRight, X, RefreshCw, Trash2, Code,
} from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ContextViewerProps {
  projectId: string;
}

export function ContextViewer({ projectId }: ContextViewerProps) {
  const [summary, setSummary] = useState<ContextSummaryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [parsing, setParsing] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContext, setFileContext] = useState<{
    language: string;
    symbols: { id: string; symbol_type: string; name: string; signature: string; docstring: string }[];
    imports: { source: string; line_number: number }[];
    chunks: CodeChunkItem[];
  } | null>(null);
  const [fileContextLoading, setFileContextLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"symbols" | "imports" | "chunks">("symbols");

  const loadSummary = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getContextSummary(projectId);
      setSummary(data);
    } catch {
      setSummary([]);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => { loadSummary(); }, [loadSummary]);

  const handleParseAll = async () => {
    setParsing(true);
    try {
      await parseAllFileContexts(projectId);
      await loadSummary();
    } catch { /* ignore */ }
    finally { setParsing(false); }
  };

  const handleSelectFile = async (fileId: string) => {
    setSelectedFile(fileId);
    setFileContextLoading(true);
    setFileContext(null);
    try {
      const ctx = await getFileContext(projectId, fileId);
      setFileContext({
        language: ctx.language,
        symbols: ctx.symbols,
        imports: ctx.imports,
        chunks: ctx.chunks,
      });
    } catch {
      setFileContext(null);
    } finally {
      setFileContextLoading(false);
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    try {
      await deleteFileContext(projectId, fileId);
      if (selectedFile === fileId) {
        setSelectedFile(null);
        setFileContext(null);
      }
      await loadSummary();
    } catch { /* ignore */ }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin mr-2" />
        Loading context...
      </div>
    );
  }

  const totalSymbols = summary.reduce((a, b) => a + b.symbol_count, 0);
  const totalChunks = summary.reduce((a, b) => a + b.chunk_count, 0);
  const totalImports = summary.reduce((a, b) => a + b.import_count, 0);
  const parsedCount = summary.filter((s) => !s.error_message).length;
  const erroredCount = summary.filter((s) => s.error_message).length;

  return (
    <div className="space-y-4">
      {/* Stats and actions */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span><strong className="text-foreground">{parsedCount}</strong> files parsed</span>
          <span><strong className="text-foreground">{totalSymbols}</strong> symbols</span>
          <span><strong className="text-foreground">{totalImports}</strong> imports</span>
          <span><strong className="text-foreground">{totalChunks}</strong> chunks</span>
          {erroredCount > 0 && (
            <Badge variant="destructive" className="text-[9px]">{erroredCount} errors</Badge>
          )}
        </div>
        <Button size="sm" variant="secondary" onClick={handleParseAll} disabled={parsing}>
          {parsing ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <RefreshCw className="h-3.5 w-3.5" />
          )}
          {parsing ? "Parsing..." : "Parse All Files"}
        </Button>
      </div>

      {summary.length === 0 ? (
        <div className="text-center py-12 space-y-3">
          <FolderSearch className="h-10 w-10 mx-auto text-muted-foreground/50" />
          <p className="text-sm text-muted-foreground">No repository context parsed yet.</p>
          <p className="text-xs text-muted-foreground/70">Upload files and click "Parse All Files" to analyze your codebase.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* File list */}
          <div className="lg:col-span-1 space-y-1 max-h-[500px] overflow-y-auto pr-1">
            {summary.map((item, i) => (
              <motion.div
                key={item.file_id}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: i * 0.02 }}
              >
                <button
                  type="button"
                  onClick={() => item.error_message ? null : handleSelectFile(item.file_id)}
                  disabled={!!item.error_message}
                  className={cn(
                    "w-full flex items-center gap-2 rounded-lg border px-3 py-2 text-left transition-all cursor-pointer",
                    selectedFile === item.file_id
                      ? "border-primary bg-primary-muted"
                      : item.error_message
                        ? "border-destructive/30 bg-destructive/5 opacity-60 cursor-not-allowed"
                        : "border-border bg-card hover:border-border-hover",
                  )}
                >
                  <FileCode className={cn(
                    "h-3.5 w-3.5 shrink-0",
                    item.error_message ? "text-destructive" : "text-primary",
                  )} />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium truncate">{item.filename}</p>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <Badge variant="secondary" className="text-[9px] px-1 py-0">{item.language || "?"}</Badge>
                      {item.error_message ? (
                        <span className="text-[9px] text-destructive">parse error</span>
                      ) : (
                        <span className="text-[9px] text-muted-foreground">{item.symbol_count} symbols</span>
                      )}
                    </div>
                  </div>
                  {!item.error_message && (
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); handleDeleteFile(item.file_id); }}
                      className="flex h-6 w-6 items-center justify-center rounded text-muted-foreground hover:text-destructive hover:bg-destructive/5 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  )}
                </button>
              </motion.div>
            ))}
          </div>

          {/* Detail panel */}
          <div className="lg:col-span-2">
            {fileContextLoading ? (
              <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Loading file context...
              </div>
            ) : fileContext ? (
              <div className="rounded-xl border border-border bg-card">
                {/* Tabs */}
                <div className="flex items-center gap-1 border-b border-border px-3 py-2">
                  <button
                    type="button"
                    onClick={() => setActiveTab("symbols")}
                    className={cn(
                      "px-2.5 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer",
                      activeTab === "symbols" ? "bg-primary text-primary-fg" : "text-muted-foreground hover:text-foreground",
                    )}
                  >
                    Symbols ({fileContext.symbols.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab("imports")}
                    className={cn(
                      "px-2.5 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer",
                      activeTab === "imports" ? "bg-primary text-primary-fg" : "text-muted-foreground hover:text-foreground",
                    )}
                  >
                    Imports ({fileContext.imports.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab("chunks")}
                    className={cn(
                      "px-2.5 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer",
                      activeTab === "chunks" ? "bg-primary text-primary-fg" : "text-muted-foreground hover:text-foreground",
                    )}
                  >
                    Chunks ({fileContext.chunks.length})
                  </button>
                </div>

                {/* Symbols */}
                {activeTab === "symbols" && (
                  <div className="divide-y divide-border max-h-[400px] overflow-y-auto">
                    {fileContext.symbols.length === 0 ? (
                      <div className="p-6 text-center text-xs text-muted-foreground">No symbols found.</div>
                    ) : (
                      fileContext.symbols.map((sym) => (
                        <div key={sym.id} className="px-4 py-2.5 hover:bg-surface/50 transition-colors">
                          <div className="flex items-center gap-2">
                            <Braces className="h-3 w-3 text-muted-foreground/70 shrink-0" />
                            <span className="text-xs font-mono font-medium">{sym.name}</span>
                            <Badge variant="secondary" className="text-[9px] px-1 py-0">{sym.symbol_type}</Badge>
                          </div>
                          {sym.signature && (
                            <p className="text-[10px] font-mono text-muted-foreground/70 mt-0.5 ml-5 truncate">{sym.signature}</p>
                          )}
                          {sym.docstring && (
                            <p className="text-[10px] text-muted-foreground/50 mt-0.5 ml-5 truncate">{sym.docstring}</p>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                )}

                {/* Imports */}
                {activeTab === "imports" && (
                  <div className="divide-y divide-border max-h-[400px] overflow-y-auto">
                    {fileContext.imports.length === 0 ? (
                      <div className="p-6 text-center text-xs text-muted-foreground">No imports found.</div>
                    ) : (
                      fileContext.imports.map((imp, i) => (
                        <div key={i} className="px-4 py-2 text-xs font-mono text-muted-foreground hover:bg-surface/50 transition-colors">
                          <span className="text-[10px] text-muted-foreground/50 mr-2">L{imp.line_number}</span>
                          <ArrowRight className="h-2.5 w-2.5 inline mr-1" />
                          {imp.source}
                        </div>
                      ))
                    )}
                  </div>
                )}

                {/* Chunks */}
                {activeTab === "chunks" && (
                  <div className="divide-y divide-border max-h-[400px] overflow-y-auto">
                    {fileContext.chunks.length === 0 ? (
                      <div className="p-6 text-center text-xs text-muted-foreground">No chunks found.</div>
                    ) : (
                      fileContext.chunks.map((chunk) => (
                        <details key={chunk.id} className="group">
                          <summary className="flex items-center gap-2 px-4 py-2.5 cursor-pointer hover:bg-surface/50 transition-colors list-none">
                            <ChevronRight className="h-3 w-3 text-muted-foreground/50 group-open:rotate-90 transition-transform shrink-0" />
                            <Code className="h-3 w-3 text-primary shrink-0" />
                            <span className="text-xs font-mono font-medium">{chunk.name}</span>
                            <Badge variant="secondary" className="text-[9px] px-1 py-0">{chunk.chunk_type}</Badge>
                            <span className="text-[9px] text-muted-foreground/50 ml-auto">~{chunk.tokens_estimate} tokens</span>
                          </summary>
                          <pre className="px-4 pb-3 pt-1 text-[10px] font-mono leading-relaxed overflow-x-auto bg-surface/30 max-h-60 overflow-y-auto">
                            <code>{chunk.content.slice(0, 2000)}{chunk.content.length > 2000 ? "\n..." : ""}</code>
                          </pre>
                        </details>
                      ))
                    )}
                  </div>
                )}
              </div>
            ) : (
              /* No file selected */
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <FolderSearch className="h-10 w-10 text-muted-foreground/30 mb-3" />
                <p className="text-sm text-muted-foreground">Select a parsed file to view its context</p>
                <p className="text-xs text-muted-foreground/50 mt-1">
                  Browse symbols, imports, and code chunks
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
