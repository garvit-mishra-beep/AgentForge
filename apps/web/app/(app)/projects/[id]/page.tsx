"use client";

import { use, useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getProject, listTasks, listTeams, listProjectFiles, listExecutions } from "@/lib/api";
import { FileUpload } from "@/components/task/file-upload";
import { ContextViewer } from "@/components/task/context-viewer";
import { MemoryViewer } from "@/components/task/memory-viewer";
import type { Project, Task, Team, Execution, ProjectFile } from "@/lib/types";
import { Loader2, ArrowLeft, FolderOpen, Plus, ChevronRight } from "lucide-react";
import Link from "next/link";
import { FormattedDate } from "@/components/ui/formatted-date";


export default function ProjectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [files, setFiles] = useState<ProjectFile[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const [p, t, tm, f, e] = await Promise.all([
        getProject(id).catch(() => null),
        listTasks({ project_id: id }).catch(() => []),
        listTeams().catch(() => []),
        listProjectFiles(id).catch(() => []),
        listExecutions({ project_id: id }).catch(() => []),
      ]);
      setProject(p);
      setTasks(t);
      setTeams(tm.filter((team) => p?.team_ids?.includes(team.id)));
      setFiles(f);
      setExecutions(e);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const handleFilesChange = useCallback(() => {
    listProjectFiles(id).then(setFiles).catch(() => {});
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        Loading project...
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <p className="text-sm">Project not found</p>
        <Link href="/projects" className="text-primary text-sm mt-2 hover:underline">Back to projects</Link>
      </div>
    );
  }

  const statusCounts = {
    completed: tasks.filter((t) => t.status === "completed").length,
    running: tasks.filter((t) => t.status === "running").length,
    failed: tasks.filter((t) => t.status === "failed").length,
    pending: tasks.filter((t) => t.status === "pending").length,
  };

  return (
    <div className="space-y-6">
      <div>
        <Link href="/projects" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors mb-3">
          <ArrowLeft className="h-3 w-3" />
          Back to projects
        </Link>
        <div className="flex items-center gap-3 mb-1">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface">
            <FolderOpen className="h-4 w-4 text-primary" />
          </div>
          <h1 className="text-xl font-bold tracking-tight">{project.name}</h1>
        </div>
        {project.description && (
          <p className="text-sm text-muted-foreground mt-1">{project.description}</p>
        )}
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="text-sm text-muted-foreground">
          <span className="text-foreground font-semibold">{tasks.length}</span> tasks
        </div>
        <div className="text-sm text-muted-foreground">
          <span className="text-foreground font-semibold">{teams.length}</span> teams
        </div>
        <div className="text-sm text-muted-foreground">
          <span className="text-foreground font-semibold">{files.length}</span> files
        </div>
        {statusCounts.running > 0 && <Badge variant="warning">{statusCounts.running} running</Badge>}
        {statusCounts.failed > 0 && <Badge variant="destructive">{statusCounts.failed} failed</Badge>}
        {statusCounts.completed > 0 && <Badge variant="success">{statusCounts.completed} completed</Badge>}
      </div>

      <Tabs defaultValue="tasks">
        <TabsList>
          <TabsTrigger value="tasks">Tasks</TabsTrigger>
          <TabsTrigger value="teams">Teams</TabsTrigger>
          <TabsTrigger value="executions">Executions</TabsTrigger>
          <TabsTrigger value="files">Files</TabsTrigger>
          <TabsTrigger value="context">Context</TabsTrigger>
          <TabsTrigger value="memories">Memories</TabsTrigger>
        </TabsList>

        <TabsContent value="tasks">
          {tasks.length === 0 ? (
            <div className="text-center py-12 space-y-3">
              <p className="text-sm text-muted-foreground">No tasks in this project yet.</p>
              <Link href="/tasks">
                <Button size="sm">
                  <Plus className="h-3.5 w-3.5" />
                  Create Task
                </Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-1.5">
              {tasks.map((task) => (
                <Link key={task.id} href={`/tasks/${task.id}`} className="block group">
                  <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-3 hover:border-border-hover transition-all">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">{task.title}</p>
                      <p className="text-xs text-muted-foreground truncate">{task.description}</p>
                    </div>
                    <Badge variant={task.status === "completed" ? "success" : task.status === "running" ? "warning" : task.status === "failed" ? "destructive" : "secondary"}>
                      {task.status}
                    </Badge>
                    <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors shrink-0" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="teams">
          {teams.length === 0 ? (
            <div className="text-center py-12 space-y-3">
              <p className="text-sm text-muted-foreground">No teams assigned to this project.</p>
              <Link href="/teams">
                <Button size="sm">
                  <Plus className="h-3.5 w-3.5" />
                  Create Team
                </Button>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {teams.map((team) => (
                <Link key={team.id} href={`/teams/${team.id}`} className="block group">
                  <div className="rounded-lg border border-border bg-card p-4 hover:border-border-hover transition-all">
                    <h3 className="text-sm font-semibold group-hover:text-primary transition-colors">{team.name}</h3>
                    <p className="text-xs text-muted-foreground mt-1">{team.description}</p>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {team.members.map((m) => (
                        <Badge key={m.id} variant="secondary" className="text-[10px]">{m.role}</Badge>
                      ))}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="executions">
          {executions.length === 0 ? (
            <div className="text-center py-12 text-sm text-muted-foreground">
              No executions yet. Create a task to see execution history.
            </div>
          ) : (
            <div className="space-y-1.5">
              {executions.map((exec) => (
                <Link key={exec.id} href={`/executions/${exec.id}`} className="block group">
                  <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-3 hover:border-border-hover transition-all">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium">Execution {exec.id.slice(0, 8)}</p>
                      <p className="text-[10px] text-muted-foreground">
                        {exec.started_at ? <FormattedDate date={exec.started_at} type="datetime" /> : ""}
                      </p>
                    </div>
                    <Badge variant={exec.status === "completed" ? "success" : exec.status === "failed" ? "destructive" : "warning"}>
                      {exec.status}
                    </Badge>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="files">
          <FileUpload projectId={id} files={files} onFilesChange={handleFilesChange} />
        </TabsContent>
        <TabsContent value="context">
          <ContextViewer projectId={id} />
        </TabsContent>
        <TabsContent value="memories">
          <MemoryViewer projectId={id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
