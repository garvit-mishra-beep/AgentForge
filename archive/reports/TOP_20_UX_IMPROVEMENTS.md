# Top 20 UX Improvements

**Date:** 2026-06-26
**Author:** Chief Product Officer

**Constraint:** No enterprise features, no billing, no scaling, no infrastructure.

---

## Priority Key

| Tier | Effort | Impact |
|------|--------|--------|
| P0 | < 1 day | Transforms user perception |
| P1 | 1-3 days | Significant quality-of-life improvement |
| P2 | 3-7 days | Delightful addition |

---

## P0 Improvements (Do These First)

### 1. Fix Templates to Populate Team Members

**File:** `apps/web/app/teams/page.tsx:85-87`

**Problem:** Clicking a template pre-fills the team name but ignores the member configuration. Users see role badges with model names on template cards, select a template, and get an empty team. This is the #1 source of early disappointment.

**Fix:** When a template is selected, call the API to create team members for each configured role, or create the team with members in a single API call. At minimum, remove the role badges from template cards if they won't be applied.

**Impact:** **Critical.** This is the first interactive moment after the demo. Getting it wrong creates immediate distrust.

---

### 2. Add Value Layer to the Demo

**File:** `apps/web/app/demo/page.tsx`

**Problem:** The demo shows *what* happens (5 steps, 4 agents) without explaining *why* it matters. Users see the mechanism but not the value.

**Fix:** Add callout annotations that appear at key moments:
- When the reviewer message appears: overlay text: "The reviewer caught 2 issues the builder would have shipped."
- When the tester message appears: overlay text: "The tester verified 87% code coverage — automatically."
- At the end: comparison text: "A single AI model would have shipped those 2 issues. AgentForge caught them."

**Impact:** **High.** Transforms the demo from "interesting" to "compelling."

---

### 3. Create Post-Execution Habit Loop

**File:** `apps/web/app/tasks/[id]/page.tsx:329-346`

**Problem:** After a task completes, there's no compelling next action. Users leave and don't return.

**Fix:** Add to the completed state:
- "Run again with a different model" button (pre-fills team selector with current team)
- "Share this result" button (copies a shareable link)
- "Create task from template" button (saves the task description as a template)
- Side-by-side model comparison CTA

**Impact:** **High.** Retention is currently zero. This creates the first retention loop.

---

### 4. Add "Why This Role" Explanations

**File:** `apps/web/app/teams/[id]/page.tsx:150-155`

**Problem:** Role descriptions are mechanical ("Writes code", "Reviews output") rather than value-driven. Users don't understand why specialized roles produce better work.

**Fix:** Replace with benefit-driven descriptions:
- Lead: "Plans the architecture so the team has clear direction"
- Builder: "Writes production code focused on the plan"
- Reviewer: "Catches bugs and edge cases the builder missed"
- Tester: "Verifies with automated tests before delivery"

**Impact:** **Medium-High.** Helps users understand and buy into the multi-agent concept.

---

### 5. Fix Duration Counter Sticking After Completion

**File:** `apps/web/app/tasks/[id]/page.tsx:244-248`

**Problem:** The duration counter uses `Date.now()` on every render, so it continues incrementing after the task completes. "12s" becomes "15s" becomes "23s" as the user reads the completed output.

**Fix:** Capture `execution.completed_at` when the task completes and use that for the final duration calculation.

**Impact:** **Medium.** A bug that erodes trust in the metrics display.

---

## P1 Improvements (1-3 Days Each)

### 6. Add Model Recommendations Per Role

**File:** `apps/web/app/teams/[id]/page.tsx:19-30`

**Problem:** 10 model options with cryptic names overwhelm new users. Tags like "Fast" and "Lightweight" don't explain why a model fits a role.

**Fix:** Mark one model per role as "Recommended" with a tooltip:
- Builder: "qwen2.5-coder:7b is fine-tuned for code generation"
- Reviewer: "phi4-mini excels at pattern analysis and finding edge cases"
- Lead: "qwen3.5:4b balances planning capability with speed"
- Tester: "qwen3 offers broad knowledge for test case generation"

Reduce options to 5 per role (only show models relevant to that function).

---

### 7. Add Execution Time Estimate Before Task Submission

**File:** `apps/web/app/tasks/page.tsx:176-179`

**Problem:** Users hit "Start Task" with no idea how long it will take. A 60-second wait feels like an eternity without expectations.

**Fix:** Show "Estimated time: ~30 seconds" next to the submit button. Show it decreasing as the task runs.

---

### 8. Add Retry Button for Failed Tasks

**File:** `apps/web/app/tasks/[id]/page.tsx:337-345`

**Problem:** Failed tasks show an error message with no action. Users must navigate away and create a new task from scratch.

**Fix:** Add "Retry with same configuration" and "Retry with different model" buttons to the error state.

---

### 9. Add "What Happens Now" to Task Detail Page

**File:** `apps/web/app/tasks/[id]/page.tsx`

**Problem:** Users arrive at the task detail page after submission and see a blank loading state. No explanation of the pipeline.

**Fix:** Show the ExecutionGraph immediately (even before data arrives) with all steps marked as "pending." Add a subtle text: "Your team is starting — Lead will plan, Builder will code, Reviewer will review, Tester will test."

