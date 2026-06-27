# Landing Page v2 — Product Requirements Document

**Status:** Draft v1
**Owner:** CPO
**Target Users:** First-time visitors (the only audience that matters for landing pages)
**Value Proposition:** "Paste code. Get review. Ship with confidence."

---

## 1. Problem Statement

The current landing page (`/`) shows a dashboard with:
- Metric cards (Active Teams, Total Tasks, Running, Executions) — all showing empty states or zeroes
- "Create Your First Team" button — requires 2-3 minutes of work before any value
- "Watch Demo" secondary button — the demo doesn't answer "why not ChatGPT?"

A first-time visitor sees empty metrics and has no idea what the product does. They have to click a button to discover value. Most don't.

**The landing page currently serves returning users with data, not first-time visitors who need to understand the product.**

---

## 2. User Story

> As a developer who heard about AgentForge,
> I want to understand what it does in 5 seconds,
> So that I can decide if it's worth trying.

**The landing page must communicate value within 5 seconds. Not "create something." Not "explore." Not "sign up." Just understand.**

---

## 3. Success Metrics

| Metric | Target | Why |
|--------|--------|-----|
| Time to value clarity | <5 seconds | Users decide in 5 seconds whether to stay |
| Click-through to Quick Review | >30% | Primary action — paste code |
| Click-through to Demo | >15% | Secondary action — watch comparison |
| Bounce rate | <50% | Current: likely >80% based on empty state |
| Free sign-ups (after first review) | >10% of reviewers | Sign-up is a result of value, not a prerequisite |

---

## 4. Page Structure

### Two States

**State A: First-time visitor (no cookie, no auth)**
Full hero section with Quick Review text area. No dashboard. No metrics. No navigation complexity.

**State B: Returning user (has account, has reviews)**
Dashboard with personal stats, recent reviews, saved teams. Quick Review still accessible.

This PRD covers **State A** — the first-time visitor experience.

---

## 5. Design Requirements

### Layout (Desktop)

```
┌──────────────────────────────────────────────────────────┐
│ [Logo]                                  [Sign In] [Demo] │
│                                                            │
│ ┌─ AgentForge───────────────────────────────────────────┐ │
│ │                                                        │ │
│ │   Paste your AI-generated code here                    │ │
│ │   and get an instant review.                           │ │
│ │                                                        │ │
│ │   ┌────────────────────────────────────────────────┐   │ │
│ │   │                                                │   │ │
│ │   │    Paste code from ChatGPT, Claude,            │   │ │
│ │   │    or any AI coding tool...                    │   │ │
│ │   │                                                │   │ │
│ │   │                                                │   │ │
│ │   │                                                │   │ │
│ │   │              [Review My Code →]                │   │ │
│ │   └────────────────────────────────────────────────┘   │ │
│ │                                                        │ │
│ │   Try: "JWT auth" "REST API" "React component"         │ │
│ │                                                        │ │
│ └───────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌─ Proof Points ─────────────────────────────────────────┐ │
│ │                                                        │ │
│ │   40% more bugs caught   12 tests generated   <30 secs  │ │
│ │   than single AI review   per review          per review │ │
│ │                                                        │ │
│ └───────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌─ How It Works ──────────────────────────────────────────┐ │
│ │                                                        │ │
│ │   ① Paste   ② AI Review   ③ Get Results               │ │
│ │                                                        │ │
│ │   Your code is analyzed by 4 specialized AI agents.     │ │
│ │   They catch bugs, security issues, and missing tests   │ │
│ │   that a single AI model would miss.                    │ │
│ │                                                        │ │
│ └───────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌─ See It In Action ──────────────────────────────────────┐ │
│ │                                                        │ │
│ │  ┌──────────────────┐  ┌──────────────────────────┐    │ │
│ │  │ ChatGPT output:   │  │ AgentForge caught:       │    │ │
│ │  │                   │  │                          │    │ │
│ │  │ def auth(req):    │  │ 🔴 Hardcoded secret      │    │ │
│ │  │   return jwt.deco-│  │ 🔴 Missing error handling│    │ │
│ │  │   de(req, "key")  │  │ 🟢 12 tests generated   │    │ │
│ │  └──────────────────┘  └──────────────────────────┘    │ │
│ │                                                        │ │
│ │           [Watch Full Demo →]                          │ │
│ │                                                        │ │
│ └───────────────────────────────────────────────────────┘ │
│                                                            │
│ [Footer: © 2026 AgentForge. Privacy. Terms.]               │
└──────────────────────────────────────────────────────────┘
```

