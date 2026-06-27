# AgentForge PMF Execution Plan

**Revision:** 2 (reordered for speed)
**Priority:** Ship value before measuring anything

---

## The Ordering Problem

Previous plan: Benchmark → Quick Review → Comparison → Team Builder → Retention

This is wrong. It spends 1-2 weeks proving the pipeline works before anyone has tried it. If the pipeline fails the benchmark, we've wasted time building infra for a product no one tried.

**Correct order:** Ship value → Validate demand → Measure quality → Iterate

---

## Phase A — Quick Review (NOW)

**Goal:** User gets value in under 15 seconds. No login. No team. No models.

### Backend: `POST /api/v1/review`

New file: `apps/api/app/routes/review.py`

```python
@router.post("/review")
async def quick_review(body: ReviewRequest):
    # 1. Clean code (strip whitespace, validate length)
    # 2. Run pipeline: Builder → Reviewer (no Lead, no Tester — speed first)
    # 3. Parse Reviewer output into structured issues
    # 4. Return issues + comparison + timing
```

Reuses existing `builder_node`, `reviewer_node`, `get_provider`. No new agents.

Default team (invisible):
- builder: qwen2.5-coder:7b
- reviewer: phi4-mini

No DB writes for anonymous users. No task/execution/message tables.

**Input:**
```json
{ "code": "def auth(request):\n    ...", "language": "python" }
```

**Output:**
```json
{
  "issues": [
    { "severity": "critical", "title": "Hardcoded API key", "line": 3,
      "description": "Secret key in source code", "suggestion": "Use env var" }
  ],
  "summary": "Found 3 issues",
  "comparison": {
    "bugs_single_would_miss": 3,
    "tests_generated": 0,
    "summary": "Without AgentForge: 3 bugs would ship"
  },
  "duration_ms": 12300
}
```

### Frontend: 3 components

**QuickReviewTextarea.tsx** — Full-width monospace textarea. Placeholder: "Paste your AI-generated code here..." "Review My Code" button. Example chips: "JWT auth", "REST API", "React component".

**QuickReviewProgress.tsx** — 3 stages: Analyzing → Checking → Results. Stage label + spinner. Elapsed time.

**QuickReviewResults.tsx** — Issues list: severity icon, title, line, description, suggestion. Comparison summary. "Review Another" button. "Save as Team" link (leads to Team Builder).

### Integration

Landing page (`app/page.tsx`) shows Quick Review textarea as primary surface:
- First-time visitor: textarea + examples + "How it works" section
- Returning user with data: textarea + recent reviews below

No more empty metric cards. No "Create Your First Team" as primary call-to-action.

### Kill criteria after ship

| Signal | Threshold | Action |
|--------|-----------|--------|
| Quick Reviews in week 1 | <20 | Reassess — no demand for the wedge |
| Quick Review → Save as Team | <5% | Conversion problem — fix flow |

---

## Phase B — Demo Comparison

**Goal:** Answer "why not ChatGPT?"

### Component: ComparisonPanel.tsx

Reusable. Shows after Quick Review results and on demo page.

```
┌─────────────────────────────────────┐
│ What ChatGPT would      AgentForge │
│ have shipped:           caught:     │
│                                     │
│ ✅ Looks clean         🔴 Hardcoded │
│ ❌ No validation       🔴 Injection │
│ ❌ 0 tests             🟢 12 tests  │
│                                     │
│ Without AgentForge: 3 bugs would    │
│ have shipped to production.         │
└─────────────────────────────────────┘
```

Data comes from the `/review` response `comparison` field. Honest — based on actual Builder output vs Reviewer findings.

### Changes to demo page

Current demo: "Here's how the pipeline works."
New demo: "Here's what ChatGPT generated. Here's what AgentForge caught."

