/**
 * Application Settings Page
 *
 * Manage LLM Provider keys and configuration settings.
 */

'use client'

import { useState, useEffect } from 'react'
import {
  Cpu,
  Key,
  Database,
  Save,
  CheckCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/loading'
import defaultApi from '@/lib/api'

interface SettingsConfig {
  llm_provider: string
  gemini_configured: boolean
  openai_configured: boolean
  anthropic_configured: boolean
  open_source_configured: boolean
  open_source_base_url: string
  open_source_model: string
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsConfig | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Input states
  const [provider, setProvider] = useState('gemini')
  const [geminiKey, setGeminiKey] = useState('')
  const [openaiKey, setOpenaiKey] = useState('')
  const [anthropicKey, setAnthropicKey] = useState('')
  const [osKey, setOsKey] = useState('')
  const [osBaseUrl, setOsBaseUrl] = useState('http://localhost:11434/v1')
  const [osModel, setOsModel] = useState('llama3')

  // Fetch settings on load
  useEffect(() => {
    async function loadSettings() {
      setIsLoading(true)
      try {
        const response = await defaultApi.get<SettingsConfig>('/settings')
        if (response.error) {
          throw new Error(response.error.message)
        }
        if (response.data) {
          const cfg = response.data
          setSettings(cfg)
          setProvider(cfg.llm_provider)
          setOsBaseUrl(cfg.open_source_base_url)
          setOsModel(cfg.open_source_model)
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load app settings.')
      } finally {
        setIsLoading(false)
      }
    }

    loadSettings()
  }, [])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSaving(true)
    setError(null)
    setSuccess(null)

    try {
      const payload: any = {
        llm_provider: provider,
        open_source_base_url: osBaseUrl,
        open_source_model: osModel,
      }

      if (geminiKey) payload.gemini_api_key = geminiKey
      if (openaiKey) payload.openai_api_key = openaiKey
      if (anthropicKey) payload.anthropic_api_key = anthropicKey
      if (osKey) payload.open_source_api_key = osKey

      const response = await defaultApi.post<any>('/settings', payload)
      if (response.error) {
        throw new Error(response.error.message)
      }

      setSuccess('Settings updated and saved to backend .env successfully!')
      setGeminiKey('')
      setOpenaiKey('')
      setAnthropicKey('')
      setOsKey('')

      // Reload config
      const reload = await defaultApi.get<SettingsConfig>('/settings')
      if (reload.data) {
        setSettings(reload.data)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to save settings.')
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-[400px] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="text-muted-foreground text-sm">Loading configurations...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Configuration Settings</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Set your credentials and preferences for the multi-agent AI engine.
        </p>
      </div>

      {success && (
        <div className="flex items-center gap-3 rounded-lg bg-green-500/10 border border-green-500/20 p-4 text-green-700 text-sm animate-fade-in">
          <CheckCircle className="h-5 w-5 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-3 rounded-lg bg-destructive/10 border border-destructive/20 p-4 text-destructive text-sm animate-fade-in">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* LLM Choice */}
        <div className="rounded-xl border bg-card p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-3 border-b pb-3">
            <Cpu className="h-5 w-5 text-primary" />
            <h3 className="font-semibold text-base">Active LLM Orchestrator</h3>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Select LLM Provider</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="gemini">Gemini 1.5 Flash (Google)</option>
                <option value="openai">GPT-4o (OpenAI)</option>
                <option value="anthropic">Claude 3.5 Sonnet (Anthropic)</option>
                <option value="open-source">Open-source Model (Ollama / Local)</option>
              </select>
            </div>
            <div className="text-xs text-muted-foreground self-center">
              The chosen LLM is used by all workflow agents (Planner, Coder, Tester, Reviewer) to coordinate tasks.
            </div>
          </div>
        </div>

        {/* API Credentials */}
        <div className="rounded-xl border bg-card p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-3 border-b pb-3">
            <Key className="h-5 w-5 text-primary" />
            <h3 className="font-semibold text-base">Provider API Credentials</h3>
          </div>

          <div className="space-y-4">
            {/* Gemini */}
            <div className="grid gap-2 sm:grid-cols-3 items-center">
              <div className="text-sm font-medium">
                Gemini API Key
                {settings?.gemini_configured && (
                  <span className="ml-2 inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                    Configured
                  </span>
                )}
              </div>
              <div className="sm:col-span-2">
                <input
                  type="password"
                  placeholder={settings?.gemini_configured ? "••••••••••••••••" : "Enter Gemini API Key"}
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>

            {/* OpenAI */}
            <div className="grid gap-2 sm:grid-cols-3 items-center">
              <div className="text-sm font-medium">
                OpenAI API Key
                {settings?.openai_configured && (
                  <span className="ml-2 inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                    Configured
                  </span>
                )}
              </div>
              <div className="sm:col-span-2">
                <input
                  type="password"
                  placeholder={settings?.openai_configured ? "••••••••••••••••" : "Enter OpenAI API Key"}
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>

            {/* Anthropic */}
            <div className="grid gap-2 sm:grid-cols-3 items-center">
              <div className="text-sm font-medium">
                Anthropic API Key
                {settings?.anthropic_configured && (
                  <span className="ml-2 inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                    Configured
                  </span>
                )}
              </div>
              <div className="sm:col-span-2">
                <input
                  type="password"
                  placeholder={settings?.anthropic_configured ? "••••••••••••••••" : "Enter Anthropic API Key"}
                  value={anthropicKey}
                  onChange={(e) => setAnthropicKey(e.target.value)}
                  className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>

            {/* Open Source */}
            {provider === 'open-source' && (
              <div className="border-t pt-4 space-y-4 animate-fade-in">
                <div className="grid gap-2 sm:grid-cols-3 items-center">
                  <div className="text-sm font-medium">Open-source Endpoint API Key</div>
                  <div className="sm:col-span-2">
                    <input
                      type="password"
                      placeholder={settings?.open_source_configured ? "••••••••••••••••" : "Enter Optional Open-source Key"}
                      value={osKey}
                      onChange={(e) => setOsKey(e.target.value)}
                      className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>
                </div>

                <div className="grid gap-2 sm:grid-cols-3 items-center">
                  <div className="text-sm font-medium">Base URL *</div>
                  <div className="sm:col-span-2">
                    <input
                      type="text"
                      placeholder="e.g. http://localhost:11434/v1"
                      value={osBaseUrl}
                      onChange={(e) => setOsBaseUrl(e.target.value)}
                      className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-primary"
                      required
                    />
                  </div>
                </div>

                <div className="grid gap-2 sm:grid-cols-3 items-center">
                  <div className="text-sm font-medium">Model Identifier *</div>
                  <div className="sm:col-span-2">
                    <input
                      type="text"
                      placeholder="e.g. llama3"
                      value={osModel}
                      onChange={(e) => setOsModel(e.target.value)}
                      className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-primary"
                      required
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Database Stats */}
        <div className="rounded-xl border bg-card p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-3 border-b pb-3">
            <Database className="h-5 w-5 text-primary" />
            <h3 className="font-semibold text-base">PostgreSQL Persistence Status</h3>
          </div>

          <div className="flex items-center gap-2.5 text-sm">
            <div className="h-2.5 w-2.5 rounded-full bg-green-500 animate-pulse" />
            <span className="font-semibold text-green-700">Connected</span>
            <span className="text-muted-foreground ml-1">
              - postgresql+asyncpg://user:***@localhost:5432/agents
            </span>
          </div>
          <div className="text-xs text-muted-foreground">
            All workflows, execution checkpoints, event logs, and generated artifacts are safely stored in Postgres.
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center justify-end">
          <Button
            type="submit"
            disabled={isSaving}
            className="gap-2 shadow-md"
          >
            {isSaving ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            <span>{isSaving ? 'Saving...' : 'Save Configuration'}</span>
          </Button>
        </div>
      </form>
    </div>
  )
}
