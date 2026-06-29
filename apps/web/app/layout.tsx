import type { Metadata } from "next";
import type { ReactNode } from "react";
import "../styles/globals.css";
import { Providers } from "@/providers/providers";

export const metadata: Metadata = {
  title: "AgentForge â€” AI Team Operating System",
  description:
    "Create teams of AI specialists and watch them collaborate on real work. AgentForge orchestrates multiple AI agents that plan, build, review, and deliver together.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
