# Pillar 2: Frontend Remediation Plan

This remediation plan lists the required fixes for the AgentForge frontend in order of severity (highest priority first).

---

## Remediation Tasks

### 1. Derive WebSocket URLs Dynamically
- **Finding ID**: Connection: Hardcoded Localhost WebSocket Connection
- **Severity**: P0 (Critical)
- **File**: [apps/web/app/tasks/\[id\]/page.tsx](file:///c:/Users/garvi/AgentForge/apps/web/app/tasks/%5Bid%5D/page.tsx#L188)
- **Remediation**:
  Calculate the WebSocket URL relative to the current API endpoint URL rather than hardcoding it:
  ```typescript
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
  const wsProto = apiBase.startsWith("https") ? "wss" : "ws";
  const wsHost = apiBase.replace(/^https?:\/\//, "");
  const wsUrl = `${wsProto}://${wsHost}/ws/tasks/${id}`;
  ```
- **Estimated Effort**: S (Small)
- **Dependencies**: None.

---

### 2. Propagate Access Token in WebSocket Handshake
- **Finding ID**: Security: Missing Auth Token on WebSocket Handshake
- **Severity**: P1 (High)
- **File**: [apps/web/app/tasks/\[id\]/page.tsx](file:///c:/Users/garvi/AgentForge/apps/web/app/tasks/%5Bid%5D/page.tsx#L188)
- **Remediation**:
  Extract the current token from `localStorage`/`cookies` and append it as a query parameter during WS client instantiation:
  ```typescript
  const token = getToken();
  const wsUrl = `${wsUrlBase}?token=${token}`;
  ```
- **Estimated Effort**: S (Small)
- **Dependencies**: Fix 1 (Derive WebSocket URLs).

---

### 3. Prevent Re-render Reconnect Loops in useWebSocket
- **Finding ID**: Code Quality: Infinite Reconnection Re-renders in Hook
- **Severity**: P2 (Medium)
- **File**: [apps/web/lib/ws-client.ts](file:///c:/Users/garvi/AgentForge/apps/web/lib/ws-client.ts#L124-L145)
- **Remediation**:
  Keep options object callbacks inside a stable mutable `useRef` reference:
  ```typescript
  export function useWebSocket(url: string, options: WSOptions = {}) {
    const [state, setState] = useState<WSConnectionState>("disconnected");
    const clientRef = useRef<WSClient | null>(null);
    const optionsRef = useRef(options);
    optionsRef.current = options;

    useEffect(() => {
      const client = new WSClient(url, (msg) => {
        optionsRef.current.onMessage?.(msg);
      });
      ...
    }, [url]);
  ```
- **Estimated Effort**: S (Small)
- **Dependencies**: None.

---

### 4. Move Auth Tokens to Secure Cookies
- **Finding ID**: Security: LocalStorage Token Storage Vulnerable to XSS
- **Severity**: P2 (Medium)
- **File**: [apps/web/lib/api.ts](file:///c:/Users/garvi/AgentForge/apps/web/lib/api.ts#L5-L13) and [apps/web/components/auth/auth-context.tsx](file:///c:/Users/garvi/AgentForge/apps/web/components/auth/auth-context.tsx#L27-L32)
- **Remediation**:
  Implement cookie storage using a library or raw document write methods:
  ```typescript
  // Set tokens as secure cookies instead of writing to localStorage
  document.cookie = `agentforge_token=${res.token}; Secure; SameSite=Strict; path=/;`;
  ```
- **Estimated Effort**: M (Medium)
- **Dependencies**: Requires backend cooperation (sending matching HTTP cookies or accepting cookie-based auth).

---

### 5. Wrap Route Functions in useCallback to Clean ESLint Warnings
- **Finding ID**: Code Quality: ESLint Missing Dependency Warnings
- **Severity**: P3 (Low)
- **File**: Multiple Files (Tasks, Teams, Projects Detail pages)
- **Remediation**:
  Wrap all `load()` page-fetching logic blocks in `useCallback` to stabilize references, and include them in the dependency arrays of `useEffect`.
- **Estimated Effort**: S (Small)
- **Dependencies**: None.

---

### 6. Dynamic Import for Heavy ExecutionGraph Component
- **Finding ID**: Bundle Discipline: Static Import of ExecutionGraph
- **Severity**: P3 (Low)
- **File**: [apps/web/app/executions/\[id\]/page.tsx:10](file:///c:/Users/garvi/AgentForge/apps/web/app/executions/%5Bid%5D/page.tsx#L10)
- **Remediation**:
  Change the static import to a dynamic import block:
  ```typescript
  import dynamic from "next/dynamic";
  const ExecutionGraph = dynamic(
    () => import("@/components/execution-graph").then((m) => m.ExecutionGraph),
    { ssr: false }
  );
  ```
- **Estimated Effort**: S (Small)
- **Dependencies**: None.

---

### 7. Render Skeleton Layout UIs in Place of Loading Spinners
- **Finding ID**: Design: Spinners Used Instead of Skeleton UIs
- **Severity**: P3 (Low)
- **File**: [apps/web/components/sidebar-provider.tsx](file:///c:/Users/garvi/AgentForge/apps/web/components/sidebar-provider.tsx#L32)
- **Remediation**:
  Create a `<SidebarSkeleton />` containing card-blocks of text outlines, and render it when loading the layout.
- **Estimated Effort**: S (Small)
- **Dependencies**: None.

---

### 8. Redirect Logged-In Users from Authentication Pages
- **Finding ID**: UX: Missing Dashboard Redirection
- **Severity**: P3 (Low)
- **File**: [apps/web/components/sidebar-provider.tsx](file:///c:/Users/garvi/AgentForge/apps/web/components/sidebar-provider.tsx#L22-L27)
- **Remediation**:
  Add an active redirect in the layouts or sidebar check:
  ```typescript
  useEffect(() => {
    if (loading) return;
    if (token && isPublic) {
      router.replace("/dashboard");
    }
  }, [token, loading, isPublic, router]);
  ```
- **Estimated Effort**: S (Small)
- **Dependencies**: None.
