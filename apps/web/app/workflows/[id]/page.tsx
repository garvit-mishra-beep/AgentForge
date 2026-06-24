/**
 * Upgraded Real-time Workflow Execution Tracking Page
 * Fulfills Feature 6: Visual Agent Graph, Live Chat, Memory Retrieval, Deliverable File Explorer & ZIP Export
 */

'use client'

import { use, useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import {
  Play,
  ArrowLeft,
  Code,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  ListTodo,
  Terminal,
  MessageSquare,
  ShieldCheck,
  AlertTriangle,
  Download,
  Folder,
  FolderOpen,
  FileCode,
  Database,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/loading'
import defaultApi, { API_BASE_URL } from '@/lib/api'
import { initializeWebSocket, cleanupWebSocket, subscribe } from '@/lib/websocket'

interface WorkflowData {
  id: string
  workflow_id: string
  name: string
  description?: string
  status: string
  agent_type: string
  inputs?: Record<string, any>
  created_at: string
}

interface ExecutionData {
  id: string
  workflow_id: string
  status: string
  created_at: string
  error?: string
  result?: string
  checkpoint?: string
}

// =================================
// SIMPLE CODE SYNTAX HIGHLIGHTER
// =================================
const highlightCode = (code: string, fileName: string) => {
  if (!code) return '';
  const ext = fileName.split('.').pop() || '';
  
  // Escape HTML entities to prevent rendering arbitrary html from generated code
  let escaped = code
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  
  if (['py', 'js', 'ts', 'tsx', 'json', 'yml', 'yaml', 'html', 'css', 'md', 'env', 'example'].includes(ext)) {
    // Split on comments and strings to highlight them without nesting issues
    const tokenRegex = /(\/\/[^\n]*|\/\*[\s\S]*?\*\/|#[^\n]*|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)/g;
    const parts = escaped.split(tokenRegex);
    
    const highlighted = parts.map((part, index) => {
      if (index % 2 === 1) {
        if (part.startsWith('//') || part.startsWith('#') || part.startsWith('/*')) {
          return `<span class="text-slate-400 italic">${part}</span>`;
        } else {
          return `<span class="text-emerald-600 font-medium">${part}</span>`;
        }
      } else {
        let h = part;
        // Keywords
        const keywords = /\b(def|class|return|import|from|as|async|await|const|let|var|function|if|else|for|while|try|except|catch|finally|export|default|interface|type|public|private|protected|readonly|new|this|null|undefined|true|false)\b/g;
        h = h.replace(keywords, '<span class="text-indigo-600 font-semibold">$1</span>');
        
        // Numbers
        h = h.replace(/\b(\d+)\b/g, '<span class="text-amber-600">$1</span>');
        
        // Functions
        h = h.replace(/\b(\w+)(?=\()/g, '<span class="text-cyan-600 font-medium">$1</span>');
        
        return h;
      }
    });
    
    escaped = highlighted.join('');
  }
  
  return <div dangerouslySetInnerHTML={{ __html: escaped }} className="whitespace-pre text-left" />;
};

// =================================
// VISUAL SVG NODE GRAPH
// =================================
const AgentGraph = ({ currentStatus }: { currentStatus: string }) => {
  const steps = [
    { id: 'planning', label: 'Planner', x: 80, y: 50 },
    { id: 'developing', label: 'Coder', x: 200, y: 50 },
    { id: 'testing', label: 'Tester', x: 320, y: 50 },
    { id: 'reviewing', label: 'Reviewer', x: 440, y: 50 },
  ];
  
  const getStatusColor = (stepId: string) => {
    const statusOrder = ['created', 'planning', 'developing', 'testing', 'reviewing', 'completed'];
    const currentIndex = statusOrder.indexOf(currentStatus);
    const stepIndex = statusOrder.indexOf(stepId);
    
    if (currentStatus === 'failed') return '#ef4444'; // red
    if (currentStatus === 'escalated') return '#f59e0b'; // amber
    if (currentStatus === stepId) return '#3b82f6'; // blue active
    if (currentIndex > stepIndex) return '#10b981'; // green completed
    return '#94a3b8'; // slate pending
  };

  return (
    <div className="w-full bg-card border rounded-xl p-4 shadow-sm">
      <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">Orchestration Graph</h4>
      <svg viewBox="0 0 520 100" className="w-full h-auto">
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 2 L 10 5 L 0 8 z" fill="#64748b" />
          </marker>
          <filter id="glow-blue" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
        
        {/* Draw connections */}
        <line x1="120" y1="50" x2="160" y2="50" stroke="#64748b" strokeWidth="2" markerEnd="url(#arrow)" />
        <line x1="240" y1="50" x2="280" y2="50" stroke="#64748b" strokeWidth="2" markerEnd="url(#arrow)" />
        <line x1="360" y1="50" x2="400" y2="50" stroke="#64748b" strokeWidth="2" markerEnd="url(#arrow)" />
        
        {/* Loopback path from Reviewer to Coder (rejection loop) */}
        <path d="M 440,30 Q 320,0 200,30" fill="none" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="4" markerEnd="url(#arrow)" />
        
        {/* Loopback path from Tester to Coder (rejection loop) */}
        <path d="M 320,70 Q 260,95 200,70" fill="none" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="4" markerEnd="url(#arrow)" />

        {/* Draw nodes */}
        {steps.map((s) => {
          const color = getStatusColor(s.id);
          const isActive = currentStatus === s.id;
          return (
            <g key={s.id}>
              <circle 
                cx={s.x} 
                cy={s.y} 
                r={24} 
                fill={color} 
                opacity={isActive ? 0.2 : 0.1}
                className={isActive ? "animate-pulse" : ""}
              />
              <circle 
                cx={s.x} 
                cy={s.y} 
                r={18} 
                fill="none" 
                stroke={color} 
                strokeWidth={isActive ? 3 : 2}
                filter={isActive ? "url(#glow-blue)" : ""}
              />
              <text 
                x={s.x} 
                y={s.y + 4} 
                textAnchor="middle" 
                fill={isActive ? "#0f172a" : "#475569"} 
                fontSize={10} 
                fontWeight="bold"
                className="font-sans"
              >
                {s.label[0]}
              </text>
              <text 
                x={s.x} 
                y={s.y + 35} 
                textAnchor="middle" 
                fill={isActive ? color : "#64748b"} 
                fontSize={10}
                fontWeight={isActive ? "bold" : "normal"}
              >
                {s.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

// =================================
// STATUS CIRCLE INDICATORS (Planner ● Developer ● Tester ● Reviewer ●)
// =================================
const StatusIndicators = ({ currentStatus }: { currentStatus: string }) => {
  const getStatusClass = (stepId: string) => {
    const statusOrder = ['created', 'planning', 'developing', 'testing', 'reviewing', 'completed'];
    const currentIndex = statusOrder.indexOf(currentStatus);
    const stepIndex = statusOrder.indexOf(stepId);
    
    if (currentStatus === 'failed') return 'text-red-500';
    if (currentStatus === 'escalated') return 'text-amber-500';
    if (currentStatus === stepId) return 'text-blue-500 animate-pulse font-bold';
    if (currentIndex > stepIndex) return 'text-emerald-500';
    return 'text-muted-foreground';
  };

  return (
    <div className="flex justify-center items-center gap-4 text-xs font-semibold uppercase tracking-wider py-2 bg-muted/20 border rounded-xl shadow-inner mt-2">
      <span className={getStatusClass('planning')}>Planner ●</span>
      <span className={getStatusClass('developing')}>Developer ●</span>
      <span className={getStatusClass('testing')}>Tester ●</span>
      <span className={getStatusClass('reviewing')}>Reviewer ●</span>
    </div>
  );
};

// =================================
// COMPETITION MODE PIPELINE VISUALIZATION
// =================================
const CompetitionModeTimeline = ({ 
  currentStatus, 
  similarProjects, 
  codeArtifacts 
}: { 
  currentStatus: string
  similarProjects: any[]
  codeArtifacts: any[]
}) => {
  const steps = [
    { 
      label: 'Memory Retrieved', 
      active: similarProjects.length > 0, 
      desc: similarProjects.length > 0 ? `✓ Found ${similarProjects.length} baselines` : 'Scanning memory DB...' 
    },
    { 
      label: 'Planner Thinking', 
      active: currentStatus === 'planning' || ['developing', 'testing', 'reviewing', 'completed'].includes(currentStatus), 
      desc: currentStatus === 'planning' ? 'Decomposing tasks...' : 'Plan approved' 
    },
    { 
      label: 'Developer Coding', 
      active: currentStatus === 'developing' || ['testing', 'reviewing', 'completed'].includes(currentStatus), 
      desc: currentStatus === 'developing' ? 'Writing files...' : 'Files written' 
    },
    { 
      label: 'Tester Validating', 
      active: currentStatus === 'testing' || ['reviewing', 'completed'].includes(currentStatus), 
      desc: currentStatus === 'testing' ? 'Executing unittests...' : 'Tests passed' 
    },
    { 
      label: 'Reviewer Reviewing', 
      active: currentStatus === 'reviewing' || currentStatus === 'completed', 
      desc: currentStatus === 'reviewing' ? 'Analyzing code...' : 'Review approved' 
    },
    { 
      label: 'Files Generated', 
      active: codeArtifacts.length > 0, 
      desc: codeArtifacts.length > 0 ? `${codeArtifacts.length} files compiled` : 'Waiting for coder...' 
    },
    { 
      label: 'ZIP Ready', 
      active: currentStatus === 'completed', 
      desc: currentStatus === 'completed' ? 'Package downloadable' : 'Packaging deliverable...' 
    }
  ];

  return (
    <div className="bg-card border rounded-xl p-4 shadow-sm space-y-3">
      <h3 className="font-bold text-sm border-b pb-2 flex items-center gap-2 text-foreground">
        <span className={cn("h-2.5 w-2.5 rounded-full bg-emerald-500", ['running', 'planning', 'developing', 'testing', 'reviewing'].includes(currentStatus) && "animate-ping")}></span>
        <span>Competition Demo Pipeline</span>
      </h3>
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 py-2 overflow-x-auto">
        {steps.map((s, idx) => {
          const isCurrent = (s.label === 'Memory Retrieved' && similarProjects.length > 0 && currentStatus === 'planning') ||
            (s.label === 'Planner Thinking' && currentStatus === 'planning') ||
            (s.label === 'Developer Coding' && currentStatus === 'developing') ||
            (s.label === 'Tester Validating' && currentStatus === 'testing') ||
            (s.label === 'Reviewer Reviewing' && currentStatus === 'reviewing') ||
            (s.label === 'Files Generated' && currentStatus === 'completed' && codeArtifacts.length > 0 && !s.active) ||
            (s.label === 'ZIP Ready' && currentStatus === 'completed');

          return (
            <div key={idx} className="flex flex-row md:flex-col items-center flex-1 text-center min-w-[120px] relative">
              {/* Node indicator */}
              <div className={cn(
                "h-8 w-8 rounded-full flex items-center justify-center border-2 text-[10px] font-bold transition-all duration-500",
                s.active 
                  ? "bg-emerald-500/10 border-emerald-500 text-emerald-500 shadow-md shadow-emerald-500/10" 
                  : isCurrent
                    ? "bg-blue-500/10 border-blue-500 text-blue-500 animate-pulse font-extrabold scale-110"
                    : "bg-muted border-border text-muted-foreground"
              )}>
                {s.active ? "✓" : idx + 1}
              </div>
              
              {/* Connecting line */}
              {idx < steps.length - 1 && (
                <div className="hidden md:block absolute top-4 left-[60%] w-[80%] h-0.5 bg-border -z-10">
                  <div className={cn(
                    "h-full bg-emerald-500 transition-all duration-700",
                    s.active ? "w-full" : "w-0"
                  )} />
                </div>
              )}

              {/* Text metadata */}
              <div className="ml-3 md:ml-0 md:mt-2 text-left md:text-center">
                <span className={cn(
                  "text-[10px] font-bold block uppercase tracking-wider",
                  s.active ? "text-emerald-500" : isCurrent ? "text-blue-500 font-extrabold" : "text-muted-foreground"
                )}>
                  {s.label}
                </span>
                <span className="text-[8px] text-muted-foreground block font-mono truncate max-w-[110px]">
                  {s.desc}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// =================================
// CHAT PANEL DETAILS (Real-Time Auto-Scroll Feed)
// =================================
const ChatPanel = ({ messages }: { messages: any[] }) => {
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const getAvatarGradient = (role: string) => {
    switch (role) {
      case 'planner': return 'from-indigo-500 to-purple-600';
      case 'developer': return 'from-blue-500 to-cyan-500';
      case 'tester': return 'from-amber-500 to-orange-500';
      case 'reviewer': return 'from-emerald-500 to-teal-500';
      default: return 'from-slate-500 to-slate-700';
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'planner': return 'Architect';
      case 'developer': return 'Coder';
      case 'tester': return 'Tester';
      case 'reviewer': return 'Reviewer';
      default: return role;
    }
  };

  return (
    <div className="rounded-xl border bg-card p-4 shadow-sm flex flex-col h-[400px]">
      <h3 className="font-bold text-sm border-b pb-2 flex items-center gap-2 mb-2 text-foreground">
        <MessageSquare className="h-4 w-4 text-primary" />
        <span>Live Agent Collaboration Feed</span>
      </h3>
      <div className="flex-1 overflow-y-auto space-y-3 pr-1 text-sm scrollbar-thin">
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground text-xs py-24">
            No agent conversations logged yet. Run execution to see agent collaboration.
          </div>
        ) : (
          messages.map((m, idx) => (
            <div key={idx} className="flex gap-2.5 items-start animate-fade-in">
              <div className={cn(
                "h-7 w-7 rounded-lg text-[10px] font-bold text-white flex items-center justify-center shrink-0 bg-gradient-to-br",
                getAvatarGradient(m.role)
              )}>
                {m.role[0].toUpperCase()}
              </div>
              <div className="flex-1 bg-muted/40 rounded-lg p-2.5 border border-muted-foreground/10">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-semibold text-xs text-foreground uppercase tracking-wider">
                    {getRoleLabel(m.role)}
                  </span>
                  <span className="text-[9px] text-muted-foreground">
                    {new Date(m.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </span>
                </div>
                <p className="text-muted-foreground text-xs leading-relaxed font-mono whitespace-pre-line">
                  {m.content}
                </p>
              </div>
            </div>
          ))
        )}
        <div ref={chatEndRef} />
      </div>
    </div>
  );
};

// =================================
// MEMORY RETRIEVAL VIEW
// =================================
const MemoryRetrievalPanel = ({ similarProjects }: { similarProjects: any[] }) => {
  return (
    <div className="rounded-xl border bg-card p-4 shadow-sm space-y-3">
      <h3 className="font-bold text-sm border-b pb-2 flex items-center gap-2 text-foreground">
        <Database className="h-4 w-4 text-primary" />
        <span>Memory Retrieval Context</span>
      </h3>
      {similarProjects.length === 0 ? (
        <div className="text-center text-muted-foreground text-xs py-8 bg-muted/20 rounded-lg border border-dashed">
          No similar projects matched in memory database yet.
        </div>
      ) : (
        <div className="space-y-3 max-h-[220px] overflow-y-auto scrollbar-thin">
          <div className="text-[11px] font-semibold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/20 px-2 py-1.5 rounded-md border border-emerald-200 dark:border-emerald-800/30">
            ✓ Found {similarProjects.length} similar project{similarProjects.length > 1 ? 's' : ''}. Reusing architecture and database patterns.
          </div>
          {similarProjects.map((p, idx) => (
            <div key={idx} className="bg-muted/40 p-2.5 rounded-lg border border-muted-foreground/10 space-y-1.5">
              <div className="flex justify-between items-center">
                <span className="font-mono text-xs font-bold text-foreground">{p.project_key}</span>
                <span className="text-[9px] bg-primary/10 text-primary px-1.5 py-0.5 rounded font-semibold">
                  Match Context
                </span>
              </div>
              <p className="text-[10px] text-muted-foreground leading-normal">{p.description}</p>
              {p.architecture && p.architecture.phases && (
                <div className="text-[9px] text-muted-foreground pt-1.5 border-t border-muted-foreground/5">
                  <span className="font-semibold text-foreground block mb-1">Retrieved Phases:</span>
                  <div className="flex flex-wrap gap-1">
                    {p.architecture.phases.map((ph: any, i: number) => (
                      <span key={i} className="bg-card px-1.5 py-0.5 rounded border text-[8px] font-mono">
                        {ph.name} ({ph.estimated_hours}h)
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// =================================
// DYNAMIC FILE EXPLORER COMPONENTS
// =================================
interface FileNodeProps {
  name: string
  artifact: any
  onSelectFile: (art: any) => void
  activeFileName?: string
}

const FileNode = ({ name, artifact, onSelectFile, activeFileName }: FileNodeProps) => {
  const isActive = activeFileName === artifact.name;
  return (
    <div 
      onClick={() => onSelectFile(artifact)}
      className={cn(
        "flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer text-xs transition-all hover:bg-accent/40 font-mono",
        isActive ? "bg-primary/10 text-primary font-semibold border-l-2 border-primary" : "text-muted-foreground hover:text-foreground"
      )}
    >
      <FileCode className={cn("h-3.5 w-3.5", isActive ? "text-primary" : "text-muted-foreground")} />
      <span className="truncate">{name}</span>
    </div>
  );
};

interface FolderNodeProps {
  name: string
  dir: any
  onSelectFile: (art: any) => void
  activeFileName?: string
}

const FolderNode = ({ name, dir, onSelectFile, activeFileName }: FolderNodeProps) => {
  const [isOpen, setIsOpen] = useState(true);
  
  const hasFiles = dir.files.length > 0;
  const hasSubDirs = Object.keys(dir.dirs).length > 0;
  if (!hasFiles && !hasSubDirs) return null;

  return (
    <div className="space-y-1">
      <div 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer text-xs font-semibold text-foreground hover:bg-accent/30 transition-all font-mono"
      >
        {isOpen ? <FolderOpen className="h-3.5 w-3.5 text-primary" /> : <Folder className="h-3.5 w-3.5 text-muted-foreground" />}
        <span>{name}/</span>
      </div>
      
      {isOpen && (
        <div className="pl-3 border-l border-muted-foreground/10 ml-3.5 space-y-1">
          {Object.keys(dir.dirs).map((dirName) => (
            <FolderNode 
              key={dirName} 
              name={dirName} 
              dir={dir.dirs[dirName]} 
              onSelectFile={onSelectFile}
              activeFileName={activeFileName}
            />
          ))}
          {dir.files.map((file: any) => (
            <FileNode 
              key={file.artifact.name} 
              name={file.name} 
              artifact={file.artifact} 
              onSelectFile={onSelectFile}
              activeFileName={activeFileName}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Parser to group files dynamically under backend/, frontend/, tests/ or root
const buildFileTree = (artifacts: any[]) => {
  const root: any = { files: [], dirs: {} };
  
  artifacts.forEach((art) => {
    let pathParts = art.name.split('/');
    if (pathParts.length === 1) {
      if (art.name === 'README.md') {
        pathParts = ['README.md'];
      } else if (art.name === 'architecture.md') {
        pathParts = ['architecture.md'];
      } else if (art.name.endsWith('.py') && art.name.startsWith('test_')) {
        pathParts = ['tests', art.name];
      } else if (art.name.endsWith('.py')) {
        pathParts = ['backend', art.name];
      } else if (art.name.endsWith('.js') || art.name.endsWith('.tsx') || art.name.endsWith('.ts') || art.name.endsWith('.html') || art.name.endsWith('.css') || art.name.endsWith('.json')) {
        pathParts = ['frontend', art.name];
      } else {
        pathParts = ['backend', art.name];
      }
    }
    
    let current = root;
    for (let i = 0; i < pathParts.length; i++) {
      const part = pathParts[i];
      if (i === pathParts.length - 1) {
        current.files.push({ name: part, artifact: art });
      } else {
        if (!current.dirs[part]) {
          current.dirs[part] = { files: [], dirs: {} };
        }
        current = current.dirs[part];
      }
    }
  });
  return root;
};

const GeneratedFilesPanel = ({ 
  codeArtifacts, 
  onSelectFile, 
  activeFileName, 
  handleDownloadZip 
}: { 
  codeArtifacts: any[]
  onSelectFile: (art: any) => void
  activeFileName?: string
  handleDownloadZip: () => void
}) => {
  const fileTree = buildFileTree(codeArtifacts);
  const rootFiles = fileTree.files;
  const rootDirs = fileTree.dirs;

  return (
    <div className="rounded-xl border bg-card p-4 shadow-sm flex flex-col h-[380px]">
      <h3 className="font-bold text-sm border-b pb-2 flex items-center gap-2 mb-2 text-foreground">
        <Folder className="h-4 w-4 text-primary" />
        <span>Generated Deliverables Explorer</span>
      </h3>
      <div className="flex-1 overflow-y-auto pr-1 text-sm scrollbar-thin space-y-1">
        {codeArtifacts.length === 0 ? (
          <div className="text-center text-muted-foreground text-xs py-24">
            No files compiled yet. Press Run Execution.
          </div>
        ) : (
          <div className="space-y-1">
            {Object.keys(rootDirs).map((dirName) => (
              <FolderNode 
                key={dirName} 
                name={dirName} 
                dir={rootDirs[dirName]} 
                onSelectFile={onSelectFile}
                activeFileName={activeFileName}
              />
            ))}
            {rootFiles.map((file: any) => (
              <FileNode 
                key={file.artifact.name} 
                name={file.name} 
                artifact={file.artifact} 
                onSelectFile={onSelectFile}
                activeFileName={activeFileName}
              />
            ))}
          </div>
        )}
      </div>
      
      {codeArtifacts.length > 0 && (
        <Button
          onClick={handleDownloadZip}
          className="w-full gap-2 bg-emerald-600 hover:bg-emerald-700 text-white mt-3 shadow-md hover:shadow-lg transition-all text-xs font-semibold py-2 shrink-0"
        >
          <Download className="h-3.5 w-3.5" />
          <span>Download Project (.zip)</span>
        </Button>
      )}
    </div>
  );
};


// =================================
// WORKFLOW DETAIL PAGE
// =================================
export default function WorkflowDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: workflowId } = use(params)

  const [workflow, setWorkflow] = useState<WorkflowData | null>(null)
  const [execution, setExecution] = useState<ExecutionData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Real-time states updated via WebSockets
  const [currentStatus, setCurrentStatus] = useState<string>('created')
  const [currentMessage, setCurrentMessage] = useState<string>('Workflow initialized. Press Run to start orchestration.')
  const [tasks, setTasks] = useState<any[]>([])
  const [codeArtifacts, setCodeArtifacts] = useState<any[]>([])
  const [similarProjects, setSimilarProjects] = useState<any[]>([])
  const [testLogs, setTestLogs] = useState<string[]>([])
  const [reviewResult, setReviewResult] = useState<any>(null)
  const [retryCount, setRetryCount] = useState<number>(0)
  const [messages, setMessages] = useState<any[]>([])
  
  // Selection/active tab states
  const [activeFile, setActiveFile] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'timeline' | 'code' | 'tests' | 'review'>('timeline')

  const loadMessages = async (execId: string) => {
    try {
      const res = await (defaultApi.workflowsAPI as any).getExecutionMessages(workflowId, execId)
      if (res.data) {
        setMessages(res.data)
      }
    } catch (e) {
      console.error("Failed to load chat logs", e)
    }
  }

  // Load initial workflow data
  useEffect(() => {
    async function loadData() {
      setIsLoading(true)
      try {
        const wfResponse = await defaultApi.workflowsAPI.get(workflowId)
        if (wfResponse.error) {
          throw new Error(wfResponse.error.message)
        }
        if (wfResponse.data) {
          setWorkflow(wfResponse.data)
          setCurrentStatus(wfResponse.data.status)
        }

        const execsResponse = await defaultApi.workflowsAPI.listExecutions(workflowId)
        if (execsResponse.data && execsResponse.data.length > 0) {
          const latest = execsResponse.data[0]
          setExecution(latest)
          setCurrentStatus(latest.status)
          
          loadMessages(latest.id)
          
          if (latest.result) {
            try {
              const resObj = JSON.parse(latest.result)
              if (resObj.code_artifacts) setCodeArtifacts(resObj.code_artifacts)
              if (resObj.tasks) setTasks(resObj.tasks)
              if (resObj.review_result) setReviewResult(resObj.review_result)
              if (resObj.similar_projects) setSimilarProjects(resObj.similar_projects)
            } catch (ex) {}
          }
          
          if (latest.checkpoint) {
            try {
              const chkObj = JSON.parse(latest.checkpoint)
              if (chkObj.similar_projects) setSimilarProjects(chkObj.similar_projects)
            } catch (ex) {}
          }
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load workflow details.')
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [workflowId])

  // WebSocket subscriptions
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const host = window.location.host
    const wsUrl = process.env.NEXT_PUBLIC_API_URL
      ? process.env.NEXT_PUBLIC_API_URL.replace(/^http/, 'ws') + `/ws/workflows/${workflowId}`
      : `${protocol}://${host}/api/ws/workflows/${workflowId}`

    initializeWebSocket({
      url: wsUrl,
      onConnect: () => {
        console.log('WS connected to workflow events')
      },
      onDisconnect: () => {
        console.log('WS disconnected')
      }
    })

    const unsubEvent = subscribe('execution_started', () => {})

    const wsListener = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'execution.event') {
          const payload = data.payload
          if (payload.status) {
            setCurrentStatus(payload.status)
          }
          if (payload.message) {
            setCurrentMessage(payload.message)
          }
          if (payload.tasks) {
            setTasks(payload.tasks)
          }
          if (payload.artifacts) {
            setCodeArtifacts(payload.artifacts)
          }
          if (payload.similar_projects) {
            setSimilarProjects(payload.similar_projects)
          }
          if (payload.test_logs) {
            setTestLogs(payload.test_logs)
          }
          if (payload.review) {
            setReviewResult(payload.review)
            if (payload.review.status === 'rejected') {
              setRetryCount((prev) => prev + 1)
            }
          }
        } else if (data.type === 'message.new') {
          const payload = data.payload
          setMessages((prev) => {
            if (prev.some(m => m.id === payload.id)) return prev;
            return [...prev, payload];
          })
        } else if (data.type === 'execution.completed') {
          setCurrentStatus('completed')
          setCurrentMessage('Execution finished successfully!')
        } else if (data.type === 'execution.failed') {
          setCurrentStatus('failed')
          setCurrentMessage(`Execution failed: ${data.payload.error}`)
        }
      } catch (e) {
        // Parse error
      }
    }

    const timer = setInterval(() => {
      const socket = (window as any).wsInstance as WebSocket | undefined
      if (socket) {
        socket.addEventListener('message', wsListener)
        clearInterval(timer)
      }
    }, 500)

    return () => {
      clearInterval(timer)
      unsubEvent()
      const socket = (window as any).wsInstance as WebSocket | undefined
      if (socket) {
        socket.removeEventListener('message', wsListener)
      }
      cleanupWebSocket()
    }
  }, [workflowId])

  // Select file from explorer
  const handleSelectFile = (artifact: any) => {
    setActiveFile(artifact)
    setActiveTab('code')
  }

  // Pre-select first file when code artifacts are populated
  useEffect(() => {
    if (codeArtifacts.length > 0 && !activeFile) {
      const readme = codeArtifacts.find(a => a.name === 'README.md' || a.name.endsWith('README.md'));
      setActiveFile(readme || codeArtifacts[0])
    }
  }, [codeArtifacts, activeFile])

  // Run a new execution
  const handleRunExecution = async () => {
    if (!workflow) return
    setCurrentStatus('running')
    setCurrentMessage('Initializing multi-agent orchestrator...')
    setTasks([])
    setCodeArtifacts([])
    setSimilarProjects([])
    setTestLogs([])
    setReviewResult(null)
    setRetryCount(0)
    setMessages([])
    setActiveFile(null)
    setActiveTab('timeline')

    try {
      const res = await defaultApi.workflowsAPI.execute(workflowId, {
        priority: 5,
        cancel_on_timeout: true,
      })
      if (res.error) {
        throw new Error(res.error.message)
      }
      setExecution(res.data)
    } catch (err: any) {
      setCurrentStatus('failed')
      setCurrentMessage(err.message || 'Failed to trigger execution.')
    }
  }

  const handleDownloadZip = () => {
    if (!execution) return
    window.open(`${API_BASE_URL}/workflows/${workflowId}/executions/${execution.id}/download`, '_blank')
  }

  if (isLoading) {
    return (
      <div className="flex h-[400px] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="text-muted-foreground text-sm">Loading workflow workspace...</span>
        </div>
      </div>
    )
  }

  if (error || !workflow) {
    return (
      <div className="rounded-xl border border-destructive/20 bg-destructive/10 p-6 text-center max-w-2xl mx-auto space-y-4">
        <XCircle className="h-12 w-12 text-destructive mx-auto" />
        <h3 className="text-lg font-bold">Failed to load workflow</h3>
        <p className="text-muted-foreground text-sm">{error || 'Workflow not found.'}</p>
        <Link href="/workflows">
          <Button variant="outline" className="mt-2">
            Back to Dashboard
          </Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b pb-4 gap-4">
        <div className="flex items-center gap-3">
          <Link href="/workflows" className="p-2 border rounded-lg hover:bg-accent hover:text-accent-foreground transition-all">
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono bg-muted px-2 py-0.5 rounded text-muted-foreground">
                {workflow.workflow_id}
              </span>
              {execution && (
                <span className="text-xs font-mono bg-muted px-2 py-0.5 rounded text-muted-foreground">
                  Run: {execution.id.slice(0, 8)}
                </span>
              )}
              <span className="text-xs inline-flex items-center gap-1 text-primary bg-primary/10 rounded-full px-2.5 py-0.5 font-medium">
                {retryCount > 0 ? `Fix iteration #${retryCount}` : 'First run'}
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight mt-1">{workflow.name}</h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {['running', 'planning', 'developing', 'testing', 'reviewing'].includes(currentStatus) ? (
            <div className="flex items-center gap-2 border px-4 py-2 rounded-lg bg-card text-sm font-medium">
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
              <span>Orchestrating...</span>
            </div>
          ) : (
            <Button
              onClick={handleRunExecution}
              className="gap-2 shadow-md hover:shadow-lg transition-all"
            >
              <Play className="h-4 w-4" />
              <span>Run Execution</span>
            </Button>
          )}
        </div>
      </div>

      {/* Primary Workflow detail grid layout */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column: Graph status, Memory contexts, and dynamic deliverables explorer */}
        <div className="lg:col-span-1 space-y-4">
          <div>
            <AgentGraph currentStatus={currentStatus} />
            <StatusIndicators currentStatus={currentStatus} />
          </div>

          <MemoryRetrievalPanel similarProjects={similarProjects} />

          <GeneratedFilesPanel 
            codeArtifacts={codeArtifacts} 
            onSelectFile={handleSelectFile} 
            activeFileName={activeFile?.name}
            handleDownloadZip={handleDownloadZip}
          />
        </div>

        {/* Right Columns: Collaboration Chat & Tab workspace panel */}
        <div className="lg:col-span-2 space-y-4">
          {/* Real-time Status Card */}
          <div className="rounded-xl border bg-card p-4 shadow-sm flex items-center gap-3">
            <div className={cn(
              'h-10 w-10 shrink-0 flex items-center justify-center rounded-xl bg-muted text-muted-foreground',
              currentStatus === 'completed' && 'bg-green-500/10 text-green-700',
              currentStatus === 'failed' && 'bg-destructive/10 text-destructive',
              ['running', 'planning', 'developing', 'testing', 'reviewing'].includes(currentStatus) && 'bg-primary/10 text-primary'
            )}>
              {currentStatus === 'completed' ? <CheckCircle2 className="h-5 w-5" /> :
               currentStatus === 'failed' ? <XCircle className="h-5 w-5" /> :
               <Clock className="h-5 w-5" />}
            </div>
            <div>
              <div className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider">
                Status: {currentStatus}
              </div>
              <div className="text-sm font-medium mt-0.5 text-foreground leading-snug">
                {currentMessage}
              </div>
            </div>
          </div>

          {/* Competition Demo Pipeline Tracker */}
          <CompetitionModeTimeline 
            currentStatus={currentStatus} 
            similarProjects={similarProjects} 
            codeArtifacts={codeArtifacts} 
          />

          {/* Real-Time chat between Planner, Coder, Tester, Reviewer */}
          <ChatPanel messages={messages} />

          {/* Active Workspace Tabs (Timeline, Source Code, Test output terminal, Review scorecard) */}
          <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
            <div className="flex border-b border-border bg-card p-1 gap-1">
              <button
                onClick={() => setActiveTab('timeline')}
                className={cn(
                  'flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-semibold rounded-lg transition-all',
                  activeTab === 'timeline'
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
                )}
              >
                <ListTodo className="h-3.5 w-3.5" />
                <span>Tasks Checklist</span>
              </button>
              <button
                onClick={() => setActiveTab('code')}
                disabled={codeArtifacts.length === 0}
                className={cn(
                  'flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-semibold rounded-lg transition-all',
                  activeTab === 'code'
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent/50 disabled:opacity-40 disabled:cursor-not-allowed'
                )}
              >
                <Code className="h-3.5 w-3.5" />
                <span>Source Viewer</span>
              </button>
              <button
                onClick={() => setActiveTab('tests')}
                disabled={testLogs.length === 0}
                className={cn(
                  'flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-semibold rounded-lg transition-all',
                  activeTab === 'tests'
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent/50 disabled:opacity-40 disabled:cursor-not-allowed'
                )}
              >
                <Terminal className="h-3.5 w-3.5" />
                <span>Test Suite Logs</span>
              </button>
              <button
                onClick={() => setActiveTab('review')}
                disabled={!reviewResult}
                className={cn(
                  'flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-semibold rounded-lg transition-all',
                  activeTab === 'review'
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent/50 disabled:opacity-40 disabled:cursor-not-allowed'
                )}
              >
                <MessageSquare className="h-3.5 w-3.5" />
                <span>Audit Review</span>
              </button>
            </div>

            <div className="p-4 min-h-[300px] bg-card/50">
              {activeTab === 'timeline' && (
                <div className="space-y-4">
                  <h4 className="font-semibold text-xs border-b pb-1.5 text-muted-foreground uppercase">Actionable Tasks List</h4>
                  {tasks.length === 0 ? (
                    <div className="text-center text-muted-foreground text-xs py-12">
                      No active tasks. Press Run Execution to start.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {tasks.map((task: any, idx: number) => (
                        <div key={idx} className="flex items-center justify-between rounded-lg border bg-muted/40 p-2.5 hover:bg-muted/60 transition-colors">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono bg-primary/10 text-primary px-1.5 py-0.5 rounded font-semibold">
                              {task.id}
                            </span>
                            <div>
                              <span className="font-medium text-xs text-foreground block">{task.name}</span>
                              <p className="text-[10px] text-muted-foreground leading-normal mt-0.5">{task.description}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="text-[9px] text-muted-foreground bg-card border rounded px-1.5 py-0.5">
                              {task.estimated_effort}
                            </span>
                            <span className={cn(
                              'inline-flex items-center rounded-full px-1.5 py-0.5 text-[9px] font-medium border uppercase',
                              task.status === 'completed'
                                ? 'bg-green-50 text-green-700 border-green-200'
                                : 'bg-amber-50 text-amber-700 border-amber-200'
                            )}>
                              {task.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'code' && activeFile && (
                <div className="space-y-4">
                  <div className="rounded-lg border bg-muted/20 overflow-hidden">
                    <div className="flex items-center justify-between bg-muted/60 px-3 py-1.5 border-b">
                      <div className="flex items-center gap-1.5">
                        <Code className="h-3.5 w-3.5 text-primary" />
                        <span className="font-mono text-[11px] font-bold text-foreground">{activeFile.name}</span>
                      </div>
                      <span className="text-[9px] font-mono uppercase bg-card border px-1.5 py-0.5 rounded text-muted-foreground">
                        {activeFile.type}
                      </span>
                    </div>
                    <pre className="p-3 overflow-auto text-[10px] font-mono bg-card/60 text-slate-800 leading-normal max-h-[350px]">
                      <code>{highlightCode(activeFile.content, activeFile.name)}</code>
                    </pre>
                  </div>
                </div>
              )}

              {activeTab === 'tests' && (
                <div className="space-y-3 font-mono text-[10px] bg-slate-950 text-emerald-400 p-3 rounded-lg min-h-[200px] border border-slate-800 shadow-inner overflow-auto leading-normal max-h-[350px]">
                  {testLogs.map((log: string, idx: number) => (
                    <div key={idx} className={cn(
                      log.includes('OK') && 'text-emerald-300 font-semibold',
                      log.includes('SUCCESS') && 'text-green-400 font-bold border-t border-emerald-950/50 pt-2',
                      (log.includes('FAILED') || log.includes('ERROR')) && 'text-red-400 font-bold',
                      log.includes('RUNNING') && 'text-amber-400'
                    )}>
                      {log}
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'review' && reviewResult && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b pb-2">
                    <div className="flex items-center gap-2">
                      <ShieldCheck className={cn('h-5 w-5', reviewResult.status === 'approved' ? 'text-green-600' : 'text-amber-500')} />
                      <div>
                        <h4 className="font-semibold text-xs text-foreground">Code Audit Scorecard</h4>
                        <p className="text-[9px] text-muted-foreground">By Senior Audit Reviewer Agent</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 text-xs">
                      <div>
                        <span className="text-[9px] text-muted-foreground block">Quality Rating</span>
                        <span className={cn('font-bold text-sm', reviewResult.quality_score >= 80 ? 'text-green-600' : 'text-amber-600')}>
                          {reviewResult.quality_score}/100
                        </span>
                      </div>
                      <div>
                        <span className="text-[9px] text-muted-foreground block">Coverage</span>
                        <span className="font-bold text-sm text-foreground">{reviewResult.coverage}%</span>
                      </div>
                    </div>
                  </div>

                  {reviewResult.status === 'rejected' ? (
                    <div className="space-y-3 animate-fade-in">
                      <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-3 flex gap-2 text-amber-700 text-xs">
                        <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600" />
                        <div>
                          <div className="font-semibold">Rejection details:</div>
                          <div className="mt-0.5 leading-relaxed">{reviewResult.rejection_reason}</div>
                        </div>
                      </div>

                      <div className="space-y-1">
                        <h5 className="font-semibold text-[10px] text-foreground uppercase tracking-wider">Required Enhancements</h5>
                        <ul className="list-disc pl-4 space-y-0.5 text-xs text-muted-foreground">
                          {reviewResult.improvements.map((imp: string, idx: number) => (
                            <li key={idx} className="leading-snug">{imp}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-1 animate-fade-in">
                      <h5 className="font-semibold text-[10px] text-foreground uppercase tracking-wider">Audit Comments</h5>
                      <ul className="list-disc pl-4 space-y-0.5 text-xs text-muted-foreground">
                        {reviewResult.comments.map((comment: string, idx: number) => (
                          <li key={idx} className="leading-snug">{comment}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
