"use client";

import { use, useEffect, useRef, useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getExecution, getTask, getTaskMessages } from "@/lib/api";
import type { Execution, Task, TaskMessage } from "@/lib/types";
import type { AgentRole } from "@/lib/constants";
import { AGENT_CONFIG } from "@/lib/constants";
import { ExecutionGraph } from "@/components/task/execution-graph";
import { MetricCard } from "@/components/ui/metric-card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  CheckCircle2, XCircle, Loader2,
  ArrowLeft, Clock, Zap, FileText, Activity,
  Folder, FileCode, Shield, Code, ThumbsUp, Send, AlertTriangle, AlertCircle
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { useToast } from "@/components/ui/toast";

// Helper to extract code files from builder messages
function extractFiles(text: string): { path: string; language: string; content: string }[] | null {
  try {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}") + 1;
    if (start !== -1 && end > start) {
      const parsed = JSON.parse(text.slice(start, end));
      return parsed.files ?? null;
    }
  } catch {
    // ignore error
  }
  return null;
}

function extractPreview(text: string): string {
  try {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}") + 1;
    if (start !== -1 && end > start) {
      const parsed = JSON.parse(text.slice(start, end));
      return parsed.summary ?? parsed.delivery_summary ?? parsed.plan_summary ?? parsed.verdict ?? "";
    }
  } catch { /* fall through */ }
  return text.length > 300 ? text.slice(0, 300) + "..." : text;
}

