# ⚡ AgentForge
## Full Frontend Build Prompt
`Version 2.0` · `Status: Production-Ready` · `Rating: 10/10`

> Build the frontend for **AgentForge** — a multi-agent AI orchestration platform
> where specialized agents (Team Lead, Builder, Reviewer, Tester, Security, DevOps)
> collaborate on real engineering tasks through a LangGraph-powered state graph.
> This is not a demo. Build it like a product.

---

```
┌─────────────────────────────────────────────────────────────────┐
│                      EXECUTION ORDER                            │
│                                                                 │
│   PHASE 0          PHASE 1          PHASE 2          PHASE 3   │
│   Backend    →     Foundation  →    Core App   →    Power      │
│   Audit            & Shell          Pages           Features    │
│                                                                 │
│                         PHASE 4                                 │
│                    Polish + Marketing                           │
└─────────────────────────────────────────────────────────────────┘
```

---

# 🔒 GROUND RULES
### These apply to every phase, every file, every line.

### 📁 Repository Boundaries

```diff
+ WRITE ACCESS          | apps/web/  ·  docs/frontend/  ·  types/
- READ ONLY (audit)     | apps/api/  ·  agents/  ·  core/  ·  tests/  ·  migrations/
```

> Need a backend change? → Log it in `BACKEND_GAPS.md`. Do not touch it.

---

### 🔍 Evidence Standard

Before claiming any route, schema, or event **exists** — cite your source:

```
✅ Confirmed:
   File:   apps/api/app/routes/tasks.py
   Lines:  45–92
   Route:  POST /api/v1/tasks
   Schema: TaskCreateRequest → models/schemas.py:112–128

❌ Not allowed:
   "The /api/v1/tasks endpoint probably accepts..."
   "I'll assume the schema looks like..."
```

If you can't cite a file + line range → **it doesn't exist for frontend purposes.**
Log it in `BACKEND_GAPS.md` and use a typed stub marked `// BLOCKED`.

---

### 🚦 Phase Completion Gate

A phase is **COMPLETE** only when every box is checked with real output:

```
  ☐  npx tsc --noEmit          →  0 errors
  ☐  npx eslint . --ext .ts,.tsx →  0 errors
  ☐  npx next build             →  successful
  ☐  All files physically exist  →  not just planned
  ☐  FRONTEND_PROGRESS.md       →  updated with evidence

  If any check cannot run → Status = BLOCKED
  Never mark COMPLETE based on assumption.
```

---

### 🧩 Component State Law

Every data-fetching component must handle **all five states**. No exceptions.

```typescript
type AsyncState<T> =
  | { status: "loading"                              }  // → <Skeleton />
  | { status: "empty"                                }  // → <EmptyState /> with CTA
  | { status: "error";  message: string; retry: fn  }  // → error card + retry button
  | { status: "unauthorized"                         }  // → redirect /login
  | { status: "success"; data: T                     }  // → real content

// WebSocket components additionally track:
type WSState = "connecting" | "connected" | "reconnecting" | "disconnected" | "error"
//                                           ↑ show banner     ↑ show banner
```

```
Never render from undefined | null.
Always guard:  if (!data) return <Skeleton />
```

---

### 📦 Bundle Discipline

```
  DEFAULT:  React Server Component (no "use client")
  EXCEPTION: only if component needs useState / useEffect / browser APIs / WebSocket

  HEAVY COMPONENTS → always dynamic import:
  ┌──────────────────────────────────────────────────────────────────┐
  │  const AgentNetwork   = dynamic(() => import("…/agent-network"), │
  │                                         { ssr: false })          │
  │  const ExecutionGraph = dynamic(() => import("…/exec-graph"),    │
  │                                         { ssr: false })          │
  └──────────────────────────────────────────────────────────────────┘

  RULES:
  - No new npm packages without a justification comment
  - No duplicate utilities → consolidate in lib/utils.ts
  - No unused imports → ESLint import/no-unused-vars must pass
  - No barrel re-exports that blow up bundle size
```

