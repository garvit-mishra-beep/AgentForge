# User Obsession Plan

## Top 3 Personas

---

### Persona 1: The Solo Founder

**Name:** Alex
**Role:** Technical founder building an MVP
**Age:** 28-40
**Stack:** TypeScript, Python, Postgres
**Budget:** Personal savings, $0-$100/mo for tools

**Biggest pain:**
"No one reviews my code. I ship bugs I didn't catch because I'm the only engineer."

**Current workflow:**
1. Write code or use ChatGPT to generate it
2. Manually test the happy path
3. Ship and hope
4. Find bugs in production
5. Fix and repeat

**Why AgentForge helps:**
AgentForge acts as a virtual team. The Reviewer catches bugs Alex would miss. The Tester generates edge case tests. Alex gets code review without hiring a second engineer.

**Why AgentForge doesn't help enough yet:**
- Setup is too slow: Alex needs to create a team, pick models, write a task. By the time the pipeline runs, Alex could have manually reviewed the code.
- No integration: Alex works in VS Code. Opening a browser, pasting code, and waiting 30 seconds is friction.
- No trust: Alex doesn't know if the Reviewer is better than their own review.

**The fastest path to making Alex obsessed:**

**Step 1: Zero-setup review.** Alex can paste code and get results in under 30 seconds. No team creation. No model selection. Just paste → review.

**Step 2: Show Alex something they missed.** The Reviewer must find a bug Alex didn't see on their first try. This is the "holy shit" moment. If the first review catches a real bug, Alex is hooked.

**Step 3: Compare to Alex's own review.** "You caught 2 issues. AgentForge caught 3 additional issues you missed." This creates trust through comparison.

**Step 4: Integrate into Alex's workflow.** CLI tool or VS Code extension to submit code without leaving the editor. After paste-and-review works, reduce friction to zero.

**Obsession trigger:** "AgentForge caught a bug I would have shipped to production."

**Retention loop:** Every time Alex writes code, they submit it to AgentForge before shipping. The product becomes part of their deployment checklist.

---

### Persona 2: The Quality-Conscious Tech Lead

**Name:** Jordan
**Role:** Tech lead at a 10-50 person startup
**Age:** 32-45
**Stack:** Anything, but responsible for code quality
**Budget:** $200-$500/mo for team tools

**Biggest pain:**
"My juniors use ChatGPT to generate code. They don't review it properly. I spend my time catching their mistakes instead of building architecture."

**Current workflow:**
1. Junior developer generates code with ChatGPT
2. Junior opens a PR
3. Jordan reviews the PR, finds issues
4. Junior fixes, Jordan re-reviews
5. Cycle repeats 5-10 times per PR

**Why AgentForge helps:**
AgentForge can pre-review AI-generated PRs before Jordan sees them. The Reviewer catches common issues. The Tester generates tests. Jordan gets a pre-filtered PR with issues already flagged.

**Why AgentForge doesn't help enough yet:**
- No CI/CD integration: Jordan needs AgentForge to automatically review PRs, not require manual paste.
- No team collaboration: Jordan needs to see reviews across multiple PRs from multiple juniors.
- No trust calibration: Jordan doesn't know if AgentForge's review is comprehensive enough to trust.

**The fastest path to making Jordan obsessed:**

**Step 1: PR review endpoint.** Jordan can paste a PR diff and get a review. No team setup needed. Just paste → results.

**Step 2: Show Jordan the issues AgentForge found that they would have found anyway.** Build trust by demonstrating coverage. "AgentForge flagged 5 issues — you found 4 of them in your review. You missed 1."

**Step 3: Show Jordan issues they missed.** The first time AgentForge catches something Jordan's manual review missed, Jordan becomes a believer.

**Step 4: Batch review.** Jordan can submit 5 PRs at once and get a summary of issues across all of them.

**Obsession trigger:** "AgentForge caught a bug I missed in code review. My team is shipping better code."

**Retention loop:** Jordan requires all PRs to pass AgentForge review before Jordan's manual review. The tool becomes part of the deployment pipeline.

---

### Persona 3: The AI Power User

**Name:** Morgan
**Role:** Senior developer, early adopter of AI tools
**Age:** 25-38
**Stack:** Anything, but spends $50-100/mo on AI tools
**Budget:** Personal, $50-$200/mo

**Biggest pain:**
"I use ChatGPT and Claude every day. They're great at generating code that *looks* right but has subtle bugs. I've been burned enough to be skeptical."

**Current workflow:**
1. Generate code with ChatGPT or Claude
2. Manually review the output (takes 5-15 minutes)
3. Fix issues found during review
4. Sometimes miss issues and discover them in production

**Why AgentForge helps:**
AgentForge automates the review step. Morgan generates code with their preferred tool, pastes it into AgentForge, and gets a structured review with bugs flagged, tests generated, and security issues identified.

**Why AgentForge doesn't help enough yet:**
- Too slow: Morgan can manually review code faster than setting up a team and waiting 30 seconds.
- No trust: Morgan doesn't know if AgentForge's review is better than their own.
- No ChatGPT integration: Morgan wants a button in ChatGPT saying "Review this with AgentForge."

**The fastest path to making Morgan obsessed:**

**Step 1: Instant review.** Paste code → see results in <15 seconds. Faster than manual review.

**Step 2: Show Morgan something they missed.** The Reviewer must catch a genuine issue — a real bug, not a style nitpick. Morgan needs to say "I wouldn't have caught that."

**Step 3: Generate tests Morgan wouldn't have written.** The Tester produces edge case tests that Morgan didn't consider. This demonstrates the tool is doing work Morgan would have skipped.

**Step 4: Browser extension / bookmarklet.** Morgan can right-click code in ChatGPT and "Review with AgentForge." Zero friction.

**Obsession trigger:** "AgentForge found a bug in code I was about to ship. It paid for itself today."

**Retention loop:** Morgan runs every ChatGPT output through AgentForge before committing. The tool becomes a habit.

---

## Summary: The Fastest Path to Obsession

All three personas share a common path:

1. **Zero-setup entry** — Paste code, get review. No teams, no models, no configuration.
2. **First-review "holy shit" moment** — The Reviewer must catch something the user missed. This is non-negotiable.
3. **Prove the comparison** — "You caught X issues. AgentForge caught Y additional issues you missed."
4. **Reduce friction** — Browser extension, CLI, API. Make it as easy as pasting.
5. **Become a habit** — The user naturally submits code to AgentForge before every deploy.

**Priority persona:** Persona 1 (Solo Founder) — highest pain, most likely to try something new, least likely to have alternatives (no team to review code).

## What to Build First

1. **Quick Review** — Text area on landing page. Paste code. Click "Review." Gets results in <30 seconds. No account needed, no setup.
2. **Comparison Summary** — After review: "You caught X issues. AgentForge caught Y. Here's what you missed."
3. **Default models** — No model selector. Pre-configured default pipeline (Builder + Reviewer + Tester) that just works.
