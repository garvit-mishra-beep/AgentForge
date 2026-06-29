# Frontend Audit Report

**Product:** AgentForge Web Dashboard  
**Auditor:** Senior Engineering Auditor  
**Scope:** `apps/web/` (Next.js 15, React 19, Tailwind v4)  
**Date:** June 29, 2026  

---

## 1. Summary of Findings

| Severity | Count | Status |
|:---|:---|:---|
| **P0 (Critical)** | 3 | ❌ Action Required |
| **P1 (High)** | 1 | ❌ Action Required |
| **P2 (Medium)** | 2 | ⚠️ Technical Debt |
| **P3 (Low)** | 1 | ⚠️ Technical Debt |

---

## 2. Findings Detail

### Projects Detail Page Route Displacement
- **Location**: `apps/web/app/projects/[id]/page.tsx` · Lines 1–119
- **Severity**: P0 (Critical)
- **Finding**: The file `projects/[id]/page.tsx` exports the `LoginPage` component and renders the sign-in form instead of project details.
- **Impact**: Clicking a project on the projects dashboard directs the user to a login screen, completely blocking users from viewing or managing project details/files.
- **Proof**:
  ```typescript
  export default function LoginPage() {
    const router = useRouter();
    const { login, shakeAnimation } = useAuth();
    ...
  ```
- **Fix**: Re-implement `projects/[id]/page.tsx` using `listProjectFiles()` and `getProject()` to fetch and show real project data.

---

### Tasks Detail Page Route Displacement
- **Location**: `apps/web/app/tasks/[id]/page.tsx` · Lines 1–167
- **Severity**: P0 (Critical)
- **Finding**: The file `tasks/[id]/page.tsx` exports the `SettingsPage` component and renders the global settings UI layout instead of the task details stream view.
- **Impact**: Clicking on a task detail link redirects the user to the global settings panel, completely preventing users from viewing the live streaming logs or final code delivery of that task.
- **Proof**:
  ```typescript
  export default function SettingsPage() {
    const [keys, setKeys] = useState<ApiKey[]>([]);
    ...
  ```
- **Fix**: Re-implement `tasks/[id]/page.tsx` to query and display real task executions, live step status, and messages.

---

### Teams Detail Page Route Displacement
- **Location**: `apps/web/app/teams/[id]/page.tsx` · Lines 1–304
- **Severity**: P0 (Critical)
- **Finding**: The file `teams/[id]/page.tsx` exports the `TasksPage` component and renders the list of tasks instead of showing team configurations.
- **Impact**: Users cannot view or edit team members, models, or instructions for individual teams.
- **Proof**:
  ```typescript
  export default function TasksPage() {
    return (
      <Suspense fallback={...}>
        <TasksPageInner />
      </Suspense>
    );
  }
  ```
- **Fix**: Re-implement `teams/[id]/page.tsx` to handle team detail queries, model selection settings, and role configurations.

---

### Executions Detail Page Mock Simulation Only
- **Location**: `apps/web/app/executions/[id]/page.tsx` · Lines 1–476
- **Severity**: P1 (High)
- **Finding**: The execution detail page (`/executions/[id]`) renders static simulation flows from `lib/demo-data.ts` using a mock interface rather than fetching real task logs and messages from the API.
- **Impact**: The dashboard fails to show real executions, making it impossible to audit past tasks or monitor active agent executions.
- **Proof**:
  ```typescript
  import { DEMO_SCENARIOS, type DemoScenario } from "@/lib/demo-data";
  // Lack of fetch or WebSocket hooks connecting to the actual API backend
  ```
- **Fix**: Refactor `/executions/[id]/page.tsx` to fetch execution data from the API gateway using `getTaskMessages()` and map real state events to the execution UI.

---

### Missing React Hook dependencies causing Stale Closures
- **Location**: `apps/web/lib/ws-client.ts` · Line 145 and `apps/web/app/tasks/page.tsx` · Line 188
- **Severity**: P2 (Medium)
- **Finding**: React `useEffect` hooks lack required variables (like `options` or `load`) in their dependency arrays.
- **Impact**: Stale callbacks are retained when state values change, leading to silent event listener failures, UI updates using outdated closure state, or missing data refreshes.
- **Proof**:
  ```typescript
  useEffect(() => {
    const client = new WSClient(url, (msg) => { options.onMessage?.(msg); });
    ...
  }, [url]); // warning: options is missing
  ```
- **Fix**: Include the missing dependencies in the arrays or wrap hook callbacks using `useCallback` / `useRef` to maintain clean references.

---

### localstorage Token storage vulnerable to XSS
- **Location**: `apps/web/components/auth/auth-context.tsx` · Lines 39–45
- **Severity**: P2 (Medium)
- **Finding**: Both JWT access and refresh tokens are stored in `localStorage`.
- **Impact**: If any XSS exploit is found in the dashboard, the attacker can silently steal the access and refresh tokens, gaining complete API access.
- **Proof**: `localStorage.setItem("agentforge_token", res.token);`
- **Fix**: Move token storage to HttpOnly, Secure, SameSite cookies.

---

### Lack of Multi-Tab Auth state synchronization
- **Location**: `apps/web/components/auth/auth-context.tsx` · Lines 78–84
- **Severity**: P3 (Low)
- **Finding**: Logouts do not notify other open browser tabs.
- **Impact**: If a user logs out in Tab A, Tab B remains active with expired token state on the screen, leading to unexpected API failures.
- **Fix**: Use a `BroadcastChannel` or storage event listener to automatically sync auth logouts across tabs.