---

### 10. Remove or Rebuild Settings Page

**File:** `apps/web/app/settings/page.tsx`

**Problem:** Every value on the Settings page is hardcoded decoration. API Key shows dots but can't be configured. Theme says "Dark (default)" but there's no toggle.

**Fix:** Either make all settings functional (API URL input, theme toggle, model provider selection) or remove the page entirely and redirect to the dashboard. Fake settings are worse than no settings.

---

### 11. Replace "Mission Control" with a Meaningful Tagline

**File:** `apps/web/app/page.tsx:77`

**Problem:** "Mission Control" is an abstract metaphor that doesn't communicate product value.

**Fix:** Use the space above the headline to show a rotating value proposition:
- "Build better code with AI teams"
- "AI code review that catches bugs"
- "Your multi-agent development platform"

---

### 12. Add Agent Collaboration Visuals to Execution View

**File:** `apps/web/app/tasks/[id]/page.tsx`

**Problem:** The execution view shows individual messages from individual agents. Users don't see the *interaction* between agents.

**Fix:** Add visual handoff indicators between messages:
- A subtle arrow connecting "Lead planned" → "Builder coded"
- A highlight when "Reviewer analyzed Builder's code"
- A summary line: "Builder created 2 files → Reviewer found 2 issues → Tester wrote 5 tests"

---

## P2 Improvements (Nice-to-Have)

### 13. Add Sound Effect on Task Completion

**File:** `apps/web/app/tasks/[id]/page.tsx`

**Problem:** No audio feedback when a task completes. Users must watch the screen.

**Fix:** Play a subtle chime (like a macOS notification) when the task status transitions to "completed." Respect `prefers-reduced-motion`.

---

### 14. Add "Quick Demo" Mode (10 Seconds)

**File:** `apps/web/app/demo/page.tsx`

**Problem:** The ~12-second demo is too long for conference walk-bys or quick shares.

**Fix:** Add a URL parameter `?speed=fast` that halves all delays, completing the demo in 5-6 seconds.

---

### 15. Add Shareable Execution Replay Links

**File:** `apps/web/app/executions/[id]/page.tsx`

**Problem:** No way to share an execution result with others.

**Fix:** Add a "Share" button that copies a URL. The recipient sees a read-only replay of the execution (pre-generated or replayed from stored messages).

---

### 16. Add Team Configuration Scoring

**File:** `apps/web/app/teams/[id]/page.tsx`

**Problem:** Users don't know if their team is well-configured.

**Fix:** Show a "Team Quality" metric: "Balanced team" (1 of each role), "Review-heavy" (2 reviewers), "Builder-focused" (2 builders). Suggest optimal configurations based on task type.

---

### 17. Improve Empty States with Benefit Copy

**File:** All empty states

**Problem:** Empty states describe the interface ("No teams yet") instead of motivating action.

**Fix:** Replace with benefit-driven copy:
- Before: "No AI teams yet"
- After: "AI teams build better code. Create your first one."

---

### 18. Add "Compare with Single Model" Toggle in Demo

**File:** `apps/web/app/demo/page.tsx`

**Problem:** Users can't see the difference between AgentForge and a single model.

**Fix:** Add a toggle: "Show me what a single model would produce." Display a simulated single-model response without review or testing steps. The contrast makes the multi-agent value obvious.

---

### 19. Add Model Size Legend

**File:** `apps/web/app/teams/[id]/page.tsx`

**Problem:** Users see "4B", "7B", "3.8B" without understanding what these numbers mean.

**Fix:** Add a small legend: "Model sizes: 3B = fast & lightweight, 7B = balanced, 14B+ = most capable but slower." Position it as a tooltip next to the "Select Model" label.

---

### 20. Add "Task Type" Pre-sets

**File:** `apps/web/app/tasks/page.tsx`

**Problem:** All tasks use the same pipeline, but different task types benefit from different configurations.

**Fix:** Add optional task type selector: "Code Generation", "Code Review", "Test Writing", "Architecture Design", "Documentation". Each type adjusts the pipeline steps and model recommendations.

---

## Effort-Impact Matrix

```
                    HIGH IMPACT
                        |
    P0: Fix templates   |   P0: Demo value layer
    P0: Habit loop      |   P0: Role explanations
    P0: Duration bug    |   P1: Model recommendations
                        |
   EASY ----------------+---------------- HARD
                        |
    P2: Sound effects   |   P2: Shareable replays
    P2: Quick demo mode |   P2: Task type presets
    P1: Settings page   |   P1: Collaboration visuals
                        |
                    LOW IMPACT
```

## Recommended Sprint Plan

| Sprint | Improvements |
|--------|-------------|
| Sprint 1 (this week) | #1 Fix templates, #2 Demo value layer, #5 Duration bug |
| Sprint 2 | #4 Role explanations, #6 Model recommendations, #10 Settings page |
| Sprint 3 | #3 Habit loop, #7 Time estimates, #8 Retry button |
| Sprint 4 | #9 "What happens now", #11 Tagline, #12 Collaboration visuals |
| Sprint 5 | #13-20 Nice-to-haves |
