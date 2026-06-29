"use client";

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { useAnimation } from "framer-motion";
import { loginUser, registerUser } from "@/lib/api";
import type { AuthResponse } from "@/lib/types";

interface AuthContextType {
  user: { id: string; email: string; name: string } | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  shakeAnimation: ReturnType<typeof useAnimation>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<{ id: string; email: string; name: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const shakeAnimation = useAnimation();

  useEffect(() => {
    const savedToken = localStorage.getItem("agentforge_token");
    const savedUser = localStorage.getItem("agentforge_user");
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    try {
      const res: AuthResponse = await loginUser(email, password);
      localStorage.setItem("agentforge_token", res.token);
      localStorage.setItem("agentforge_refresh", res.refresh_token);
      localStorage.setItem(
        "agentforge_user",
        JSON.stringify({ id: res.user_id, email: res.email, name: res.name })
      );
      setToken(res.token);
      setUser({ id: res.user_id, email: res.email, name: res.name });
    } catch (err) {
      // Trigger shake animation on failed login
      shakeAnimation.start({ x: [-10, 10, -10, 10, 0] }, {
        duration: 0.5,
        type: "spring"
      });
      throw err;
    }
  }, [shakeAnimation]);

  const register = useCallback(async (name: string, email: string, password: string) => {
    try {
      const res: AuthResponse = await registerUser(name, email, password);
      localStorage.setItem("agentforge_token", res.token);
      localStorage.setItem("agentforge_refresh", res.refresh_token);
      localStorage.setItem(
        "agentforge_user",
        JSON.stringify({ id: res.user_id, email: res.email, name: res.name })
      );
      setToken(res.token);
      setUser({ id: res.user_id, email: res.email, name: res.name });
    } catch (err) {
      // Trigger shake animation on failed registration
      shakeAnimation.start({ x: [-10, 10, -10, 10, 0] }, {
        duration: 0.5,
        type: "spring"
      });
      throw err;
    }
  }, [shakeAnimation]);

  const logout = useCallback(() => {
    localStorage.removeItem("agentforge_token");
    localStorage.removeItem("agentforge_refresh");
    localStorage.removeItem("agentforge_user");
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, shakeAnimation }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
