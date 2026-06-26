"use client";

import { usePathname } from "next/navigation";
import Sidebar from "@/components/sidebar";
import TopBar from "@/components/topbar";
import { CommandPalette } from "@/components/command-palette";

const LANDING_ROUTES = new Set(["/"]);

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLanding = LANDING_ROUTES.has(pathname);

  if (isLanding) {
    return <>{children}</>;
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
