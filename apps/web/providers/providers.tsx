"use client";

import type { ReactNode } from "react";
import { AuthProvider } from "@/components/auth/auth-context";
import { SidebarProvider } from "@/providers/sidebar-provider";
import { ToastProvider } from "@/components/ui/toast";
import { ErrorBoundary } from "@/components/layout/error-boundary";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <AuthProvider>
          <SidebarProvider>{children}</SidebarProvider>
        </AuthProvider>
      </ToastProvider>
    </ErrorBoundary>
  );
}
