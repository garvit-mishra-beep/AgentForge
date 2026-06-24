/**
 * WebSocket Client for AgentOS
 *
 * Handles connection, reconnection, event listeners,
 * and workflow subscriptions.
 */

type WebSocketEvents = {
  workflow_created: { workflowId: string; name: string }
  workflow_completed: { workflowId: string; status: 'completed' }
  workflow_failed: { workflowId: string; error: string }
  workflow_cancelled: { workflowId: string }
  execution_started: { executionId: string; workflowId: string }
  execution_completed: { executionId: string; status: 'completed' }
  execution_failed: { executionId: string; error: string }
  execution_cancelled: { executionId: string }
  heartbeat: { timestamp: number }
}

interface WebSocketState {
  connected: boolean
  reconnecting: boolean
  reconnectAttempts: number
  lastEvent: string | null
}

export interface WebSocketOptions {
  url?: string
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onConnect?: (state: WebSocketState) => void
  onDisconnect?: (state: WebSocketState) => void
  onEvent?: <K extends keyof WebSocketEvents>(
    event: K,
    data: WebSocketEvents[K],
  ) => void
}

export type WebSocketEventsMap = {
  workflow_created: { workflowId: string; name: string }
  workflow_completed: { workflowId: string; status: 'completed' }
  workflow_failed: { workflowId: string; error: string }
  workflow_cancelled: { workflowId: string }
  execution_started: { executionId: string; workflowId: string }
  execution_completed: { executionId: string; status: 'completed' }
  execution_failed: { executionId: string; error: string }
  execution_cancelled: { executionId: string }
  heartbeat: { timestamp: number }
}

// WebSocket connection state
const state: WebSocketState = {
  connected: false,
  reconnecting: false,
  reconnectAttempts: 0,
  lastEvent: null,
}

// Current websocket instance
let wsInstance: WebSocket | null = null

// Store of event listeners for each event type
const eventListeners: Record<keyof WebSocketEventsMap, Array<(data: any) => void>> =
  {} as any

const eventKeys: Array<keyof WebSocketEventsMap> = [
  'workflow_created',
  'workflow_completed',
  'workflow_failed',
  'workflow_cancelled',
  'execution_started',
  'execution_completed',
  'execution_failed',
  'execution_cancelled',
  'heartbeat',
]

// Initialize event listeners registry
eventKeys.forEach((key) => {
  eventListeners[key] = []
})

/**
 * Initialize WebSocket connection
 */
