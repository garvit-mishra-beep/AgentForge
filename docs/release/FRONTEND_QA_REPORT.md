# Frontend Functional QA Report

`Version: 1.0` · `Audit Focus: Frontend Interactions & Integration Integrity`

This report catalogs a visual and functional audit of every page, modal, and button in the AgentForge frontend client, comparing it against the API backend contract.

---

## 1. Feature Interaction Scorecard

| Page / Component | Interaction Area | Status Classification | Findings & Code Context |
| :--- | :--- | :--- | :--- |
| **Login** | Email/Password submissions | **WORKING** | Resolves to `POST /api/v1/auth/login` and correctly populates JWT, refresh tokens, and user metadata key-value slots in localStorage. |
| **Register** | Account creation | **WORKING** | Resolves to `POST /api/v1/auth/register` and successfully redirects to `/dashboard` upon completion. |
| **Logout** | Clear session | **WORKING** | Resolves to `POST /api/v1/auth/logout` and untracks local session tokens. |
| **Google Auth** | Third-party sign-in | **PLACEHOLDER** | Bypassed. Option A (Email + Password only) is the active security model for V1. |
| **Dashboard** | Mission Control overview | **WORKING** | Correctly polls running tasks, completed executions, and analytical usage counters in parallel. |
| **Projects** | Repository contexts | **WORKING** | Allows creating projects, indexing files, and configuring project-level environments. |
| **Tasks** | Agent Execution loop | **WORKING** | Triggers state graph runners, renders real-time timeline logs, and accepts human interactive approval interventions. |
| **Teams** | Model and role grid | **WORKING** | Replaces select cards with detailed role model assignments grid, committing edits in parallel. |
| **Executions** | Timeline logs page | **WORKING** | Renders state transitions and files tree browsers. |
| **Docs** | Marketing docs link | **BROKEN** | Links to `/docs` in marketing headers and footers, yielding a client-side Next.js 404 because no `/docs` route exists. |
| **Settings** | App variables config | **WORKING** | Correctly resolves mask keys and encryption settings. |
| **Pricing** | Plan tiers cards | **PLACEHOLDER** | Renders Starter, Pro, and Enterprise plan tables, but does not integrate payment gateways (Stripe/PayPal). Clicking tier buttons redirects to `/register`. |
| **BYOK** | API keys configuration | **PARTIALLY_WORKING** | Pricing tables state BYOK is reserved for Pro/Enterprise plans, but backend files do not enforce plan restrictions (all registered users can configure keys). |
| **Waitlist** | Email access requests | **BROKEN** | Submitting the waitlist form on the home page calls `POST /api/v1/waitlist`, which fails with a backend 404 (endpoint does not exist). |

---

## 2. Detailed Findings & Remediation Steps

### P0 (Critical Blockers)
*No P0 critical blockers are active; authentication flows, task creations, and sandboxed runtimes are fully verified.*

### P1 (High Severity Issues)

#### 1. Docs Navigation Link
*   **Page**: Marketing Page (`app/(marketing)/page.tsx`)
*   **Component**: Header navigation (`NAV_ITEMS`) and CTA Footer links
*   **Root Cause**: Links point to a client-side route `/docs` which does not exist. 
*   **Fix Estimate**: **30 minutes**
*   **Remediation**: Correct links to target either the backend Swagger `/docs` endpoint (using an absolute URL e.g. `http://localhost:8000/docs`) or link directly to the repository docs hub.

#### 2. Waitlist Form Endpoint
*   **Page**: Marketing Page (`app/(marketing)/page.tsx`)
*   **Component**: Section `#waitlist` form submission handler
*   **Root Cause**: The form attempts to submit payload metadata to `POST /api/v1/waitlist`, but the backend FastAPI server does not implement or register a waitlist router.
*   **Fix Estimate**: **1 hour**
*   **Remediation**: Either create a database table and registered router endpoint for waitlist submissions, or integrate the form with a third-party waitlist/newsletter provider.

---

### P2 (Low Severity / Product Alignment)

#### 1. BYOK Plan-Level Enforcement
*   **Page**: Settings & Task Creation Pages
*   **Component**: Model configuration inputs
*   **Root Cause**: Discrepancy between marketing plan limits (which claim BYOK is restricted to Pro and Enterprise tiers) and code logic (which permits all users to configure provider API keys).
*   **Fix Estimate**: **2 hours**
*   **Remediation**: Either update marketing copy to declare BYOK as a platform-wide core capability (Option Recommended), or introduce check restrictions in the task creation router.

#### 2. Pricing Tiers Checkout Redirects
*   **Page**: Marketing Page (`app/(marketing)/page.tsx`)
*   **Component**: `#pricing` cards CTA buttons
*   **Root Cause**: Payment gateways are not coded, so buttons serve as redirects to signup page.
*   **Fix Estimate**: **3 hours** (if integrating payment gateway), **10 minutes** (if modifying wording)
*   **Remediation**: Add explicit copy notes declaring payment integrations as "Coming Soon," or link pricing CTAs directly to team workspace setups.