---

### 🎨 Design Consistency Gate

Before closing any phase, update `DESIGN_REVIEW.md`:

```markdown
## /dashboard
Typography  : ✅ Inter only, no rogue fonts
Spacing     : ✅ 4px base unit throughout
Reuse       : ✅ StatCard, DataTable from ui/
A11y        : ⚠️  StatCard missing aria-label → fix before merge
Responsive  : ✅ collapses to single column at 768px
New patterns: none introduced
```

> No page may introduce a new design pattern without a justification entry here.

---

### 🏁 Production Completeness Checklist

No page ships without:

```
  ☐  Loading state     →  skeleton UI (no spinners)
  ☐  Empty state       →  <EmptyState /> with actionable CTA
  ☐  Error state       →  error card + retry button
  ☐  Unauthorized      →  redirect to /login
  ☐  Mobile layout     →  works at 320px minimum
  ☐  Keyboard nav      →  all interactions reachable via Tab + Enter
  ☐  WS disconnect     →  top banner: "Connection lost — data may be stale"
```

---

# 🛠️ STACK & DESIGN SYSTEM

### Tech Stack

| Layer | Choice |
|-------|--------|
| Framework | Next.js 15 (App Router) |
| UI Library | React 19 + TypeScript strict |
| Styling | Tailwind v4 — utility classes only |
| Primitives | Radix UI (Dialog, Tooltip, DropdownMenu, Select, Tabs, Popover) |
| Animation | Framer Motion (transitions, entrances, pipeline pulses) |
| Icons | Lucide React |
| Charts | Recharts (analytics only, dynamic import) |
| Banned | shadcn · MUI · Chakra · Bootstrap · any component kit |

### Design System

```css
/* globals.css — single source of truth */
:root {
  /* Surfaces */
  --bg:           #0a0a0a;   /* page background    */
  --surface-1:    #111111;   /* cards, sidebar      */
  --surface-2:    #1a1a1a;   /* inputs, hover       */
  --border:       #222222;   /* default border      */
  --border-faint: #181818;   /* subtle dividers     */

  /* Brand */
  --accent:       #6366f1;   /* indigo — primary    */
  --accent-hi:    #818cf8;   /* indigo — hover      */
  --violet:       #8b5cf6;   /* secondary accent    */

  /* Semantic */
  --live:         #22c55e;   /* active / success    */
  --warn:         #f59e0b;   /* warning             */
  --error:        #ef4444;   /* error / danger      */

  /* Text */
  --text-1:       #f0f0f0;   /* primary             */
  --text-2:       #a0a0a0;   /* secondary / muted   */
  --text-3:       #555555;   /* placeholder         */
  --code-bg:      #0d1117;   /* code surfaces       */

  /* Typography */
  --font-sans:    'Inter', sans-serif;
  --font-mono:    'JetBrains Mono', 'Fira Code', monospace;
}
```

> **Aesthetic target:** Vercel × Raycast × Linear
> Developer-native. Handcrafted. Not a template. Not AI-generic.

### Agent Role Color Map

```typescript
export const ROLE_COLORS: Record<AgentRole, string> = {
  team_lead:  "#6366f1",  // indigo
  builder:    "#3b82f6",  // blue
  reviewer:   "#f59e0b",  // amber
  tester:     "#10b981",  // emerald
  security:   "#ef4444",  // red
  devops:     "#8b5cf6",  // violet
  aggregator: "#06b6d4",  // cyan
}
```

---

# 🔎 PHASE 0 — BACKEND AUDIT
### `MANDATORY` · No frontend code until this phase is signed off.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Do NOT write a single React component until all 5 deliverables     │
│  in this phase are generated and non-empty.                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Audit Steps

```
1. Every route in        apps/api/app/routes/          → cite file + lines
2. All schemas in        apps/api/models/schemas.py    → cite file + lines
3. WebSocket contracts   apps/api/app/ws/              → cite file + lines
4. Auth flow             JWT mint · refresh rotation · middleware order
5. BYOK endpoints        apps/api/app/routes/keys.py   → encryption + masking
```