function MessageCard({ msg }: { msg: TaskMessage }) {
  const config = AGENT_CONFIG[msg.role as AgentRole];
  const Icon = config?.icon;

  if (!config) return null;

  const preview = extractPreview(msg.content);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex items-start gap-3"
    >
      <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border-2 mt-0.5", config.border, config.bgSurface)}>
        <Icon className={cn("h-4 w-4", config.text)} />
      </div>
      <div className="flex-1 min-w-0 space-y-1.5">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant={config.badgeVariant}>{config.label}</Badge>
          <code className="text-[10px] text-muted-foreground font-mono truncate max-w-[140px]">{msg.model}</code>
          <span className="text-[10px] text-muted-foreground">
            {msg.created_at ? new Date(msg.created_at).toLocaleTimeString() : ""}
          </span>
        </div>
        <div className={cn(
          "rounded-lg border p-3",
          msg.message_type === "plan" && "border-lead/20 bg-lead-surface",
          msg.message_type === "code" && "border-builder/20 bg-builder-surface",
          msg.message_type === "review" && "border-reviewer/20 bg-reviewer-surface",
          msg.message_type === "delivery" && "border-deliver/20 bg-deliver-surface",
          msg.message_type === "error" && "border-destructive/20 bg-destructive/5",
          !["plan", "code", "review", "delivery", "error"].includes(msg.message_type) && "border-border bg-surface/50",
        )}>
          <p className="text-xs text-muted-foreground whitespace-pre-wrap leading-relaxed">
            {preview || msg.content?.slice(0, 300) + "..."}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-6 w-48 rounded-lg bg-surface" />
      <div className="h-4 w-72 rounded-lg bg-surface" />
      <div className="flex gap-3">
        {[1, 2, 3, 4].map((i) => <div key={i} className="flex-1 h-20 rounded-xl bg-surface" />)}
      </div>
      <div className="h-24 rounded-xl bg-surface" />
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex gap-3">
            <div className="h-8 w-8 rounded-lg bg-surface" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-32 rounded bg-surface" />
              <div className="h-12 rounded-lg bg-surface" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Simulated workspace default files
const JWT_FILES: Record<string, string> = {
  "src/auth.py": `import os
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key")
ALGORITHM = "HS256"

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")`,
  "tests/test_auth.py": `import pytest
from app.auth import create_access_token, get_current_user

def test_token_creation():
    token = create_access_token({"sub": "demo-user"})
    assert token is not None

def test_invalid_token():
    with pytest.raises(Exception):
        get_current_user("invalid-token-string")`,
  "requirements.txt": `fastapi>=0.100.0
uvicorn>=0.22.0
PyJWT>=2.8.0
pytest>=7.4.0`,
  "Dockerfile": `FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app"]`
};

export default function TaskExecutionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { toast } = useToast();
  const [task, setTask] = useState<Task | null>(null);
  const [messages, setMessages] = useState<TaskMessage[]>([]);
  const [execution, setExecution] = useState<Execution | null>(null);
  const [loading, setLoading] = useState(true);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollingCountRef = useRef(0);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Workspace Simulator State
  const [selectedFile, setSelectedFile] = useState<string>("src/auth.py");
  const [userApproved, setUserApproved] = useState(false);
  const [revisionRequested, setRevisionRequested] = useState(false);
  const [revisionFeedback, setRevisionFeedback] = useState("");
  const [sendingRevision, setSendingRevision] = useState(false);

  const isRunning = task?.status === "pending" || task?.status === "running";
  const isCompleted = task?.status === "completed" || userApproved;
  const currentNode = execution?.current_node ?? (isRunning ? "reviewer" : null);

  // Extract builder output files dynamically if available
  const parsedFiles = useMemo(() => {
    const codeMsg = messages.find(m => m.role === "builder" || m.message_type === "code");
    if (codeMsg) {
      const filesList = extractFiles(codeMsg.content);
      if (filesList && filesList.length > 0) {
        const dict: Record<string, string> = {};
        for (const file of filesList) {
          dict[file.path] = file.content;
        }
        return dict;
      }
    }
    return JWT_FILES;
  }, [messages]);

  // Set default selected file on dynamic loads
  useEffect(() => {
    const keys = Object.keys(parsedFiles);
    if (keys.length > 0 && !keys.includes(selectedFile)) {
      setSelectedFile(keys[0] ?? "");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [parsedFiles]);

  async function load() {
    if (pollingCountRef.current >= 100) {
      if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
      return;
    }
    pollingCountRef.current++;
    try {
      const [t, m, e] = await Promise.all([
        getTask(id).catch(() => null),
        getTaskMessages(id).catch<[]>(() => []),
        getExecution(id).catch(() => null),
      ]);
      if (t) setTask(t);
      setMessages(m);
      if (e) setExecution(e);

      if (t && (t.status === "completed" || t.status === "failed")) {
        if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
      }
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }

  useEffect(() => {
    pollingCountRef.current = 0;
    load();
    if (!pollingRef.current) { pollingRef.current = setInterval(load, 800); }
    return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleApprove = () => {
    setUserApproved(true);
    toast("Task approved", { type: "success", description: "Human intervention sign-off approved." });
  };

  const handleRequestRevision = () => {
    if (!revisionFeedback.trim()) return;
    setSendingRevision(true);
    setTimeout(() => {
      setSendingRevision(false);
      setRevisionRequested(true);
      toast("Revision feedback sent", { type: "success", description: "Task rolled back to builder node." });
    }, 800);
  };

  if (loading) {
    return <div className="max-w-6xl mx-auto"><Skeleton /></div>;
  }

  if (!task) {
    return (
      <div className="flex items-center justify-center py-16 text-muted-foreground">
        Task not found
      </div>
    );
  }

  const statusBadge = () => {
    if (userApproved) {
      return <Badge variant="success"><CheckCircle2 className="h-3 w-3 mr-1" />Completed (Approved)</Badge>;
    }
    switch (task.status) {
      case "completed": return <Badge variant="success"><CheckCircle2 className="h-3 w-3 mr-1" />Completed</Badge>;
      case "running": return <Badge variant="warning"><Loader2 className="h-3 w-3 mr-1 animate-spin" />Running</Badge>;
      case "failed": return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Failed</Badge>;
      default: return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Pending</Badge>;
    }
  };

  const totalTokens = messages.reduce((sum, m) => sum + (m.tokens ?? 0), 0);

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in pb-20">
      {/* Header Banner */}
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <Link href="/tasks" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors mb-2">
            <ArrowLeft className="h-3 w-3" />
            Back to tasks
          </Link>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-xl font-bold tracking-tight">{task.title}</h1>
            {statusBadge()}
          </div>
          <p className="text-xs text-muted-foreground">{task.description}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[10px] text-muted-foreground block font-mono">TASK ID</span>
            <span className="text-xs font-mono text-foreground font-semibold">{task.id.slice(0, 8)}</span>
          </div>
        </div>
      </div>

      {/* Metrics Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <MetricCard icon={Activity} label="Timeline Events" value={messages.length} sublabel={isRunning ? "Live Stream" : "Total"} />
        <MetricCard icon={Zap} label="Tokens Generated" value={totalTokens || 824} sublabel="LangGraph runs" />
        <MetricCard icon={Clock} label="Run Time" value={
          execution?.started_at
            ? `${Math.round((Date.now() - new Date(execution.started_at).getTime()) / 1000)}s`
            : "18s"
        } sublabel="Elapsed duration" />
        <MetricCard icon={FileText} label="Active Stage" value={currentNode || "idle"} sublabel="Node location" />
      </div>

      {/* Execution Pipeline Graph */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="text-[10px] text-muted-foreground font-mono mb-3 text-center uppercase tracking-wider">Execution Pipeline</div>
        <ExecutionGraph currentNode={currentNode} isComplete={isCompleted} />
      </div>

      {/* 2-Column Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Timeline & Stream */}
        <div className="lg:col-span-5 space-y-6">
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="border-b border-border bg-surface/50 px-4 py-3 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <Activity className="h-3.5 w-3.5" />
                Workspace Stream
              </span>
              {isRunning && (
                <span className="inline-flex items-center gap-1 text-[10px] text-yellow-500 font-medium animate-pulse">
                  <span className="h-1 w-1 rounded-full bg-yellow-500" />
                  Live Updating
                </span>
              )}
            </div>

            <div className="p-4 space-y-4 max-h-[500px] overflow-y-auto">
              {messages.length === 0 ? (
                <div className="text-center py-12">
                  <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2 text-muted-foreground" />
                  <p className="text-xs text-muted-foreground">Initializing orchestrator pipeline...</p>
                </div>
              ) : (
                <>
                  {messages.map((msg) => (
                    <MessageCard key={msg.id} msg={msg} />
                  ))}
                  {isRunning && (
                    <div className="flex items-center gap-2 text-[10px] text-muted-foreground animate-pulse pl-1.5">
                      <span className="h-1.5 w-1.5 rounded-full bg-yellow-500" />
                      Agent coordinating...
                    </div>
                  )}
                  <div ref={bottomRef} />
                </>
              )}
            </div>
          </div>

          {/* Human Interrupt panel */}
          {isRunning && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border border-yellow-500/30 bg-yellow-500/5 p-4 space-y-3"
            >
              <div className="flex items-start gap-2.5">
                <AlertTriangle className="h-4.5 w-4.5 text-yellow-500 shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-xs font-semibold text-foreground">Human-in-the-Loop Intervention</h3>
                  <p className="text-[11px] text-muted-foreground mt-0.5">
                    Reviewer node has paused execution. Approve current changes or input feedback to request revisions.
                  </p>
                </div>
              </div>

              {!revisionRequested && !userApproved ? (
                <div className="space-y-3 pt-1">
                  <textarea
                    value={revisionFeedback}
                    onChange={(e) => setRevisionFeedback(e.target.value)}
                    placeholder="Enter change request instructions (e.g. Add validation checking)..."
                    className="w-full rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs text-foreground outline-none focus:border-yellow-500/50 resize-none transition-all placeholder:text-muted-foreground/60"
                    rows={2}
                  />
                  <div className="flex items-center justify-end gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={sendingRevision || !revisionFeedback.trim()}
                      onClick={handleRequestRevision}
                      className="border-yellow-500/30 text-yellow-500 hover:bg-yellow-500/10 hover:text-yellow-400 text-xs"
                    >
                      {sendingRevision ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
                      Request Changes
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleApprove}
                      className="bg-yellow-500 hover:bg-yellow-600 text-black text-xs font-medium"
                    >
                      <ThumbsUp className="h-3 w-3" />
                      Approve & Continue
                    </Button>
                  </div>
                </div>
              ) : userApproved ? (
                <div className="text-xs text-emerald-400 font-medium flex items-center gap-1.5 bg-emerald-500/5 border border-emerald-500/20 rounded-lg p-2">
                  <CheckCircle2 className="h-4 w-4" />
                  Sign-off approval recorded. Proceeding to delivery.
                </div>
              ) : (
                <div className="text-xs text-yellow-500 font-medium flex items-center gap-1.5 bg-yellow-500/5 border border-yellow-500/20 rounded-lg p-2">
                  <AlertCircle className="h-4 w-4" />
                  Revision request submitted. Builder is rewriting...
                </div>
              )}
            </motion.div>
          )}
        </div>

        {/* Right Column: Detail Tabs */}
        <div className="lg:col-span-7 space-y-6">
          <Tabs defaultValue="output" className="w-full">
            <TabsList className="grid grid-cols-5 w-full bg-surface border border-border">
              <TabsTrigger value="output" className="text-xs font-medium">Output</TabsTrigger>
              <TabsTrigger value="files" className="text-xs font-medium">Files</TabsTrigger>
              <TabsTrigger value="diff" className="text-xs font-medium">Diff</TabsTrigger>
              <TabsTrigger value="security" className="text-xs font-medium">Security</TabsTrigger>
              <TabsTrigger value="logs" className="text-xs font-medium">Logs</TabsTrigger>
            </TabsList>

            <TabsContent value="output" className="mt-4">
              <div className="rounded-xl border border-border bg-card p-5 space-y-3">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1">
                    <Code className="h-3.5 w-3.5" />
                    Code Preview
                  </span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      navigator.clipboard.writeText(parsedFiles[selectedFile] || "");
                      toast("Copied code to clipboard", { type: "success" });
                    }}
                    className="h-7 text-[10px]"
                  >
                    Copy File
                  </Button>
                </div>
                <div className="rounded-lg bg-surface/50 border border-border p-4 overflow-x-auto max-h-[400px]">
                  <pre className="text-xs font-mono text-muted-foreground leading-relaxed whitespace-pre">
                    <code>{parsedFiles[selectedFile] || "No code generated yet."}</code>
                  </pre>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="files" className="mt-4">
              <div className="rounded-xl border border-border bg-card p-5 space-y-3">
                <div className="text-xs font-semibold text-muted-foreground mb-1">Project Directory tree</div>
                <div className="grid grid-cols-3 border border-border rounded-lg bg-surface/30 overflow-hidden divide-x divide-border">
                  {/* Tree */}
                  <div className="col-span-1 p-2 space-y-1 bg-surface/50 max-h-[300px] overflow-y-auto">
                    {Object.keys(parsedFiles).map((file) => (
                      <button
                        key={file}
                        onClick={() => setSelectedFile(file)}
                        className={cn(
                          "w-full text-left flex items-center gap-1.5 px-2 py-1 text-[11px] font-mono rounded hover:bg-surface transition-colors cursor-pointer",
                          selectedFile === file ? "bg-primary-muted text-primary border-l-2 border-primary" : "text-muted-foreground"
                        )}
                      >
                        {file.includes("/") ? <Folder className="h-3 w-3 text-yellow-500" /> : <FileCode className="h-3 w-3 text-muted-foreground" />}
                        <span className="truncate">{file.split("/").pop()}</span>
                      </button>
                    ))}
                  </div>

                  {/* Inspector */}
                  <div className="col-span-2 p-3 bg-surface/20 max-h-[300px] overflow-y-auto font-mono text-[10px] text-muted-foreground">
                    <div className="text-[10px] border-b border-border pb-1.5 mb-2 font-sans font-semibold text-foreground">
                      {selectedFile}
                    </div>
                    <pre className="whitespace-pre overflow-x-auto">
                      {parsedFiles[selectedFile] || ""}
                    </pre>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="diff" className="mt-4">
              <div className="rounded-xl border border-border bg-card p-5 space-y-3">
                <div className="text-xs font-semibold text-muted-foreground mb-1">LangGraph Workspace Diff View</div>
                <pre className="rounded-lg border border-border bg-surface/50 p-4 text-[10px] font-mono leading-relaxed overflow-x-auto whitespace-pre-wrap text-muted-foreground">
{`@@ -12,4 +12,16 @@
-def create_token(user_id: str):
-    return jwt.encode({"user_id": user_id}, SECRET)
+def create_access_token(data: dict, expires_delta: timedelta | None = None):
+    to_encode = data.copy()
+    if expires_delta:
+        expire = datetime.utcnow() + expires_delta
+    else:
+        expire = datetime.utcnow() + timedelta(minutes=15)
+    to_encode.update({"exp": expire})
+    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
+    return encoded_jwt`}
                </pre>
              </div>
            </TabsContent>

            <TabsContent value="security" className="mt-4">
              <div className="rounded-xl border border-border bg-card p-5 space-y-4">
                <div className="flex items-center gap-2 border-b border-border pb-3">
                  <Shield className="h-4 w-4 text-emerald-400" />
                  <span className="text-xs font-semibold text-foreground">SAST Code Security Scanner</span>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between border-b border-border/50 pb-2">
                    <span className="text-xs text-muted-foreground font-mono">1. Secret Leakage Detection</span>
                    <Badge variant="success">PASSED</Badge>
                  </div>
                  <div className="flex items-center justify-between border-b border-border/50 pb-2">
                    <span className="text-xs text-muted-foreground font-mono">2. Dependency Vulnerability</span>
                    <Badge variant="success">PASSED</Badge>
                  </div>
                  <div className="flex items-center justify-between border-b border-border/50 pb-2">
                    <span className="text-xs text-muted-foreground font-mono">3. OWASP Top 10 Patterns</span>
                    <Badge variant="success">SECURE</Badge>
                  </div>
                  <div className="text-[11px] text-muted-foreground bg-emerald-500/5 border border-emerald-500/20 p-2.5 rounded-lg">
                    Security scanner completed with 0 errors. No hardcoded environment secrets or insecure code patterns detected in builder node output.
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="logs" className="mt-4">
              <div className="rounded-xl border border-border bg-card p-5 space-y-3">
                <div className="text-xs font-semibold text-muted-foreground">Execution Container Logs</div>
                <div className="rounded-lg bg-surface/50 border border-border p-4 max-h-[300px] overflow-y-auto font-mono text-[10px] text-muted-foreground space-y-1">
                  <p>[INFO] 2026-06-29 10:55:12 - Starting task execution sequence</p>
                  <p>[INFO] 2026-06-29 10:55:13 - Loading team template config</p>
                  <p>[INFO] 2026-06-29 10:55:14 - Routing task to team_lead node</p>
                  <p>[SUCCESS] 2026-06-29 10:55:18 - Team lead planning complete</p>
                  <p>[INFO] 2026-06-29 10:55:19 - Routing task to builder node</p>
                  <p>[SUCCESS] 2026-06-29 10:55:42 - Code generation complete (2 files written)</p>
                  <p>[INFO] 2026-06-29 10:55:43 - Routing task to reviewer node</p>
                  <p className="text-yellow-500 font-semibold">[INTERRUPT] 2026-06-29 10:55:46 - Paused on human interrupt approval.</p>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
