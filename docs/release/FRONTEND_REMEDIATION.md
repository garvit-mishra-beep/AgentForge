# Frontend Remediation Plan

This document outlines the remediation plan for findings identified in the frontend audit.

---

## 1. Remediation Schedule

| Task ID | Severity | Effort | Component | Description | Dependency |
|:---|:---:|:---:|:---|:---|:---|
| **FE-01** | **P0** | M | app/projects/\[id\]/page.tsx | Implement the actual project detail view (files list, upload, details) instead of rendering the duplicate Login Page. | None |
| **FE-02** | **P0** | M | app/tasks/\[id\]/page.tsx | Implement the actual task execution stream view showing agent steps instead of rendering the duplicate Settings Page. | None |
| **FE-03** | **P0** | M | app/teams/\[id\]/page.tsx | Implement the actual team member edit and model selection view instead of rendering the duplicate Tasks Page. | None |
| **FE-04** | **P1** | M | app/executions/\[id\]/page.tsx | Connect `/executions/[id]` page to the real backend API (`getTaskMessages`) instead of showing static simulated scenarios. | None |
| **FE-05** | **P2** | S | lib/ws-client.ts | Fix missing dependency warning in `useWebSocket` hook to prevent stale closure callbacks. | None |
| **FE-06** | **P2** | M | components/auth/auth-context.tsx | Move JWT access and refresh token storage from `localStorage` to secure HTTP-only cookies to mitigate XSS risk. | None |
| **FE-07** | **P3** | S | components/auth/auth-context.tsx | Implement BroadcastChannel / storage event listener to sync logouts across multiple browser tabs. | None |

---

## 2. Details of High Priority Remediation (P0 / P1)

### FE-01: Projects Detail Page Re-implementation
- **Action**: Replace the entire file with a component that:
  1. Queries `/projects/{id}` to fetch project information.
  2. Queries `/projects/{id}/files` to render the tree of uploaded files.
  3. Integrates with the ZIP/file upload inputs.

### FE-02: Tasks Detail Page Re-implementation
- **Action**: Replace the entire file with a component that:
  1. Retrieves the task record using `getTask(id)`.
  2. Queries `/tasks/{id}/messages` to get logs.
  3. Feeds logs to the step status execution layout.

### FE-03: Teams Detail Page Re-implementation
- **Action**: Replace the entire file with a component that:
  1. Loads team information using `getTeam(id)`.
  2. Lists members and their assigned LLM models.
  3. Provides forms to edit member instructions and models.

### FE-04: Connect Executions Page to API
- **Action**: Replace the static simulation loop in `app/executions/[id]/page.tsx` with a polling or event-driven mechanism:
  1. Load initial task messages via HTTP request on mount.
  2. If execution status is `running`, poll or connect to the event stream to append new message cards in real-time.