Add to `app/demo/page.tsx`:
- Step 1: Show ChatGPT-generated code (the prompt's output)
- Step 2: Show issues found by AgentForge
- Step 3: ComparisonPanel showing the delta
- CTA: "Try it with your code →" (links to Quick Review)

Remove from demo page:
- Token counts
- Model names
- Pipeline graph (hide by default, show on expand)

---

## Phase C — Landing Page V2

**Goal:** First-time visitor understands value in 5 seconds.

### New structure

```
┌────────────────────────────────────────────┐
│ AgentForge                    Demo  Sign In │
│                                             │
│  ┌────────────────────────────────────┐    │
│  │ Paste your AI-generated code here  │    │
│  │                                    │    │
│  │  [                            ]    │    │
│  │  [                            ]    │    │
│  │         [Review My Code →]         │    │
│  └────────────────────────────────────┘    │
│                                             │
│  Try: "JWT auth"  "REST API"  "React"      │
│                                             │
│ ── How it works ──                          │
│ ① Paste code from ChatGPT/Claude/Cursor     │
│ ② AI agents review it for bugs + security   │
│ ③ Get results in under 30 seconds           │
│                                             │
│ ── See it in action ──                      │
│ [ComparisonPanel showing demo result]        │
│         [Watch Full Demo →]                  │
└────────────────────────────────────────────┘
```

Content removed from first-timer view:
- Metric cards
- Team list
- "Create Your First Team" button
- Sidebar navigation
- Token counts
- Model names

### Returning user view

If user has reviews or teams:
- Quick Review textarea still at top (always accessible)
- Below: Recent Reviews list with quality summary
- Below: Saved Teams grid

---

## Phase D — Internal Benchmark

**Goal:** Learn whether the pipeline actually catches bugs. 100 tasks, not 500.

### When to run

After Quick Review ships. Not before. Reason: if people use Quick Review and find value, the benchmark confirms why. If they don't, the benchmark doesn't matter.

### Dataset

100 tasks:

| Category | Count | Example |
|----------|-------|---------|
| Python | 25 | API with hardcoded secret, SQL injection |
| TypeScript | 25 | React component with XSS, missing key props |
| Security | 25 | JWT with no expiry, unsanitized input |
| API | 25 | Missing error handling, no rate limiting |

Each task has exactly 1-3 known bugs documented in a manifest.

### Runner

`apps/eval/runner.py`:
1. For each task: send code to Quick Review endpoint
2. Parse response issues
3. Compare against known bugs (manifest)
4. Compute TP, FP, FN, precision, recall, FPR

### Metrics

Minimal: precision, recall, false positive rate. That's it.

### Kill criteria (same as before, but measured with 100 tasks)

| Metric | Threshold | Action |
|--------|-----------|--------|
| Precision | <0.60 | Pipeline flags too many false issues |
| Recall | <0.50 | Pipeline misses most bugs |
| FPR | >0.15 | False positives destroy trust |

If pipeline passes: continue to Retention + Distribution.
If pipeline fails: fix reviewers before adding more features.

---

## Phase E — Retention

**Goal:** Give users a reason to come back.

### Features (build in this order)

1. **Review History** — List of past Quick Reviews with: date, language, issues found, summary. Stored in new `reviews` table.

2. **Saved Teams** — "Save as Team" button on Quick Review results. Creates a team with the default config. Shows up on dashboard.

3. **Quality Trends** — Dashboard shows: total reviews, bugs caught, top issue categories. Chart: bugs caught per review over time.

### Database: 005_reviews.sql

```sql
CREATE TABLE IF NOT EXISTS reviews (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID,
    code_hash   VARCHAR(64),
    language    VARCHAR(20),
    issues      JSONB DEFAULT '[]'::jsonb,
    comparison  JSONB DEFAULT '{}'::jsonb,
    duration_ms INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### Backend routes

```
POST /api/v1/reviews          ← Save a review (called after Quick Review for logged-in users)
GET  /api/v1/reviews          ← List reviews for user
GET  /api/v1/reviews/stats    ← Aggregated quality stats
```

---

## Phase F — Team Builder Repositioning

**Goal:** Teams are an advanced feature, not the entry point.

### New flow

```
Landing → Quick Review → Results → "Save as Team" → Team Builder
                                                      ↓
                                               Customize models
                                               Assign roles
                                               Advanced workflow
```

Team Builder stays as-is functionally but changes position in the funnel:
- No longer the first thing users see
- No longer required to get value
- Accessible from "Save as Team" after a Quick Review
- Direct navigation for power users who know what they want

### UX simplification

Model selector defaults to the working config from Quick Review. User sees:

```
Team: "My JWT Review Team"
├─ Builder: qwen2.5-coder:7b  (change ▼ — shows 3 recommended models)
└─ Reviewer: phi4-mini       (change ▼ — shows 3 recommended models)
```

No blank model selectors. No 10+ options. No "provider" selection.

---

## DEPENDENCY MAP

```
Phase A (Quick Review)
  ├── Phase B (Demo Comparison) — depends on Quick Review results
  ├── Phase C (Landing Page V2) — wraps Quick Review
  ├── Phase D (Benchmark) — depends on Quick Review endpoint existing
  └── Phase E (Retention) — depends on Quick Review results
        └── Phase F (Team Builder) — depends on "Save as Team" from Retention
```

**Everything depends on Quick Review working first.** That's why it's Phase A.

---

## IMPLEMENTATION START

Proceeding to build Phase A now: Quick Review backend route + frontend components.
