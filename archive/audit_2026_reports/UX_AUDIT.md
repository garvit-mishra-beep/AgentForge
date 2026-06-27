# AgentForge — UX Audit (2026-06-26)

Reviewed: `apps/web/app/*` (all routes) and `apps/web/components/*`.

## Strengths (verified)
- **Landing page** (`app/page.tsx`, ~413 lines): clear hero, embedded Quick-Review CTA, proof-stats,
  3-step "how it works", FAQ, footer. Genuinely good top-of-funnel.
- **Loading / empty / error states** handled on most pages: spinners (`tasks/page.tsx:191-195`),
  empty CTAs (`teams/page.tsx:172-185`), error boxes with retry (`page.tsx:177-184`), and a global
  `error-boundary.tsx` fallback.
- **Responsive:** desktop sidebar collapses to a mobile sheet (`sidebar.tsx:115-198`); responsive grids.
- **Keyboard niceties:** Ctrl+Enter submit (`QuickReviewTextarea.tsx:77-82`), command palette.
- Consistent design system (Radix + Tailwind), dark theme, Framer Motion polish.

## Friction points & defects
1. **No route protection** — logged-out users reach `/dashboard`,`/teams`,`/tasks`; the page just
   spins/fails. On a final 401, `lib/api.ts` does not redirect to `/login`. *Confusing dead-end.*
2. **Auth in `localStorage`** (`auth-context.tsx:39-41`) — security + UX risk (token theft via XSS).
3. **No password recovery / no email verification / no social login** — `register/page.tsx` is a
   4-field form with hard fail on mismatch; `login/page.tsx` has no "forgot password".
4. **Review history is browser-local** (`page.tsx:87-97`) — switching device/browser loses everything;
   no reason to return.
5. **No timeout/stuck state** in task polling — a hung execution shows a spinner indefinitely
   (`tasks/[id]/page.tsx` polls every ~600ms with no give-up UI).
6. **`/demo` is fake** (`lib/demo-data.ts`) — a scripted animation, not the real pipeline. A new user
   who tries `/demo` then the real flow will feel the gap (the real flow is slower and plainer).
7. **A11y:** icon-only buttons lack `aria-label` (`sidebar.tsx:96`, `topbar.tsx:96`); no modal focus
   trap/restoration. Label/input pairing and focus rings are correct.
8. **Two products, one nav** — Quick Review vs Team Builder aren't visually differentiated; users
   won't know where the value is.

## Dead/duplicate UI
- Unused: `components/status-dot.tsx`, `components/ui/skeleton.tsx`.
- Quick-Review UI duplicated across `page.tsx`, `dashboard/page.tsx`, `review/page.tsx`.

## Redesign recommendations (prioritized)
1. **Add route guards** + redirect-to-login; persist intended destination.
2. **Move auth to HttpOnly cookies**; remove tokens from JS.
3. **Make Quick Review the home action** for logged-in users; persist review history server-side.
4. **Add stuck/timeout/cancel UI** to executions and a "what's happening" stepper tied to real graph events.
5. **Add forgot-password + email verification**; consider GitHub OAuth (also enables PR integration).
6. **Either make `/demo` run the real pipeline (sandboxed) or label it explicitly as a simulation.**
7. **A11y pass:** aria-labels on icon buttons, focus management in modals/command palette.

## Verdict
UX maturity is **high at the funnel, thin underneath**. The landing/demo would convert; the
authenticated product has dead-ends (no guards), a security smell (localStorage auth), and no
retention. Polish is not the problem — **product focus and post-signup substance are.**
