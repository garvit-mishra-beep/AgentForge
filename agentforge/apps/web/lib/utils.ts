export function cn(...inputs: (string | undefined | null | false)[]) {
  return inputs.filter(Boolean).join(" ");
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
}

export function formatCost(usd: number): string {
  return `$${usd.toFixed(6)}`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function getStatusColor(status: string): string {
  switch (status) {
    case "active":
    case "completed":
      return "text-emerald-600 bg-emerald-50";
    case "running":
      return "text-blue-600 bg-blue-50";
    case "failed":
      return "text-red-600 bg-red-50";
    case "pending":
      return "text-amber-600 bg-amber-50";
    default:
      return "text-slate-600 bg-slate-50";
  }
}