### Deliverable 1 — `ROUTE_DISCOVERY_REPORT.md`

```markdown
| Method | Path | Auth | Request Schema | Response Schema | File | Lines |
|--------|------|------|----------------|-----------------|------|-------|
| POST | /api/v1/tasks | ✅ | TaskCreateRequest | TaskResponse | routes/tasks.py | 45–92 |
```

### Deliverable 2 — `API_SCHEMA_MAP.md`

```markdown
## TaskCreateRequest
File: models/schemas.py · Lines 112–128
Fields:
  - team_id:         UUID    (required)
  - project_id:      UUID    (optional)
  - title:           str     (required, max 200)
  - description:     str     (required)
  - fast_demo_mode:  bool    (default: false)
```

### Deliverable 3 — `WEBSOCKET_EVENT_MAP.md`

```markdown
## agent_message
File:      app/ws/task_stream.py · Lines 34–51
Direction: server → client
Payload:   { content: str, role: AgentRole, model: str, chunk_index: int }
Pages:     /tasks/[id]  ·  /executions/[id]
```

### Deliverable 4 — `BACKEND_UI_COMPATIBILITY_REPORT.md`

```markdown
| Page | Required Routes | All Exist? | Gaps |
|------|----------------|------------|------|
| /tasks/[id] | GET /tasks/{id}, WS task_stream | ⚠️ Partial | WS auth unclear |
```

### Deliverable 5 — `ARCHITECTURE_RISKS.md`

```markdown
## 🔴 P0 — Critical
- [ ] WebSocket auth: token passed as query param or header? Confirm before building.
- [ ] Parallel 401s may trigger double refresh → race condition

## 🟠 P1 — High
- [ ] pgvector queries not paginated → analytics page may time out at scale
- [ ] No optimistic rollback on task creation failure defined

## 🟡 P2 — Medium
- [ ] /executions/[id] graph canvas: no mobile layout defined
- [ ] Command palette: focus trap not specified → keyboard leak risk

## 🔵 P3 — Low
- [ ] StatCard animations may cause CLS on slow connections
```

### `BACKEND_GAPS.md` — Start empty, fill continuously

```markdown
## GAP: [METHOD /path]
| Field | Value |
|-------|-------|
| Missing route      | e.g. POST /api/v1/tasks/{id}/revise |
| Required schema    | { verdict: "approved" \| "rejected", comment?: string } |
| UI blocked         | Human-in-the-loop approval in /tasks/[id] |
| Recommended impl   | Add to apps/api/app/routes/executions.py |
| Priority           | P0 |
```

---

# 🏗️ PHASE 1 — FOUNDATION
### Design system · Shell · Auth · UI primitives

```
Goal: A working skeleton every page will live inside.
      No real data yet. Just the bones — built right.
```

### File Tree

```
types/
  api.ts              ← from API_SCHEMA_MAP.md
  ws.ts               ← from WEBSOCKET_EVENT_MAP.md
  agents.ts

lib/
  api.ts              ← typed fetch wrapper
  ws-client.ts        ← WebSocket + auto-reconnect
  auth.ts             ← token helpers
  utils.ts

app/
  globals.css         ← design tokens, resets, scrollbar
  layout.tsx          ← root, fonts, auth context
  (auth)/
    login/page.tsx
    register/page.tsx
  (app)/
    layout.tsx        ← Sidebar + Topbar shell

components/
  layout/
    sidebar.tsx
    topbar.tsx
    command-palette.tsx     ← Cmd+K global search
  ui/
    badge.tsx · button.tsx · card.tsx · code-block.tsx
    data-table.tsx · dialog.tsx · empty-state.tsx · input.tsx
    kbd.tsx · live-dot.tsx · skeleton.tsx · stat-card.tsx · tooltip.tsx
```

### `lib/api.ts` — Contract