### Content Sections (Top to Bottom)

**Header:**
- Logo (left)
- "Demo" link (center-right) — links to `/demo`
- "Sign In" link (right) — links to `/auth/signin`
- No "Get Started" button — the text area IS the Get Started

**Hero (above the fold):**
- Headline: "Paste your AI-generated code here and get an instant review."
- This is the ONLY headline. One sentence. No sub-headline.
- Quick Review text area (see QUICK_REVIEW_PRD.md for spec)
- Example chips: "JWT auth" | "REST API" | "React component" | "SQL migration"
- These chips populate the text area with example code

**Proof Points (below hero):**
- Three metrics in a row: "40% more bugs caught than single AI review" | "12 tests generated per review" | "<30 seconds per review"
- These are claims that the Quick Review experience will prove
- Each has an icon (shield, flask, clock)

**How It Works:**
- Three simple steps with icons
- Step 1: Paste — "Paste code from ChatGPT, Claude, or any tool"
- Step 2: AI Review — "4 specialized agents analyze your code"
- Step 3: Results — "Get bugs, security issues, and tests in seconds"
- No numbered steps with arrows — just a clean three-column layout

**See It In Action:**
- Mini demo comparison: static before/after showing ChatGPT output vs AgentForge findings
- This is a static preview, not the full interactive demo
- "Watch Full Demo →" CTA links to `/demo`
- The comparison should be the same code as the full demo (JWT auth)

**Footer:**
- Logo
- Privacy Policy
- Terms of Service
- © 2026 AgentForge

### What Is NOT On The Page

- Metric cards (Active Teams, Total Tasks, Running, Executions)
- "Create Your First Team" button
- Sidebar navigation
- Team list
- Recent activity
- Any empty state
- Model names
- Token counts
- Pipeline architecture
- "Multi-agent platform" language
- Dashboard elements

---

## 6. Mobile Layout

```
┌──────────────────────────────┐
│ [Logo]        [Demo] [Login] │
│                                │
│ Paste your AI-generated       │
│ code and get an instant       │
│ review.                       │
│                                │
│ ┌──────────────────────────┐  │
│ │                          │  │
│ │ Paste code here...       │  │
│ │                          │  │
│ │                          │  │
│ │                          │  │
│ │    [Review My Code]      │  │
│ └──────────────────────────┘  │
│                                │
│ Try: "JWT auth" "REST API"    │
│                                │
│ ── Proof Points ──            │
│ 40% more bugs caught          │
│ 12 tests generated            │
│ <30 seconds per review        │
│                                │
│ ── How It Works ──            │
│ ① Paste  ② AI Review         │
│ ③ Get Results                 │
│                                │
│ ── See It In Action ──        │
│ [Mini comparison — stacked]   │
│                                │
│ [Watch Full Demo →]           │
└──────────────────────────────┘
```

- Single column, everything stacks
- Text area takes full width
- Proof points stack vertically
- See It In Action comparison is stacked (ChatGPT output on top, AgentForge caught below)

---

## 7. Copy Requirements