export async function connect(options?: WebSocketOptions): Promise<void> {
  // Check if already connected
  if (state.connected) {
    return
  }

  // Determine WebSocket URL
  const wsUrl =
    options?.url ||
    (typeof window !== 'undefined'
      ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/api/ws/workflows`
      : 'ws://localhost:8000/api/ws/workflows')

  try {
    // Create WebSocket connection
    wsInstance = new WebSocket(wsUrl)

    // Handle connection open
    wsInstance.onopen = () => {
      state.connected = true
      state.reconnecting = false
      state.reconnectAttempts = 0
      state.lastEvent = 'connected'

      options?.onConnect?.(state)
      console.log('WebSocket connected')
    }

    // Handle messages
    wsInstance.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)

        // Handle different event types
        switch (data.type) {
          case 'heartbeat':
            state.lastEvent = 'heartbeat'
            break
          case 'workflow.created':
            state.lastEvent = 'workflow_created'
            options?.onEvent?.('workflow_created', data.payload)
            break
          case 'workflow.completed':
            state.lastEvent = 'workflow_completed'
            options?.onEvent?.('workflow_completed', data.payload)
            break
          case 'workflow.failed':
            state.lastEvent = 'workflow_failed'
            options?.onEvent?.('workflow_failed', data.payload)
            break
          case 'workflow.cancelled':
            state.lastEvent = 'workflow_cancelled'
            options?.onEvent?.('workflow_cancelled', data.payload)
            break
          case 'execution.started':
            state.lastEvent = 'execution_started'
            options?.onEvent?.('execution_started', data.payload)
            break
          case 'execution.completed':
            state.lastEvent = 'execution_completed'
            options?.onEvent?.('execution_completed', data.payload)
            break
          case 'execution.failed':
            state.lastEvent = 'execution_failed'
            options?.onEvent?.('execution_failed', data.payload)
            break
          case 'execution.cancelled':
            state.lastEvent = 'execution_cancelled'
            options?.onEvent?.('execution_cancelled', data.payload)
            break
        }
      } catch {
        // Ignore parsing errors
      }
    }

    // Handle connection close
    wsInstance.onclose = (event) => {
      state.connected = false

      // Auto-reconnect logic
      if (event.code === 1000 || event.code === 1012) {
        // Normal closure, don't reconnect
        options?.onDisconnect?.(state)
        return
      }

      // Attempt to reconnect
      if (
        !state.reconnecting &&
        options?.maxReconnectAttempts !== undefined &&
        state.reconnectAttempts < options.maxReconnectAttempts
      ) {
        state.reconnecting = true
        state.reconnectAttempts++

        // Exponential backoff
        const delay =
          Math.min(
            1000 * Math.pow(2, state.reconnectAttempts),
            options.reconnectInterval || 30000,
          )

        console.log(
          `WebSocket reconnection attempt ${state.reconnectAttempts} in ${delay}ms`,
        )

        setTimeout(() => {
          connect(options)
        }, delay)

        options?.onDisconnect?.(state)
      } else {
        options?.onDisconnect?.(state)
      }
    }

    // Handle errors
    wsInstance.onerror = () => {
      console.error('WebSocket error')
    }
  } catch (error) {
    console.error('Failed to create WebSocket connection:', error)
    options?.onDisconnect?.(state)
  }
}

/**
 * Disconnect WebSocket
 */
export async function disconnect(): Promise<void> {
  if ((state as any).heartbeatInterval) {
    clearInterval((state as any).heartbeatInterval)
    ;(state as any).heartbeatInterval = null
  }
  if (wsInstance) {
    wsInstance.close(1000, 'Client disconnect')
    wsInstance = null
    state.connected = false
  }
}

/**
 * Subscribe to workflow events
 */
export function subscribe<K extends keyof WebSocketEventsMap>(
  event: K,
  listener: (data: WebSocketEventsMap[K]) => void,
): () => void {
  const listeners = eventListeners[event]
  if (listeners) {
    listeners.push(listener)
  }

  return () => {
    const index = listeners.indexOf(listener)
    if (index > -1) {
      listeners.splice(index, 1)
    }
  }
}

/**
 * Unsubscribe all listeners
 */
export function unsubscribeAll(): void {
  Object.values(eventListeners).forEach((listeners) => {
    listeners.length = 0
  })
}

/**
 * Trigger event listeners
 */
function triggerEvent(event: keyof WebSocketEventsMap, data: any): void {
  const listeners = eventListeners[event]
  if (listeners) {
    listeners.forEach((listener) => {
      try {
        listener(data)
      } catch (error) {
        console.error(`Error in ${event} listener:`, error)
      }
    })
  }
}

/**
 * Simulate incoming event (for testing/development)
 */
export function simulateEvent<K extends keyof WebSocketEventsMap>(
  event: K,
  data: WebSocketEventsMap[K],
): void {
  triggerEvent(event, data)
}

/**
 * Get current WebSocket state
 */
export function getState(): WebSocketState {
  return { ...state }
}

/**
 * Initialize WebSocket with heartbeat
 */
export async function initializeWebSocket(options?: WebSocketOptions): Promise<void> {
  // Connect
  await connect(options)

  // Setup heartbeat (ping/pong simulation)
  const heartbeatInterval = setInterval(() => {
    // In production, this would send ping messages
    // For now, we'll simulate heartbeat events
    triggerEvent('heartbeat', { timestamp: Date.now() })
  }, 30000)

  // Store interval ID for cleanup
  ;(state as any).heartbeatInterval = heartbeatInterval

  // Heartbeat interval is automatically cleared inside disconnect()
}

/**
 * Cleanup function for use with useEffect cleanup
 */
export function cleanupWebSocket(): void {
  disconnect()
  unsubscribeAll()
}