```typescript
// Auto-attaches:  Authorization: Bearer <access_token>
//                 X-Request-ID:  crypto.randomUUID()
// On 401:         calls POST /api/v1/auth/refresh once → retry → redirect /login

export const api = {
  get<T>  (path: string             ): Promise<T>,
  post<T> (path: string, body: unknown): Promise<T>,
  put<T>  (path: string, body: unknown): Promise<T>,
  del     (path: string             ): Promise<void>,
}
```

### `lib/ws-client.ts` — Contract

```typescript
class WSClient {
  constructor(url: string, onEvent: (e: WSEvent) => void)
  connect():    void   // exponential backoff: 1s → 2s → 4s → 8s → max 30s
  disconnect(): void
  send(msg: unknown): void
  get state(): WSConnectionState
}
```

### Sidebar Navigation

```
  ⬡ AgentForge
  ───────────────────────
  ⬜  Dashboard
  ⬜  Teams
  ⬜  Tasks
  ⬜  Executions    [● 3]
  ⬜  Projects
  ───────────────────────
  ⬜  Analytics
  ⬜  Quick Review
  ⬜  Benchmark
  ⬜  Templates
  ───────────────────────
  ⬜  Settings
  ── ● Garvit Mishra ───
```

- 240px fixed · collapses to 60px icon rail · toggle in localStorage
- Active: `--accent` left border + `--surface-2` bg
- Mobile < 768px: bottom navigation bar, 5 primary items

### Auth Pages

- Centered card · subtle CSS grid pattern on `--bg`
- Login: Email + Password
- Register: Full Name + Email + Password
- Failed auth: Framer Motion shake animation
- Success: store `{ access, refresh }` → localStorage → redirect `/dashboard`
- Auth guard in `(app)/layout.tsx`: no token → redirect `/login`

### ✅ Phase 1 Gate

```
  ☐  tsc --noEmit        →  0 errors
  ☐  eslint              →  0 errors
  ☐  next build          →  success
  ☐  Shell renders at /dashboard (empty, no data)
  ☐  /login + /register  →  render + submit
  ☐  FRONTEND_PROGRESS.md updated
  ☐  DESIGN_REVIEW.md created
```

---

# 🖥️ PHASE 2 — CORE APP
### Dashboard · Teams · Tasks — the pages users live in.

```
Goal: Real data. Real WebSockets. Real collaboration UI.
      If it doesn't work end-to-end, it's not done.
```

### `/dashboard`

**Confirmed routes (cite from Phase 0):**
- `GET /api/v1/tasks?limit=10&sort=created_at`
- `GET /api/v1/executions?status=running`

**Layout — 2 column (2/3 · 1/3):**

```
┌─────────────────────────────┬──────────────────┐
│  [stat] [stat] [stat] [stat]│  Your Teams      │
│                              │  ─────────────── │
│  Recent Tasks ──────────────│  Quick Review ⚡  │
│  title · team · status · age│                  │
│  ──────────────────────────│                  │
│  Active Executions (live)   │                  │
│  polls every 3s             │                  │
└─────────────────────────────┴──────────────────┘
```

### `/teams` + `/teams/[id]`

**List:** card grid — name · member count · task count · Open / Delete

**Detail (`/teams/[id]`):**

```
Role         Model                   Status
──────────────────────────────────────────────
Team Lead    [ Gemini 1.5 Pro    ▾]  ● Active
Builder      [ Claude Sonnet     ▾]  ● Active
Reviewer     [ GPT-4o            ▾]  ● Active
Tester       [ Qwen-72B          ▾]  ● Active
Security     [ GPT-4o            ▾]  ● Active
DevOps       [ Claude Haiku      ▾]  ○ Idle
                                    [  Save  ]
```

- `<ModelSelector />` via Radix Select per role
- Save → `PUT /api/v1/teams/[id]` with optimistic UI

### `/tasks` + `/tasks/[id]`

**List:** filter bar (status · project · team · date) + task cards + "+ New Task" dialog
- Dialog fields: Title · Description · Team · Project · Fast Demo Mode toggle
- Submit → `POST /api/v1/tasks` → redirect `/tasks/[id]`

