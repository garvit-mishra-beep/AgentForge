import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
// @ts-ignore - CSS files are handled by Next.js, not TypeScript
import './globals.css'
import { AppShell } from '@/components/layout/app-shell'

const geistSans = Geist({
  variable: '--font-sans',
  subsets: ['latin'],
})

const geistMono = Geist_Mono({
  variable: '--font-mono',
  subsets: ['latin'],
})

export const metadata: Metadata = {
  title: 'AgentOS - Multi-Agent Orchestration Platform',
  description: 'Production-grade async FastAPI backend for multi-agent orchestration',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <AppShell>{children as React.ReactNode}</AppShell>
      </body>
    </html>
  )
}
