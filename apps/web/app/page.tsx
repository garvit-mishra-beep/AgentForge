'use client'

import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/loading'

export default function Home() {
  const [isConnected, setIsConnected] = useState(false)
  const [status, setStatus] = useState('Connecting...')

  useEffect(() => {
    // Simulate connection status (in production, use real WebSocket)
    const timer = setTimeout(() => {
      setIsConnected(true)
      setStatus('Connected')
    }, 1500)

    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-background via-background to-accent/20 flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center space-y-8 p-8 max-w-2xl"
      >
        <div className="space-y-4">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-primary/10 border border-primary/20 mb-4">
            <span className="text-4xl font-bold bg-gradient-to-br from-primary to-secondary bg-clip-text text-transparent">
              AO
            </span>
          </div>

          <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
            AgentOS
          </h1>

          <p className="text-muted-foreground text-lg max-w-md mx-auto">
            Multi-agent orchestration platform for autonomous software engineering workflows
          </p>
        </div>

        <div className="flex items-center justify-center gap-4">
          <Link href="/workflows">
            <Button
              variant="default"
              size="lg"
            >
              Start Working
            </Button>
          </Link>

          <Button
            variant="outline"
            size="lg"
            onClick={() => {
              setIsConnected(false)
              setStatus('Connecting...')
            }}
          >
            Disconnect
          </Button>
        </div>

        <div className="flex items-center justify-center gap-3 text-sm text-muted-foreground">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected
                ? 'bg-green-500 animate-pulse'
                : 'bg-amber-500 animate-pulse'
            }`}
          />
          <span>{status}</span>
        </div>
      </motion.div>
    </div>
  )
}