**`/tasks/[id]` — The Main Workspace:**

```
┌──────────────────────────────┬──────────────────────────────┐
│  AGENT TIMELINE              │  OUTPUT PANEL                │
│  ─────────────────────────── │  ──────────────────────────  │
│  ● Team Lead  [Gemini]       │  Output │ Files │ Review │   │
│    Planning task...          │  Security │ Logs │           │
│                              │                              │
│  ● Builder    [Claude]       │  [Syntax-highlighted code]   │
│    Implementing auth...      │  [File tree]                 │
│                              │  [Diff view: green/red]      │
│  ⏸ HUMAN INTERRUPT           │                              │
│  [ Approve ] [ Revise ]      │                              │
│                              │                              │
│  ● Reviewer   [GPT-4o]       │                              │
│    Checking edge cases...    │                              │
└──────────────────────────────┴──────────────────────────────┘
```

**WebSocket event handling:**

```typescript
AGENT_STARTED    → add placeholder card + spinner
AGENT_MESSAGE    → stream tokens into card (append chunks)
AGENT_COMPLETE   → remove spinner, mark card done
HANDOFF          → animate arrow between role icons in header
HUMAN_INTERRUPT  → show Approve / Request Changes buttons
                   → POST /api/v1/tasks/[id]/revise on reject
TASK_COMPLETE    → canvas-confetti (dynamic import)
TASK_ERROR       → error state card
WS disconnect    → top banner: "Connection lost — data may be stale"
```

### ✅ Phase 2 Gate

```
  ☐  tsc --noEmit                  →  0 errors
  ☐  eslint                        →  0 errors
  ☐  next build                    →  success
  ☐  /dashboard renders real data  →  or correct empty/error state
  ☐  /teams CRUD                   →  works end-to-end
  ☐  /tasks/[id] WebSocket         →  connected and streaming
  ☐  All 5 component states        →  implemented on every page
  ☐  Mobile layout                 →  tested at 375px
  ☐  FRONTEND_PROGRESS.md updated
  ☐  DESIGN_REVIEW.md updated
```

---

# ⚡ PHASE 3 — POWER FEATURES
### Execution graph · Quick Review · Analytics

```
Goal: The features that make AgentForge feel powerful.
      Heavy visualizations. Real-time data. Insight at a glance.
```

### `/executions/[id]` — Live Graph Viewer

```
┌──────────────────────────────────┬──────────────────────┐
│  EXECUTION GRAPH (60%)           │  LOG STREAM (40%)    │
│                                  │                      │
│  ┌─────────┐                     │  [14:32:01] team_lead│
│  │team_lead│──●──────────────►   │  Planning JWT auth   │
│  │  plan   │  ↑ animated dot     │                      │
│  └─────────┘                     │  [14:32:08] builder  │
│       │                          │  Writing middleware  │
│       ▼                          │                      │
│  ┌─────────┐                     │  [14:32:19] reviewer │
│  │ builder │                     │  3 issues flagged    │
│  └─────────┘                     │                      │
│    ╱   │   ╲                     │  ● ACTIVE            │
│  rev  test  sec   (parallel)     │                      │
│    ╲   │   ╱                     │                      │
│  ┌──────────┐                    │                      │
│  │aggregator│                    │                      │
│  └──────────┘                    │                      │
│       │                          │                      │
│  ┌──────────┐                    │                      │
│  │team_lead │                    │                      │
│  │ deliver  │                    │                      │
│  └──────────┘                    │                      │
└──────────────────────────────────┴──────────────────────┘
```

- Active node: pulsing `--accent` glow (CSS keyframes)
- Completed: `--live` green fill · Failed: `--error` red fill
- Zoom (mouse wheel) + pan (drag)
- Click node → right panel jumps to that agent's logs
- Both canvas components: **dynamic import only**

### `/review` — Quick Review

