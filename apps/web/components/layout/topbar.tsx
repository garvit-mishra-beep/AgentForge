'use client'

import { cn } from '@/lib/utils'
import { Bell, Wifi, WifiOff } from 'lucide-react'
import { Button } from '@/components/ui/loading'

interface TopbarProps {
  websocketConnected: boolean
  setWebsocketConnected: (connected: boolean) => void
}

export function Topbar({
  websocketConnected,
  setWebsocketConnected,
}: TopbarProps) {
  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-4">
      <div className="flex items-center gap-4">
        {/* App Title */}
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <span className="font-bold text-sm">AO</span>
          </div>
          <span className="hidden font-semibold text-foreground sm:inline">
            AgentOS Platform
          </span>
        </div>

        {/* Environment Badge */}
        <div
          className={cn(
            'hidden rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset',
            'ring-background/10 dark:ring-slate-700 dark:text-slate-100 sm:inline-flex',
          )}
        >
          <span className="inline-flex items-center gap-1">
            <span
              className={cn(
                'h-1.5 w-1.5 rounded-full',
                process.env.NODE_ENV === 'development'
                  ? 'bg-amber-500'
                  : 'bg-green-500',
              )}
            />
            {process.env.NODE_ENV === 'development'
              ? 'Development'
              : 'Production'}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Websocket Status */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => setWebsocketConnected(!websocketConnected)}
          className={cn(
            'gap-2 border-border dark:border-slate-700',
            websocketConnected ? 'text-green-600' : 'text-amber-600',
          )}
        >
          {websocketConnected ? (
            <>
              <Wifi className="h-4 w-4" />
              <span className="hidden sm:inline">Connected</span>
            </>
          ) : (
            <>
              <WifiOff className="h-4 w-4" />
              <span className="hidden sm:inline">Disconnected</span>
            </>
          )}
        </Button>

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          <span className="absolute right-1 top-1.5 h-2 w-2 rounded-full bg-destructive ring-2 ring-background" />
        </Button>

        {/* User Menu Placeholder */}
        <div className="ml-2 flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center">
            <span className="text-sm font-medium text-muted-foreground">
              U
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}
