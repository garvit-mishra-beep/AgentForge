# First-Time User Journey

**Date:** 2026-06-26
**Author:** Principal UX Researcher

---

## The Journey (Current State)

### Step 1: Arrival at Mission Control

**What the user sees:** A dark-themed dashboard with "Mission Control" at the top, metrics showing zeros, and an empty state card that says "Your AI Command Center" with options to "Create Your First Team" or "Watch Demo."

**What the user thinks:**
- *"What is this?"*
- *"Why would I use this instead of ChatGPT?"*
- *"What does 'AI Command Center' mean?"*

**Gap:** The value proposition is missing. The term "Mission Control" is a metaphor that means nothing to a new user. The empty state describes an interface, not a benefit.

**Recommendation:** Replace the empty state header with a benefit-driven line: "Build better code with specialized AI teams." Add a one-sentence subhead: "AgentForge assembles a team of AI agents that plan, build, review, test, and deliver — catching bugs that a single model would miss."

---

### Step 2: Deciding What to Do

**Choices available:**
- "Create Your First Team" (primary CTA)
- "Watch Demo" (secondary CTA)
- Navigate sidebar to any of 8 sections

**What the user thinks:**
- *"I should understand what this is before I create anything."*
- *"Let me watch the demo first."*

**Observation:** The demo is the correct first step, but it's a secondary button. The primary CTA asks users to commit before understanding.

**Recommendation:** Swap the button hierarchy. Make "Watch Demo" the primary CTA for first-time users. Only show "Create Your First Team" as primary for returning users.

---

### Step 3: Watching the Demo

**What the user sees:** A ~12-second animated sequence showing 5 messages from 4 agents (Lead plans -> Builder codes -> Reviewer reviews -> Tester tests -> Lead delivers). The demo shows real code, real test results, and a final delivery summary.

**What the user thinks:**
- *"That's cool, but... why is 4 agents better than 1?"*
- *"The reviewer found 2 minor issues — would ChatGPT have missed those?"*
- *"12 seconds seems slow compared to asking ChatGPT the same thing."*

**Gap:** The demo shows *what* happens (the mechanism) without showing *why it matters* (the value). The advantage of specialized agents catching each other's mistakes is shown, but not called out explicitly.

**Recommendation:** Add callout annotations to the demo:
- When the reviewer appears: "The reviewer caught 2 issues the builder missed."
- When the tester appears: "The tester verified 5 test cases with 87% coverage."
- At the end: "One model would have shipped those bugs. Four models caught them."

Add a comparison overlay option: "Show me what a single model would have generated."

---

### Step 4: Creating a Team

**What the user sees:** A form with 3 template cards showing role badges, a team name input, and a Create button.

**What the user does:**
1. Clicks "Software Engineering" template
2. Sees name auto-fill to "Software Engineering"
3. Clicks "Create Team"
4. Navigates to team detail page

**What the user thinks:**
- *"Wait, the template showed Lead, Builder, Reviewer, Tester with specific models — but none of that was applied."*
- *"I just created an empty team. Now I need to assign all 4 roles manually?"*

**Gap:** This is the highest-friction moment in the entire journey. Templates show member configurations but only apply the name. Users feel misled.

**Recommendation:** Fix templates to pre-populate members. Alternatively, remove role badges from template cards. Either way, the current state is broken UX.

---

### Step 5: Assigning Roles and Models

**What the user sees:** 4 role cards with model selector buttons. An organizational chart showing the team structure.

**What the user does:**
1. Clicks a role card (e.g., Builder)
2. Reviews the 10 model options with cryptic names like "qwen2.5-coder:7b"
3. Hovers between options, unsure which to pick
4. Makes a choice based on model size (bigger = better?)

**What the user thinks:**
- *"I have no idea which model to pick for which role."*
- *"Is a 7B model better than a 3B model for code generation?"*
- *"Why would I pick phi4-mini for reviewing and qwen2.5-coder for building?"*

**Gap:** Model selection requires expertise that new users don't have. The tags ("Fast", "Lightweight", "Best for code") help but don't provide clear guidance.

**Recommendation:** Add a "Recommended" badge to the suggested model for each role. Add tooltips explaining why each model fits each role (e.g., "Qwen2.5-Coder is fine-tuned for code generation — best choice for the Builder role"). Consider reducing to 5 options instead of 10.

---

### Step 6: First Task

**What the user sees:** A form with team selector, title input with example suggestions, and optional description.

**What the user does:**
1. Selects their newly created team
2. Clicks a task example ("Build JWT Authentication in FastAPI")
3. Clicks "Start Task"

**What the user thinks:**
- *"Will this actually work?"*
- *"How long will it take?"*
- *"What happens if it fails?"*

**Gap:** The user is about to commit to an asynchronous process with unknown duration and unknown success probability.

**Recommendation:** Add an expected time indicator (e.g., "Estimated: ~30 seconds"). Add a "What to expect" dropdown: "Your team will plan, build, review, test, and deliver. You'll see each step in real-time."

---

### Step 7: Watching the Execution

**What the user sees:** A real-time updating page with:
- 4 metric cards (Messages, Tokens, Duration, Status)
- An execution pipeline graph showing progress
- A tabbed area with Activity Stream, Timeline, and Output

**What the user thinks (if it works):**
- *"Messages are appearing! It's working!"*
- *"Whoa, the reviewer found something the builder missed."*
- *"This is actually pretty cool."*

**What the user thinks (if it fails):**
- *"It just says 'error' — what went wrong?"*
- *"Can I retry? Do I need to create a new task?"*

**Gap:** The success case is the demo-friendly path. The failure case has no retry mechanism and limited diagnostic information.

**Recommendation:** Add a retry button for failed tasks. Add a "What went wrong" expandable section with the error message in plain language. Add a "Try a simpler task" suggestion for persistent failures.

---

### Step 8: After First Execution

**What the user sees:** A completed task with final output, metrics, and the option to "Build Your Team" or "Back to Mission Control."

**What the user thinks:**
- *"That was interesting. Now what?"*
- *"Is there anything else to do here?"*
- *"I don't think I'd use this again."*

**Gap:** The post-execution experience has no call-to-action that creates a habit loop. No "Run another task" with pre-filled settings. No "Compare with different team configurations." No "Share this result."

**Recommendation:** Add a post-execution CTA: "Run this task again with a different model for the Builder role to compare results." Add a "Share execution replay" link. Add a "Create a new task based on this result" button.

---

## Journey Map Summary

| Step | Current State | User Feeling | Fix Priority |
|------|--------------|--------------|--------------|
| 1. Landing | Abstract headline, no value prop | Confused | P0 |
| 2. Decision | Demo is secondary button | Hesitant | P1 |
| 3. Demo | Shows mechanism, not value | Impressed but unconvinced | P0 |
| 4. Create team | Templates don't populate | Misled, frustrated | P0 |
| 5. Assign models | No guidance on choices | Overwhelmed | P1 |
| 6. First task | No expectations set | Anxious | P1 |
| 7. Execution | No retry on failure | Stuck | P1 |
| 8. Post-execution | No reason to return | Done, leaving | P0 |

---

## Critical Path to Fix

The 3 highest-impact changes that would transform the first-time experience:

1. **Fix templates to populate members.** This removes the #1 frustration and saves users 4 clicks.

2. **Add "why this matters" to the demo.** Call out reviewer catching bugs, tester finding edge cases. Make the differentiation visible.

3. **Create a post-execution habit loop.** Give users a reason to come back — compare results, share executions, iterate on teams.
