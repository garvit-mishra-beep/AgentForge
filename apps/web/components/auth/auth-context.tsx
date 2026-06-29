"use client";
import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { useAnimation } from "framer-motion";
import { loginUser, registerUser, logoutUser, getMe } from "@/lib/api";

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
  const [user, setUser] = useState<{ id: string; email: string; name: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const shakeAnimation = useAnimation();

  // Backward compatible token state
  const token = user ? "session_active" : null;

  useEffect(() => {
    async function initAuth() {
      try {
        const u = await getMe();
        setUser(u);
        localStorage.setItem("agentforge_user", JSON.stringify(u));
      } catch {
        // Try refreshing cookies session
        const { refreshAccessToken } = await import("@/lib/api");
        const ok = await refreshAccessToken();
        if (ok) {
          try {
            const u = await getMe();
            setUser(u);
            localStorage.setItem("agentforge_user", JSON.stringify(u));
          } catch {
            setUser(null);
            localStorage.removeItem("agentforge_user");
          }
        } else {
          setUser(null);
          localStorage.removeItem("agentforge_user");
        }
      } finally {
        setLoading(false);
      }
    }
    initAuth();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    try {
      const res = await loginUser(email, password);
      localStorage.setItem(
        "agentforge_user",
        JSON.stringify({ id: res.user_id, email: res.email, name: res.name })
      );
      setUser({ id: res.user_id, email: res.email, name: res.name });
    } catch (err) {
      shakeAnimation.start({ x: [-10, 10, -10, 10, 0] }, {
        duration: 0.5
      });
      throw err;
    }
  }, [shakeAnimation]);

  const register = useCallback(async (name: string, email: string, password: string) => {
    try {
      const res = await registerUser(name, email, password);
      localStorage.setItem(
        "agentforge_user",
        JSON.stringify({ id: res.user_id, email: res.email, name: res.name })
      );
      setUser({ id: res.user_id, email: res.email, name: res.name });
    } catch (err) {
      shakeAnimation.start({ x: [-10, 10, -10, 10, 0] }, {
        duration: 0.5
      });
      throw err;
    }
  }, [shakeAnimation]);

  const logout = useCallback(async () => {
    try {
      await logoutUser();
    } catch (err) {
      console.error("Logout API call failed", err);
    } finally {
      localStorage.removeItem("agentforge_user");
      setUser(null);
    }
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
