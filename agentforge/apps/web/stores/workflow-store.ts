import { create } from "zustand";
import type { Workflow, Execution } from "@/types";
import { api } from "@/lib/api";

interface WorkflowState {
  workflows: Workflow[];
  executions: Execution[];
  selectedWorkflow: Workflow | null;
  isLoading: boolean;
  error: string | null;
  fetchWorkflows: () => Promise<void>;
  fetchWorkflow: (id: string) => Promise<void>;
  createWorkflow: (data: Partial<Workflow>) => Promise<Workflow | null>;
  executeWorkflow: (id: string, input: Record<string, unknown>) => Promise<Execution | null>;
  fetchExecutions: (workflowId?: string) => Promise<void>;
}

export const useWorkflowStore = create<WorkflowState>((set) => ({
  workflows: [],
  executions: [],
  selectedWorkflow: null,
  isLoading: false,
  error: null,

  fetchWorkflows: async () => {
    set({ isLoading: true, error: null });
    const res = await api.get<Workflow[]>("/workflows");
    set({ workflows: res.data || [], isLoading: false, error: res.error?.message || null });
  },

  fetchWorkflow: async (id: string) => {
    set({ isLoading: true, error: null });
    const res = await api.get<Workflow>(`/workflows/${id}`);
    set({ selectedWorkflow: res.data || null, isLoading: false, error: res.error?.message || null });
  },

  createWorkflow: async (data: Partial<Workflow>) => {
    const res = await api.post<Workflow>("/workflows", data);
    if (res.error) return null;
    if (res.data) {
      set((state) => ({ workflows: [res.data!, ...state.workflows] }));
      return res.data;
    }
    return null;
  },

  executeWorkflow: async (id: string, input: Record<string, unknown>) => {
    const res = await api.post<Execution>(`/workflows/${id}/execute`, input);
    return res.data || null;
  },

  fetchExecutions: async (workflowId?: string) => {
    const path = workflowId ? `/executions?workflow_id=${workflowId}` : "/executions";
    const res = await api.get<Execution[]>(path);
    set({ executions: res.data || [] });
  },
}));
