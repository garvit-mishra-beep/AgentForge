"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/layout/sidebar";
import TopBar from "@/components/layout/topbar";
import { CommandPalette } from "@/components/layout/command-palette";
import { useAuth } from "@/components/auth/auth-context";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { token, loading } = useAuth();

  useEffect(() => {
    if (!loading && !token) {
      router.replace("/login");
    }
  }, [token, loading, router]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!token) {
    return null;
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <CommandPalette />
      <Sidebar />
      <div className="flex flex-1 flex-col min-w-0">
        <TopBar />
        <main className="flex-1 overflow-y-auto pt-12 sm:pt-0">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 py-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
