'use client'

import { useTransition, useState } from 'react'
import { Sidebar } from './sidebar'
import { Topbar } from './topbar'
import { cn } from '@/lib/utils'

interface AppShellProps {
  children: React.ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const [isSidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [isWebsocketConnected, setWebsocketConnected] = useState(false)

  const [, startTransition] = useTransition()

  const handleSidebarToggle = (collapsed: boolean) => {
    startTransition(() => {
      setSidebarCollapsed(collapsed)
    })
  }

  const handleWebsocketToggle = (connected: boolean) => {
    startTransition(() => {
      setWebsocketConnected(connected)
    })
  }

  return (
    <div
      className={cn(
        'flex min-h-screen w-full bg-background',
        isSidebarCollapsed ? 'overflow-x-hidden' : '',
      )}
    >
      {/* Background pattern */}
      <div
        className="pointer-events-none fixed inset-0 z-0 flex items-center justify-center overflow-hidden"
        aria-hidden="true"
      >
        <div
          className="absolute -inset-[100%] opacity-[0.03] dark:opacity-[0.04]"
          style={{
            backgroundImage: 'url("data:image/svg+xml,%3Csvg width=64 height=64%3E%3Ccircle cx=32 cy=32 r=32 fill=%23000000%3E%3C/svg%3E")',
          }}
        />
      </div>

      {/* Sidebar */}
      <Sidebar
        collapsed={isSidebarCollapsed}
        setCollapsed={handleSidebarToggle}
      />

      {/* Main Content */}
      <div
        className={cn(
          'flex flex-1 flex-col overflow-hidden transition-all duration-300 ease-in-out',
          isSidebarCollapsed ? 'ml-16' : 'ml-64',
        )}
      >
        <Topbar
          websocketConnected={isWebsocketConnected}
          setWebsocketConnected={handleWebsocketToggle}
        />

        {/* Main Content Area */}
        <main className="flex-1 overflow-auto">
          <div
            className={cn(
              'min-h-screen p-4 transition-all duration-300',
              isSidebarCollapsed ? 'animate-fade-in' : '',
            )}
          >
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
