# Next 30 Days: Top 5 Highest-ROI Improvements

## Selection Criteria

- **User impact:** How many users benefit × how much
- **Engineering effort:** Estimated person-days
- **Startup impact:** Effect on retention, conversion, or funding narrative

---

## #1: Demo Comparison Layer

**Why:** The single highest-risk issue is "why not ChatGPT?" Every user asks it. The demo currently avoids the question. Adding a comparison layer directly addresses the existential threat.

**User impact:** 100% of demo viewers — every potential user. Transforms "cool demo" into "compelling reason to try."

**Engineering effort:** 2-3 days
- Modify `demo/page.tsx` to add comparison panel (1 day)
- Add "Single AI vs AgentForge" side-by-side to demo data (0.5 day)
- Add "Why this matters" callouts per step (0.5 day)
- Update CTA copy from "how it works" to "why it's better" (0.5 day)

**Startup impact:** High. This is the difference between "interesting project" and "I should try this."

**What to build:**
- Right-side comparison panel showing accumulating contrast
- Each step reveals a new row: "Single AI: no tests" vs "AgentForge: 12 tests"
- Final "Why this matters" summary with quantified difference
- New CTA: "Why use ChatGPT when you can have a team?"

---

## #2: Run Again + Saved Teams

**Why:** The #2 risk is zero retention. Run Again is the simplest retention feature — one button that re-creates the same task with a different team. Saved Teams lets users bookmark configurations.

**User impact:** 100% of users who complete a task. Gives immediate next action instead of dead end.

**Engineering effort:** 1.5 days
- Run Again button on task detail page (0.5 day)
- `is_favorite` migration + API toggle (0.5 day)
- Star toggle on team detail page (0.25 day)
- Saved teams filter on teams list (0.25 day)

**Startup impact:** High. First retention feature. Creates the habit loop: "run → complete → run again with different team → compare → save."

**What to build:**
- `[Run Again]` button in task detail completion CTA
- Click → modal: select team → creates task with same title/description
- Star icon on team detail header → toggle favorite
- "Favorites" filter on teams page

---

## #3: Collaboration Visibility (One Feature)

**Why:** Risk #5 — the product's core differentiation is invisible. Users can't see agents working together. The highest-ROI single change is showing **handoffs** between agents.

**User impact:** 100% of execution viewers. Transforms "5 messages" into "a team collaborating."

**Engineering effort:** 3-4 days
- Handoff arrow component between pipeline nodes (1 day)
- Incoming context panel showing what each agent received (1 day)
- Impact metrics bar accumulating stats per step (1 day)
- Integration into demo page and execution detail page (0.5-1 day)

**Startup impact:** High. Makes the multi-agent architecture visible. Investors can see the collaboration, not just the messages.

**What to build (pick ONE — handoff arrows):**
- Replace static connector lines in ExecutionGraph with animated arrows
- Arrow shows context count (e.g., "2 files" passed from Builder to Reviewer)
- Color gradient from source agent color to target agent color

---

## #4: Personal Dashboard Stats

**Why:** The current dashboard shows nothing personal. Adding "Your Tasks: 12" with a quality score creates identity investment — the #1 retention hook.

**User impact:** 100% of returning users. Transforms generic dashboard into personal control center.

**Engineering effort:** 1.5 days
- Backend stats aggregation endpoint (0.5 day)
- Frontend dashboard stats component (0.5 day)
- Integrate into landing page (0.5 day)

**Startup impact:** Medium-High. Personal stats are the foundation for all retention features (achievements, streaks, comparisons). Without a personal dashboard, nothing else works.

**What to build:**
- `GET /stats/user` — backend aggregation: tasks completed, quality score, review pass rate, time saved, bugs found
- Dashboard shows 5 metric cards with user's lifetime stats
- Empty state → "Complete your first task to see your stats"

---

## #5: Achievement System (Core)

**Why:** Achievements create the "next reward visible" hook — the #3 retention hook. The minimum viable version is 6 seeded achievements with a progress display.

**User impact:** Users who complete multiple tasks. Creates "I'm 3/10 of the way to the next achievement" pull.

**Engineering effort:** 4-5 days
- Database migration (achievements + user_achievements tables) (0.5 day)
- Achievement definitions (16 seeded) (0.5 day)
- Achievement checking engine (backend) (1 day)
- Achievement endpoint + integration with task completion (0.5 day)
- Achievement page + badge components (1 day)
- Achievement toast notification (0.5 day)

**Startup impact:** Medium. Achievements are a retention feature, and retention is the #2 risk. But the other features (#1-#4) must exist first — achievements amplify retention but don't create it.

**What to build (minimum):**
- 6 seeded achievements: First Team, First Task, First Review, Bug Hunter, 10 Tasks, Week Warrior
- Achievement unlocked toast on task completion
- `/achievements` page showing earned + next progress
- Achievement progress on dashboard

---

## Summary

| # | Improvement | Days | User Impact | Startup Impact | ROI Rank |
|---|-------------|------|-------------|----------------|----------|
| 1 | Demo Comparison Layer | 2-3 | 100% of viewers | Value proposition | **#1** |
| 2 | Run Again + Saved Teams | 1.5 | 100% of completers | First retention hook | **#2** |
| 3 | Collaboration Visibility | 3-4 | 100% of viewers | Differentiation visible | **#3** |
| 4 | Personal Dashboard Stats | 1.5 | 100% of returners | Identity investment | **#4** |
| 5 | Achievement System (Core) | 4-5 | 50% of multi-taskers | Amplifies retention | **#5** |

**Total effort:** 12.5-17 days within a 30-day window.

## Order of Execution

```
Week 1: Demo Comparison Layer (#1) + Run Again/Saved Teams (#2)
        → Solves the existential question + creates first retention hook

Week 2: Personal Dashboard Stats (#4)
        → Foundation for all retention features

Week 3: Collaboration Visibility (#3) — handoff arrows
        → Makes differentiation visible

Week 4: Achievement System Core (#5)
        → Amplifies retention
```

## What NOT to Build (Deferred)

| Feature | Why Not Now |
|---------|-------------|
| Compare Teams full page | Requires 2+ teams + 2+ executions → low initial usage |
| Execution Replay | Users haven't watched executions yet → premature |
| Model Comparison | Same as Compare Teams — premature |
| Streak tracking | Requires daily_activity table + cron → infrastructure |
| Sharing/viral | Requires auth system → premature |
| Mobile responsive | Low traffic on mobile for dev tool |
| Dark/light mode | Dev tool → dark mode is assumed |
