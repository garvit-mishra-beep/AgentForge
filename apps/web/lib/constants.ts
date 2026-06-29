import {
  Sparkles,
  Code2,
  Search,
  Bug,
  Bot,
  Brain,
  Globe,
  Zap,
  type LucideIcon,
} from "lucide-react";

export type AgentRole = "team_lead" | "builder" | "reviewer" | "tester";
export type AgentStatus = "idle" | "planning" | "building" | "reviewing" | "testing" | "delivering" | "error";
export type MessageType = "plan" | "code" | "review" | "delivery" | "error" | "info" | "test";
export type TaskStatus = "pending" | "running" | "completed" | "failed";

export const AGENT_COLORS = {
  team_lead: { name: "Lead", css: "lead" as const, icon: Sparkles },
  builder: { name: "Builder", css: "builder" as const, icon: Code2 },
  reviewer: { name: "Reviewer", css: "reviewer" as const, icon: Search },
  tester: { name: "Tester", css: "tester" as const, icon: Bug },
};

export const AGENT_CONFIG: Record<AgentRole, {
  label: string;
  badgeVariant: "lead" | "builder" | "reviewer" | "tester";
  icon: LucideIcon;
  color: string;
  bg: string;
  bgSurface: string;
  border: string;
  text: string;
  glow: string;
}> = {
  team_lead: {
    label: "Lead",
    badgeVariant: "lead",
    icon: Sparkles,
    color: "var(--color-lead)",
    bg: "bg-lead-muted",
    bgSurface: "bg-lead-surface",
    border: "border-lead/30",
    text: "text-lead",
    glow: "shadow-[0_0_12px_var(--color-lead)]",
  },
  builder: {
    label: "Builder",
    badgeVariant: "builder",
    icon: Code2,
    color: "var(--color-builder)",
    bg: "bg-builder-muted",
    bgSurface: "bg-builder-surface",
    border: "border-builder/30",
    text: "text-builder",
    glow: "shadow-[0_0_12px_var(--color-builder)]",
  },
  reviewer: {
    label: "Reviewer",
    badgeVariant: "reviewer",
    icon: Search,
    color: "var(--color-reviewer)",
    bg: "bg-reviewer-muted",
    bgSurface: "bg-reviewer-surface",
    border: "border-reviewer/30",
    text: "text-reviewer",
    glow: "shadow-[0_0_12px_var(--color-reviewer)]",
  },
  tester: {
    label: "Tester",
    badgeVariant: "tester",
    icon: Bug,
    color: "var(--color-tester)",
    bg: "bg-tester-muted",
    bgSurface: "bg-tester-surface",
    border: "border-tester/30",
    text: "text-tester",
    glow: "shadow-[0_0_12px_var(--color-tester)]",
  },
};

export const STATUS_CONFIG = {
  idle: { label: "Idle", color: "text-muted-foreground", dot: "bg-muted-foreground" },
  planning: { label: "Planning", color: "text-lead", dot: "bg-lead" },
  building: { label: "Building", color: "text-builder", dot: "bg-builder" },
  reviewing: { label: "Reviewing", color: "text-reviewer", dot: "bg-reviewer" },
  testing: { label: "Testing", color: "text-tester", dot: "bg-tester" },
  delivering: { label: "Delivering", color: "text-deliver", dot: "bg-deliver" },
  error: { label: "Error", color: "text-destructive", dot: "bg-destructive" },
} as const;

export const EXECUTION_STEPS = [
  { node: "team_lead_plan", agent: "team_lead" as AgentRole, label: "Plan" },
  { node: "builder", agent: "builder" as AgentRole, label: "Build" },
  { node: "reviewer", agent: "reviewer" as AgentRole, label: "Review" },
  { node: "tester", agent: "tester" as AgentRole, label: "Test" },
  { node: "team_lead_deliver", agent: "team_lead" as AgentRole, label: "Deliver" },
];

export type ProviderName = "openai" | "anthropic" | "google" | "openrouter" | "groq";

export interface ProviderConfig {
  label: string;
  icon: LucideIcon;
  models: { name: string; size: string; tag: string }[];
  color: string;
}

export const PROVIDER_CONFIG: Record<ProviderName, ProviderConfig> = {
  openai: {
    label: "OpenAI",
    icon: Bot,
    models: [
      { name: "gpt-4o", size: "-", tag: "Best" },
      { name: "gpt-4o-mini", size: "-", tag: "Fast" },
      { name: "gpt-3.5-turbo", size: "-", tag: "Legacy" },
    ],
    color: "var(--color-lead)",
  },
  anthropic: {
    label: "Anthropic",
    icon: Brain,
    models: [
      { name: "claude-sonnet-4-20250514", size: "-", tag: "Best" },
      { name: "claude-haiku-3-5", size: "-", tag: "Fast" },
    ],
    color: "var(--color-builder)",
  },
  google: {
    label: "Google Gemini",
    icon: Globe,
    models: [
      { name: "gemini-2.0-flash", size: "-", tag: "Fast" },
      { name: "gemini-2.0-pro", size: "-", tag: "Best" },
    ],
    color: "var(--color-reviewer)",
  },
  openrouter: {
    label: "OpenRouter",
    icon: Zap,
    models: [
      { name: "openrouter/auto", size: "-", tag: "Auto" },
    ],
    color: "var(--color-tester)",
  },
  groq: {
    label: "Groq",
    icon: Zap,
    models: [
      { name: "mixtral-8x7b-32768", size: "47B", tag: "Fast" },
      { name: "llama-3.3-70b-versatile", size: "70B", tag: "Best" },
    ],
    color: "var(--color-deliver)",
  },
};

export const NAV_ITEMS = [
  { href: "/", label: "Mission Control", icon: "LayoutDashboard" },
  { href: "/projects", label: "Projects", icon: "FolderKanban" },
  { href: "/teams", label: "Teams", icon: "Users" },
  { href: "/tasks", label: "Tasks", icon: "ListChecks" },
  { href: "/executions", label: "Executions", icon: "Activity" },
  { href: "/templates", label: "Templates", icon: "LayoutTemplate" },
  { href: "/analytics", label: "Analytics", icon: "BarChart3" },
  { href: "/settings", label: "Settings", icon: "Settings" },
] as const;
