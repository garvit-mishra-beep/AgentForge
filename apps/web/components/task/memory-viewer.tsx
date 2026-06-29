"use client";

import { useState, useEffect, useCallback, FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { listMemories, createMemory, deleteMemory } from "@/lib/api";
import type { MemoryItem } from "@/lib/api";
import {
  Brain, Loader2, Plus, Trash2, Sparkles, Search, X,
} from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface MemoryViewerProps {
  projectId?: string;
  teamId?: string;
}

export function MemoryViewer({ projectId, teamId }: MemoryViewerProps) {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [newKey, setNewKey] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newType, setNewType] = useState("general");
  const [newImportance, setNewImportance] = useState(0.5);
  const [newTags, setNewTags] = useState("");
  const [creating, setCreating] = useState(false);

  const loadMemories = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listMemories({
        project_id: projectId,
        team_id: teamId,
        search: search || undefined,
        limit: 100,
      });
      setMemories(data);
    } catch {
      setMemories([]);
    } finally {
      setLoading(false);
    }
  }, [projectId, teamId, search]);

  useEffect(() => { loadMemories(); }, [loadMemories]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!newKey.trim() || !newContent.trim()) return;

    setCreating(true);
    try {
      await createMemory({
        key: newKey,
        content: newContent,
        memory_type: newType,
        importance: newImportance,
        tags: newTags.split(",").map((t) => t.trim()).filter(Boolean),
        project_id: projectId,
        team_id: teamId,
      });
      setNewKey("");
      setNewContent("");
      setNewTags("");
      setNewImportance(0.5);
      setShowCreate(false);
      await loadMemories();
    } catch { /* ignore */ }
    finally { setCreating(false); }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteMemory(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
    } catch { /* ignore */ }
  };

  const typeColors: Record<string, string> = {
    general: "bg-surface text-muted-foreground",
    decision: "bg-emerald-500/10 text-emerald-400",
    code: "bg-blue-500/10 text-blue-400",
    design: "bg-violet-500/10 text-violet-400",
    error: "bg-destructive/10 text-destructive",
    pattern: "bg-amber-500/10 text-amber-400",
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search memories..."
            className="w-full rounded-lg border border-border bg-card pl-8 pr-8 py-1.5 text-xs placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all"
          />
          {search && (
            <button
              type="button"
              onClick={() => setSearch("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground cursor-pointer"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>
        <Button size="sm" onClick={() => setShowCreate(!showCreate)}>
          {showCreate ? <X className="h-3.5 w-3.5" /> : <Plus className="h-3.5 w-3.5" />}
          {showCreate ? "Cancel" : "Add Memory"}
        </Button>
      </div>

      {/* Create form */}
      {showCreate && (
        <motion.form
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          onSubmit={handleCreate}
          className="rounded-xl border border-border bg-card p-4 space-y-3"
        >
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[10px] font-medium text-muted-foreground">Key</label>
              <input
                type="text"
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
                placeholder="memory.identifier"
                className="w-full rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-medium text-muted-foreground">Type</label>
              <select
                value={newType}
                onChange={(e) => setNewType(e.target.value)}
                className="w-full rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-primary/30"
              >
                <option value="general">General</option>
                <option value="decision">Decision</option>
                <option value="code">Code</option>
                <option value="design">Design</option>
                <option value="error">Error</option>
                <option value="pattern">Pattern</option>
              </select>
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-medium text-muted-foreground">Content</label>
            <textarea
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              placeholder="Memory content..."
              rows={3}
              className="w-full rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[10px] font-medium text-muted-foreground">Tags (comma-separated)</label>
              <input
                type="text"
                value={newTags}
                onChange={(e) => setNewTags(e.target.value)}
                placeholder="tag1, tag2"
                className="w-full rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs placeholder:text-muted-foreground/50 focus:outline-none"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-medium text-muted-foreground">Importance ({newImportance.toFixed(1)})</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={newImportance}
                onChange={(e) => setNewImportance(parseFloat(e.target.value))}
                className="w-full accent-primary"
              />
            </div>
          </div>
          <Button type="submit" size="sm" disabled={creating || !newKey.trim() || !newContent.trim()}>
            {creating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
            Store Memory
          </Button>
        </motion.form>
      )}

      {/* Memory list */}
      {loading ? (
        <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin mr-2" />
          Loading memories...
        </div>
      ) : memories.length === 0 ? (
        <div className="text-center py-12 space-y-3">
          <Brain className="h-10 w-10 mx-auto text-muted-foreground/50" />
          <p className="text-sm text-muted-foreground">No memories stored yet.</p>
          <p className="text-xs text-muted-foreground/70">Memories persist across sessions to give your AI agents long-term context.</p>
          <Button size="sm" variant="secondary" onClick={() => setShowCreate(true)}>
            <Plus className="h-3.5 w-3.5" />
            Create first memory
          </Button>
        </div>
      ) : (
        <div className="space-y-1.5">
          {memories.map((mem, i) => (
            <motion.div
              key={mem.id}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: i * 0.02 }}
              className="group rounded-lg border border-border bg-card px-4 py-3 hover:border-border-hover transition-all"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Brain className="h-3.5 w-3.5 text-primary shrink-0" />
                    <span className="text-xs font-mono font-medium">{mem.key}</span>
                    <Badge className={cn("text-[9px] px-1.5 py-0", typeColors[mem.memory_type] || typeColors.general)}>
                      {mem.memory_type}
                    </Badge>
                    <span className="text-[9px] text-muted-foreground/50">
                      importance: {mem.importance.toFixed(1)}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1.5 whitespace-pre-wrap line-clamp-3">{mem.content}</p>
                  {mem.tags.length > 0 && (
                    <div className="flex gap-1 mt-1.5 flex-wrap">
                      {mem.tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-[9px] px-1 py-0">{tag}</Badge>
                      ))}
                    </div>
                  )}
                  <p className="text-[9px] text-muted-foreground/40 mt-1.5">
                    {new Date(mem.created_at).toLocaleString()}
                    {mem.source && ` via ${mem.source}`}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleDelete(mem.id)}
                  className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/5 transition-colors opacity-0 group-hover:opacity-100 shrink-0 cursor-pointer"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