```
┌────────────────────────────────────────────┐
│  Paste code or describe what to review     │
│  ┌──────────────────────────────────────┐  │
│  │                                      │  │
│  │  // your code here                   │  │
│  │                                      │  │
│  └──────────────────────────────────────┘  │
│  Language: [TypeScript ▾]  [📎 Upload]     │
│                           [ Run Review → ] │
└────────────────────────────────────────────┘

Progress:  ●●●○○  Analyzing → Building → Reviewing → Done

Results:
┌─────────────────────────────────────────────────────┐
│  ⚠ HIGH   line 34   Missing input validation        │
│  ℹ INFO   line 67   Consider memoizing this call    │
└─────────────────────────────────────────────────────┘
```

- Full flow via `POST /api/v1/review`
- `<QuickReviewProgress />` with step labels
- `<QuickReviewResults />` findings table + summary

### `/analytics`

- Date range: Last 7d / 30d / Custom
- Stats row: Total Tasks · Success Rate · Avg. Duration · Top Model
- Recharts (dynamic import):
  - Line: tasks per day
  - Bar: tasks by agent role
  - Donut: model distribution
- Top Agents table: role · tasks · avg duration · error rate

### ✅ Phase 3 Gate

```
  ☐  tsc --noEmit                       →  0 errors
  ☐  eslint                             →  0 errors
  ☐  next build                         →  success
  ☐  /executions/[id] graph animates    →  correctly
  ☐  /review full flow                  →  works end-to-end
  ☐  /analytics charts                  →  render real data
  ☐  Canvas components                  →  dynamically imported (check bundle)
  ☐  Mobile layout                      →  tested at 375px
  ☐  FRONTEND_PROGRESS.md updated
  ☐  DESIGN_REVIEW.md updated
```

---

# ✨ PHASE 4 — POLISH + MARKETING
### Settings · BYOK · Projects · Public Landing Page

```
Goal: Complete the app. Then make it irresistible to strangers on the internet.
```

### `/projects` + `/projects/[id]`

- List: card grid — name · file count · last updated
- Detail: drag-and-drop file upload zone → `POST /api/v1/projects/[id]/files`
- File list: name · size · timestamp · delete
- Context tab: chunked repository viewer via `GET /api/v1/context?project_id=`

### `/settings` — 4 Tabs

**Profile** — name, email, change password

**API Keys (BYOK)**
```
  Provider       Key                      Actions
  ─────────────────────────────────────────────────
  OpenAI         sk-••••••••••••abcd      [Delete]
  Anthropic      sk-ant-••••••••efgh      [Delete]
  Google         AIza••••••••••••ijkl     [Delete]

  [ + Add Key ]

  ⚠ Keys are encrypted at rest using AES-256.
```

**Models** — default model per role (saves to `PUT /api/v1/teams/[id]`)

**Notifications** — toggles

### `(marketing)/page.tsx` — Public Landing

> This page converts engineers into users. Make it feel inevitable.

**Sections:**

**① Sticky Navbar**
Logo · Features · Pipeline · Pricing · Docs · `Sign in` ghost · `Join Waitlist` primary
Frosted glass backdrop on scroll

**② Hero**
```
           ● Now in Private Beta

   Ship with an AI team,
   not just a tool.

   AgentForge orchestrates specialized AI agents —
   Planner, Builder, Reviewer, QA, Security, DevOps —
   that collaborate like a real engineering team.

   [ Get Early Access ]   [ Read the Docs → ]

   ┌─────────────────────────────────────────────┐
   │         <AgentNetwork /> canvas             │
   │   6 nodes · animated bezier edges           │
   │   pulse-dot traveling along connections     │
   │   nodes glow + tooltip on hover             │
   └─────────────────────────────────────────────┘
```

**③ How It Works** — 3-column numbered steps
```
  01                    02                    03
  Define Your Team  →   Submit a Task     →   Agents Ship It
  Assign roles +        Describe what         Plan → Build →
  models to agents      to build              Review → Secure
```

**④ Pipeline Visualizer** — full-width dark card
```
[User Task] → [Team Lead] → [Builder] → [Reviewer + Tester + Security]
                                                    ↓
                                          [Aggregator] → [Team Lead] → [✓ Output]
```
Click any node → slide-in log panel with fake live output

