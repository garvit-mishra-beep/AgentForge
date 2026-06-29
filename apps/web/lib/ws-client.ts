import { useEffect, useState, useCallback, useRef } from "react";

interface WSMessage<T = unknown> {
  type: string;
  payload: T;
}

interface WSOptions {
  onConnect?: () => void;
  onDisconnect?: (error?: unknown) => void;
  onMessage?: <T>(message: WSMessage<T>) => void;
  onError?: (error: unknown) => void;
}

export type WSConnectionState = "connecting" | "connected" | "reconnecting" | "disconnected" | "error";

const INITIAL_BACKOFF = 1000;
const MAX_BACKOFF = 30000;
const BACKOFF_MULTIPLIER = 2;
const HEARTBEAT_INTERVAL = 30000;

class WSClient {
  private url: string;
  private onEvent: (e: WSMessage) => void;
  private ws: WebSocket | null = null;
  private backoff = INITIAL_BACKOFF;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private isManualDisconnect = false;
  private _state: WSConnectionState = "disconnected";

  constructor(url: string, onEvent: (e: WSMessage) => void) {
    this.url = url;
    this.onEvent = onEvent;
  }

  get state(): WSConnectionState {
    return this._state;
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) return;

    this.isManualDisconnect = false;
    this._state = "connecting";
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this._state = "connected";
      this.backoff = INITIAL_BACKOFF;
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.onEvent(data);
      } catch {
        // Ignore malformed messages
      }
    };

    this.ws.onclose = () => {
      this._state = "disconnected";
      this.stopHeartbeat();
      if (!this.isManualDisconnect) {
        this._state = "reconnecting";
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = () => {
      this._state = "error";
    };
  }

  disconnect() {
    this.isManualDisconnect = true;
    this.stopHeartbeat();
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this._state = "disconnected";
  }

  send(msg: unknown): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
    }
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, this.backoff);
    this.backoff = Math.min(this.backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF);
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "ping" }));
      }
    }, HEARTBEAT_INTERVAL);
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer !== null) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }
}

export function useWebSocket(url: string, options: WSOptions = {}) {
  const [state, setState] = useState<WSConnectionState>("disconnected");
  const clientRef = useRef<WSClient | null>(null);
  const optionsRef = useRef(options);

  useEffect(() => {
    optionsRef.current = options;
  });

  useEffect(() => {
    const client = new WSClient(url, (msg) => {
      optionsRef.current.onMessage?.(msg);
    });
    clientRef.current = client;

    const interval = setInterval(() => {
      setState(client.state);
    }, 200);

    client.connect();

    return () => {
      clearInterval(interval);
      client.disconnect();
      clientRef.current = null;
    };
  }, [url]);

  const send = useCallback((msg: unknown) => {
    clientRef.current?.send(msg);
  }, []);

  return { state, send };
}

export default WSClient;
