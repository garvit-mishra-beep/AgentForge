# Pillar 2: Frontend Audit Report

This report documents the findings from a deep technical audit of the AgentForge Next.js frontend (`apps/web/`).

---

## Summary Table

| Severity | Count | Status |
|----------|-------|--------|
| **P0 (Critical)** | 1 | ❌ Action Required |
| **P1 (High)** | 1 | ❌ Action Required |
| **P2 (Medium)** | 2 | ⚠️ Remediation Recommended |
| **P3 (Low)** | 4 | ℹ️ Minor Polish |
| **TOTAL** | 8 | ❌ **NOT READY** |

---

## 2.1 TypeScript & Code Quality

### Code Quality: ESLint Missing Dependency Warnings
- **File**: Multiple Files
  - [apps/web/app/executions/\[id\]/page.tsx:256](file:///c:/Users/garvi/AgentForge/apps/web/app/executions/%5Bid%5D/page.tsx#L256)
  - [apps/web/app/projects/\[id\]/page.tsx:43](file:///c:/Users/garvi/AgentForge/apps/web/app/projects/%5Bid%5D/page.tsx#L43)
  - [apps/web/app/tasks/\[id\]/page.tsx:194, 229](file:///c:/Users/garvi/AgentForge/apps/web/app/tasks/%5Bid%5D/page.tsx#L194)
  - [apps/web/app/tasks/page.tsx:188](file:///c:/Users/garvi/AgentForge/apps/web/app/tasks/page.tsx#L188)
  - [apps/web/app/teams/\[id\]/page.tsx:59](file:///c:/Users/garvi/AgentForge/apps/web/app/teams/%5Bid%5D/page.tsx#L59)
  - [apps/web/app/teams/page.tsx:43](file:///c:/Users/garvi/AgentForge/apps/web/app/teams/page.tsx#L43)
- **Severity**: P3 (Low)
- **Finding**: Hook functions (`useEffect`, `useCallback`) are missing the `load` dependencies in their dependency arrays.
- **Impact**: Code triggers 7 distinct ESLint `react-hooks/exhaustive-deps` warnings. Although page loads work, it creates linting noise and risks referencing stale closures if the function scopes update.
- **Fix**: Wrap `load()` functions in `useCallback` or include them in the dependency arrays.

---

## 2.2 Authentication Flow

### Security: LocalStorage Token Storage Vulnerable to XSS
- **File**: [apps/web/lib/api.ts](file:///c:/Users/garvi/AgentForge/apps/web/lib/api.ts#L5-L13) and [apps/web/components/auth/auth-context.tsx](file:///c:/Users/garvi/AgentForge/apps/web/components/auth/auth-context.tsx#L27-L32)
- **Severity**: P2 (Medium)
- **Finding**: Access and refresh tokens are stored in the browser's `localStorage` namespace.
- **Impact**: Sensitive tokens are vulnerable to Cross-Site Scripting (XSS) extraction. If a third-party script or dependency is compromised, an attacker can extract tokens silently.
- **Fix**: Transition token storage to secure, `httpOnly`, `sameSite=Strict` cookies.

---

### UX: Missing Dashboard Redirection for Logged-In Users
- **File**: [apps/web/components/sidebar-provider.tsx](file:///c:/Users/garvi/AgentForge/apps/web/components/sidebar-provider.tsx#L22-L27)
- **Severity**: P3 (Low)
- **Finding**: Authenticated users visiting `/login` or `/register` are not redirected to `/dashboard`.
- **Impact**: Logged-in users are allowed to see registration or login forms, degrading the user experience.
- **Fix**: Add a check in `useEffect` to redirect users to `/dashboard` if `token` is present when path is `/login` or `/register`.

---

## 2.3 Component Architecture

### Bundle Discipline: Static Import of ExecutionGraph
- **File**: [apps/web/app/executions/\[id\]/page.tsx](file:///c:/Users/garvi/AgentForge/apps/web/app/executions/%5Bid%5D/page.tsx#L10)
- **Severity**: P3 (Low)
- **Finding**: `ExecutionGraph` is loaded statically rather than using React lazy load / Next dynamic imports.
- **Impact**: Bypasses the bundle discipline directive: "HEAVY COMPONENTS -> always dynamic import". Increases initial page bundle loading size.
- **Fix**: Load `ExecutionGraph` dynamically:
  ```typescript
  const ExecutionGraph = dynamic(() => import("@/components/execution-graph").then((m) => m.ExecutionGraph), { ssr: false });
  ```

---

### Design: Spinners Used Instead of Skeleton UIs
- **File**: [apps/web/components/sidebar-provider.tsx:32](file:///c:/Users/garvi/AgentForge/apps/web/components/sidebar-provider.tsx#L32) and [apps/web/app/analytics/page.tsx:51](file:///c:/Users/garvi/AgentForge/apps/web/app/analytics/page.tsx#L51)
- **Severity**: P3 (Low)
- **Finding**: Spinner elements (`animate-spin`) are displayed during loading sequences.
- **Impact**: Bypasses the checklist guidelines: "Loading state -> skeleton UI (no spinners)". Renders standard, raw spinners instead of layout skeletons.
- **Fix**: Replace loading spinners with pure `<Skeleton />` primitive screens.

---

## 2.4 WebSocket Integration

### Connection: Hardcoded Localhost WebSocket Connection
- **File**: [apps/web/app/tasks/\[id\]/page.tsx](file:///c:/Users/garvi/AgentForge/apps/web/app/tasks/%5Bid%5D/page.tsx#L188)
- **Severity**: P0 (Critical)
- **Finding**: The WebSocket endpoint is hardcoded to `ws://localhost:8000/...`.
- **Impact**: In staging and production environments, the browser attempts to establish connection with the client's local machine, causing connection errors and breaking real-time status flows.
- **Proof**:
  ```typescript
  const wsUrl = `ws://localhost:8000/api/v1/ws/tasks/${id}`;
  const { state: wsState } = useWebSocket(wsUrl, { ... });
  ```
- **Fix**: Dynamically resolve the protocol and host based on `process.env.NEXT_PUBLIC_API_URL` or `window.location`.

---

### Security: Missing Auth Token on WebSocket Handshake
- **File**: [apps/web/app/tasks/\[id\]/page.tsx](file:///c:/Users/garvi/AgentForge/apps/web/app/tasks/%5Bid%5D/page.tsx#L188) and [apps/web/lib/ws-client.ts](file:///c:/Users/garvi/AgentForge/apps/web/lib/ws-client.ts#L41-L47)
- **Severity**: P1 (High)
- **Finding**: WebSocket initialization fails to pass the authentication JWT token.
- **Impact**: If auth is enabled, the backend will reject unauthenticated connections, preventing task message streams from displaying.
- **Fix**: Append the JWT token as a query parameter (e.g. `?token=...`) or negotiate it through WebSocket subprotocols.

---

### Code Quality: Infinite Reconnection Re-renders in Hook
- **File**: [apps/web/lib/ws-client.ts](file:///c:/Users/garvi/AgentForge/apps/web/lib/ws-client.ts#L145)
- **Severity**: P2 (Medium)
- **Finding**: ESLint flags that `options` is missing from the dependency array in `useWebSocket`.
- **Impact**: If `options` is added directly, a new object inline in components (e.g. `useWebSocket(url, { onMessage })`) will trigger hook cleanup and reconnection on every single render, causing constant reconnect spam.
- **Proof**:
  ```typescript
  export function useWebSocket(url: string, options: WSOptions = {}) {
    ...
    useEffect(() => {
      const client = new WSClient(url, (msg) => {
        options.onMessage?.(msg); // options is missing from dep array
      });
      ...
    }, [url]); // react-hooks/exhaustive-deps warning
  ```
- **Fix**: Save `options` in a React `useRef` container inside `useWebSocket` to isolate effect runs from object re-instantiations.
