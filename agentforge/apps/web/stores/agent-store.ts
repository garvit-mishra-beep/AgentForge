import { create } from "zustand";
import type { Agent } from "@/types";
import { api } from "@/lib/api";

interface AgentState {
  agents: Agent[];
  selectedAgent: Agent | null;
  isLoading: boolean;
  error: string | null;
  fetchAgents: () => Promise<void>;
  fetchAgent: (id: string) => Promise<void>;
  createAgent: (data: Partial<Agent>) => Promise<Agent | null>;
  deleteAgent: (id: string) => Promise<void>;
}

export const useAgentStore = create<AgentState>((set, get) => ({
  agents: [],
  selectedAgent: null,
  isLoading: false,
  error: null,

  fetchAgents: async () => {
    set({ isLoading: true, error: null });
    const res = await api.get<Agent[]>("/agents");
    if (res.error) {
      set({ error: res.error.message, isLoading: false });
    } else {
      set({ agents: res.data || [], isLoading: false });
    }
  },

  fetchAgent: async (id: string) => {
    set({ isLoading: true, error: null });
    const res = await api.get<Agent>(`/agents/${id}`);
    if (res.error) {
      set({ error: res.error.message, isLoading: false });
    } else {
      set({ selectedAgent: res.data || null, isLoading: false });
    }
  },

  createAgent: async (data: Partial<Agent>) => {
    const res = await api.post<Agent>("/agents", data);
    if (res.error) {
      set({ error: res.error.message });
      return null;
    }
    if (res.data) {
      set((state) => ({ agents: [res.data!, ...state.agents] }));
      return res.data;
    }
    return null;
  },

  deleteAgent: async (id: string) => {
    const res = await api.delete(`/agents/${id}`);
    if (!res.error) {
      set((state) => ({ agents: state.agents.filter((a) => a.id !== id) }));
    }
  },
}));