**⑤ Features Grid** — 3×2
- Multi-Agent Orchestration
- LangGraph State Graph
- Real-Time WebSocket Logs
- pgvector Semantic Memory
- Human-in-the-Loop Approvals
- Bring Your Own Keys (BYOK)

**⑥ Dashboard Preview** — CSS-only browser chrome mockup, fake data inside

**⑦ Pricing**

| | Starter | Pro | Enterprise |
|---|---|---|---|
| Price | Free | $29/mo | Custom |
| Tasks/mo | 10 | Unlimited | Unlimited |
| Agents | 2 | All 6 | All 6 |
| Support | Community | Priority | SLA + Dedicated |
| BYOK | ✗ | ✓ | ✓ |
| SSO | ✗ | ✗ | ✓ |

**⑧ Waitlist Form**
Email input · "Reserve your spot" button · optimistic: *"You're on the list ✓"*

**⑨ Footer**
Logo · links · GitHub icon · *"Built for engineers who move fast."*

### ✅ Phase 4 Gate

```
  ☐  tsc --noEmit                     →  0 errors
  ☐  eslint                           →  0 errors
  ☐  next build                       →  success
  ☐  /settings BYOK                   →  works end-to-end
  ☐  Landing page                     →  renders + waitlist submits
  ☐  All pages mobile-tested          →  375px minimum
  ☐  Lighthouse /dashboard            →  performance ≥ 85
  ☐  FRONTEND_PROGRESS.md             →  all phases COMPLETE
  ☐  DESIGN_REVIEW.md                 →  final pass, no rogue patterns
  ☐  BACKEND_GAPS.md                  →  all gaps documented
  ☐  ARCHITECTURE_RISKS.md            →  all P0/P1 addressed or deferred
```

---

# 📚 LIVING DOCUMENTS
### Never delete. Append only. Updated after every phase.

| Document | Created | Updated |
|----------|---------|---------|
| `ROUTE_DISCOVERY_REPORT.md` | Phase 0 | Phase 0 |
| `API_SCHEMA_MAP.md` | Phase 0 | Phase 0 |
| `WEBSOCKET_EVENT_MAP.md` | Phase 0 | Phase 0 |
| `BACKEND_UI_COMPATIBILITY_REPORT.md` | Phase 0 | Phase 0 |
| `ARCHITECTURE_RISKS.md` | Phase 0 | Every phase |
| `BACKEND_GAPS.md` | Phase 0 | As gaps found |
| `FRONTEND_IMPLEMENTATION_PLAN.md` | Before Phase 1 | If scope changes |
| `FRONTEND_PROGRESS.md` | Phase 1 | After every phase |
| `DESIGN_REVIEW.md` | Phase 1 | After every phase |

### `FRONTEND_PROGRESS.md` Format

```markdown
## Phase 0 — Backend Audit
Status       : ✅ Complete
Deliverables : ROUTE_DISCOVERY_REPORT · API_SCHEMA_MAP · WS_EVENT_MAP · COMPAT_REPORT · ARCH_RISKS
Gaps found   : 3  (see BACKEND_GAPS.md)
Risks logged : 7  (P0: 1 · P1: 2 · P2: 3 · P3: 1)

## Phase 1 — Foundation
Status          : ✅ Complete
TypeScript errors: 0
ESLint errors   : 0
Build           : ✅ passed
Files generated : 28

## Phase 2 — Core App
Status          : 🔄 In Progress
Current file    : components/task/task-output-panel.tsx

## Phase 3 — Power Features
Status          : ⏳ Not Started

## Phase 4 — Polish + Marketing
Status          : ⏳ Not Started
```

---

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   Start with Phase 0.                                            │
│   Do not write a React component until all 5 audit              │
│   documents exist and are non-empty.                             │
│                                                                  │
│   Every phase gate must pass before the next begins.            │
│   BLOCKED beats COMPLETE based on assumption — always.          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```