| Element | Copy | Rationale |
|---------|------|-----------|
| Headline | "Paste your AI-generated code here and get an instant review." | One sentence. Complete thought. No ambiguity. |
| Text area placeholder | "Paste code from ChatGPT, Claude, or any AI coding tool..." | Sets context: this is for code from AI tools |
| Button | "Review My Code" | Personal. Action. "My" creates ownership. |
| Example label | "Try:" | Minimal. Inviting. |
| Proof point 1 | "40% more bugs caught than single AI review" | Concrete. Provable. Differentiating. |
| Proof point 2 | "12 tests generated per review" | Specific. Measurable. |
| Proof point 3 | "<30 seconds per review" | Addresses the speed objection directly |
| How It Works title | "How It Works" | Standard. Clear. |
| How It Works step 1 | "Paste your code" | Obvious. |
| How It Works step 2 | "AI agents review it" | "AI agents" not "multi-agent pipeline" |
| How It Works step 3 | "Get bugs, tests, and security fixes" | Concrete outputs. |
| See It In Action title | "See It In Action" | Standard. |
| See It In Action CTA | "Watch Full Demo →" | Obvious. |

**Tone:** Direct. Confident. Zero fluff.
- One sentence paragraphs
- No adjectives before nouns (not "powerful AI", not "cutting-edge")
- Every word must earn its place

---

## 8. Animation Requirements

| Element | Animation | Why |
|---------|-----------|-----|
| Text area | Subtle glow/pulse on page load | Draws attention without being distracting |
| Example chips | Hover: slight lift (2px translateY) | Indicates clickability |
| Proof points | Fade in on scroll | Creates progression feel |
| See It In Action | Hover: mini comparison transforms | Indicates clickability for demo |
| Page load | Sequential fade-in: header → hero → proof → how → action | Clean, professional entrance |

No auto-playing video. No hero animation that distracts from the text area.

---

## 9. Acceptance Criteria

- [ ] Above the fold: only logo, text area, examples, and button
- [ ] No metric cards visible to first-time visitors
- [ ] No "Create Team" button on first visit
- [ ] Text area is the focal point (60% of above-fold space)
- [ ] Example chips populate text area with realistic code
- [ ] "Review My Code" triggers Quick Review (see QUICK_REVIEW_PRD.md)
- [ ] "Demo" link navigates to `/demo`
- [ ] "Sign In" link navigates to `/auth/signin`
- [ ] Proof points section shows 3 metrics with icons
- [ ] How It Works section shows 3 steps with icons
- [ ] See It In Action shows static before/after comparison
- [ ] Watch Full Demo links to `/demo`
- [ ] Footer: Privacy Policy, Terms, © 2026
- [ ] Responsive design (desktop, tablet, mobile)
- [ ] No model names, token counts, or pipeline architecture visible
- [ ] Page loads in <2 seconds (no heavy assets)
- [ ] State transitions: text area → loading → results (all inline, no page reload)

---

## 10. What NOT to Build

| Feature | Rejection Reason |
|---------|-----------------|
| Metric cards | Meaningless to new users. Shows after first review (returning user state). |
| Team creation | Blocks value creation. Teams are power-user feature. |
| Sidebar | Desktop-first nav. Sidebar adds complexity with no value. |
| User onboarding flow | Let users paste code first. Show onboarding after value is proven. |
| Video hero | Slow to load. Text + text area is faster and clearer. |
| Carousel/slider | Users don't interact with carousels. Static content beats sliders. |
| Pricing section | Premature. No one will pay before understanding value. |
| Social proof | Testimonials without real users are dishonest. Add later with real data. |
| Blog/news | Out of scope. Landing page should convert, not educate. |
| Language switcher | Premature localization. |

---

## 11. Edge Cases

| Case | Handling |
|------|----------|
| Returning user (cookie detected) | Show dashboard with recent reviews and stats |
| Returning user (no reviews yet) | Show landing page v2 with text area — same as first-time |
| User with adblock/tracking blocked | Cookie detection fails. Show landing page v2. User can always paste code. |
| Slow connection | Text area and static content load first. Proof points and How It Works load progressively. |
| JavaScript disabled | Show minimal fallback: logo, text area with `<form>` action to `/review`, no animations |
| Mobile keyboard open | Text area scrolls into view, doesn't overlap with other content |
| User scrolls past text area | Sticky "Quick Review" FAB appears after hero scrolls past (mobile only) |
