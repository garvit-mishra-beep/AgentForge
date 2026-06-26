# Quick Review — Product Requirements Document

**Status:** Draft v1
**Owner:** CPO
**Target Users:** Solo Founders, AI Power Users, first-time visitors
**Value Proposition:** "Get an automated code review in 10 seconds. No setup. No configuration."

---

## 1. Problem Statement

Users land on AgentForge and see an empty dashboard. To get value, they must:
1. Create a team (name, description)
2. Assign team members (Lead, Builder, Reviewer, Tester)
3. Select models for each role (10+ options with no guidance)
4. Write a task description
5. Wait 30-60 seconds for execution

This is 2-3 minutes of setup before any value. Most users leave before completing step 1.

**The existential question:** "Why not just paste this prompt into ChatGPT and get an answer in 3 seconds?"

---

## 2. User Story

> As a developer who just generated code with ChatGPT,
> I want to paste that code into AgentForge and get a review immediately,
> So that I know if there are bugs, security issues, or missing tests before I ship.

**No account required. No team creation. No model selection. Paste. Click. Results.**

---

## 3. Success Metrics

| Metric | Target | Why |
|--------|--------|-----|
| Time to first review | <10 seconds from page load | Every second of delay loses users |
| % visitors who paste code | >30% | Measures whether the CTA is compelling |
| % pasted reviews completed | >80% | Measures whether results are fast enough |
| % users who run a second review | >40% | Measures whether the first review proved value |
| Bounce rate reduction | -50% vs current landing page | The ultimate measure |

---

## 4. UX Flow

### Screen 1: Landing State

```
┌──────────────────────────────────────────────────────┐
│  [Logo]                     [Sign In] [Get Started]  │
│                                                        │
│  ┌────────────────────────────────────────────────┐   │
│  │                                                │   │
│  │    Paste your AI-generated code here           │   │
│  │                                                │   │
│  │    paste code from ChatGPT, Claude, or         │   │
│  │    any AI coding tool...                       │   │
│  │                                                │   │
│  │                                                │   │
│  │                                                │   │
│  │         [Review My Code →]                     │   │
│  │                                                │   │
│  └────────────────────────────────────────────────┘   │
│                                                        │
│  Or try an example →                                   │
│    "JWT auth middleware"  "REST API endpoint"          │
│    "React component"     "SQL migration"               │
│                                                        │
│  ┌────────────────────────────────────────────────┐   │
│  │ How it works:                                  │   │
│  │                                                │   │
│  │ ① Paste code  →  ② AI review  →  ③ Get results│   │
│  │                                                │   │
│  │ Catches bugs, security issues, missing tests   │   │
│  │ that a single AI model would miss.             │   │
│  └────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

**Rules:**
- Text area auto-grows to 60vh on focus
- Character limit: 50,000 characters (catches 99% of real cases)
- No syntax highlighting — simplicity wins. Plain monospace text.
- Example buttons populate the text area with realistic AI-generated code
- "Review My Code" button disabled until content is detected

### Screen 2: Loading State

```
┌──────────────────────────────────────────────────────┐
│  Reviewing your code...                              │
│                                                        │
│  ┌────────────────────────────────────────────────┐   │
│  │  ■■■■■■■■■■■■■■■□□□□□□□  65%                   │   │
│  │                                                │   │
│  │  • Analyzing code structure...  ✅             │   │
│  │  • Checking for bugs...          ⌛             │   │
│  │  • Generating test cases...     ⬜             │   │
│  │  • Security scan...             ⬜             │   │
│  └────────────────────────────────────────────────┘   │
│                                                        │
│  Expected time: ~15 seconds                            │
└──────────────────────────────────────────────────────┘
```

**Rules:**
- Show real-time progress bars for each stage
- Never show model names, token counts, or pipeline architecture
- If >30 seconds: show "This is taking longer than usual. We'll notify you when done."
- Allow user to leave and come back (email notification — future)

### Screen 3: Results State

```
┌──────────────────────────────────────────────────────┐
│  Review Complete — 4 Issues Found                     │
│                                                        │
│  ┌───────────────────┐  ┌───────────────────────┐    │
│  │ What ChatGPT       │  │ AgentForge caught:    │    │
│  │ would have shipped │  │                       │    │
│  │                    │  │ 🔴 Hardcoded API key  │    │
│  │ ✅ Looks clean     │  │ 🔴 No input validation│    │
│  │ ❌ Hardcoded key   │  │ 🔴 SQL injection risk │    │
│  │ ❌ No validation   │  │ 🟢 12 tests generated │    │
│  │ ❌ SQL injection   │  │                       │    │
│  │ ❌ 0 tests         │  │                       │    │
│  └───────────────────┘  └───────────────────────┘    │
│                                                        │
│  Without AgentForge: would have shipped 3 bugs + 0 t. │
│  With AgentForge: caught 3 bugs, generated 12 tests   │
│                                                        │
│  ┌────────────────────────────────────────────────┐   │
│  │  Issues Found                                    │   │
│  │                                                  │   │
│  │  🔴 Hardcoded API key (Line 47)                  │   │
│  │     └─ Uses os.environ["API_KEY"] directly       │   │
│  │        Fix: Use environment variable validator    │   │
│  │                                                  │   │
│  │  🔴 No input validation (Line 12-34)             │   │
│  │     └─ SQL query uses f-string interpolation     │   │
│  │        Fix: Use parameterized queries             │   │
│  │                                                  │   │
│  │  🔴 SQL injection risk (Line 28)                  │   │
│  │     └─ User input concatenated into query         │   │
│  │        Fix: Use query builder or ORM              │   │
│  │                                                  │   │
│  │  🟢 Generated 12 test cases                       │   │
│  │     └─ Edge cases: null input, empty string,      │   │
│  │        SQL injection, XSS, rate limiting          │   │
│  └────────────────────────────────────────────────┘   │
│                                                        │
│  [Review Another →]    [Fix Issues →]                  │
│                                                        │
│  🔒 Sign up to save this review and track your stats   │
└──────────────────────────────────────────────────────┘
```

**Rules:**
- Comparison panel is the **first** thing the user sees — above the fold
- Issues are ordered by severity (Security > Bugs > Missing Tests)
- Each issue shows: severity icon, title, line number, description, fix suggestion
- Generated tests section is positive reinforcement ("look what we built for you")
- "Review Another" is primary CTA — creates repeat loop
- "Fix Issues" is secondary — could open integration (future)
- Sign up prompt is shown but NOT blocking — user can review as many times as they want without an account

---

## 5. Backend Requirements

### New Route: `POST /api/review`

**Request:**
```json
{
  "code": "string (max 50,000 chars)",
  "language": "string (optional, auto-detect)"
}
```

**Response:**
```json
{
  "review_id": "uuid",
  "status": "complete",
  "duration_ms": 15230,
  "comparison": {
    "bugs_single_would_miss": 3,
    "tests_generated": 12,
    "security_issues_found": 1
  },
  "issues": [
    {
      "severity": "critical",
      "category": "security",
      "title": "Hardcoded API key",
      "line": 47,
      "description": "Uses os.environ[\"API_KEY\"] directly",
      "suggestion": "Use environment variable validator like python-decouple"
    }
  ],
  "tests": [
    {
      "description": "Test empty string input",
      "code": "assert validate_input(\"\") == False"
    }
  ]
}
```

**Pipeline Configuration (invisible to user):**
- Builder: qwen2.5-coder:7b (analyzes the code, prepares context)
- Reviewer: phi4-mini (identifies bugs, security issues, style problems)
- Tester: qwen3.5:4b (generates test cases)
- All defaults — no user configuration

**Performance target:**
- P95 response time: <25 seconds
- P50 response time: <15 seconds
- If models are busy: queue with position indicator

---

## 6. Frontend Components

### QuickReviewTextarea
- Full-width monospace text area
- Placeholder text: "Paste your AI-generated code here..."
- Auto-grows on focus (from 200px to 60vh)
- Character counter at bottom-right
- "Review My Code" button — blue, prominent, right-aligned
- Example buttons below: "JWT auth middleware" | "REST API endpoint" | "React component" | "SQL migration"
- These populate the text area with realistic code that has known bugs

### QuickReviewProgress
- Animated progress bar (segmented into 4 stages)
- Stage labels: "Analyzing code...", "Checking for bugs...", "Generating tests...", "Security scan..."
- Checkmarks for completed stages
- Spinner for current stage
- Elapsed time counter
- Cancellation button (X in corner)

### QuickReviewResults (3 panels)
1. **Comparison Panel** — Side-by-side: "What single AI would ship" vs "What AgentForge caught"
2. **Issues Panel** — Expandable list of issues sorted by severity
3. **Tests Panel** — Each test case in a code block
4. **Action Bar** — "Review Another" (primary), "Fix Issues" (secondary, disabled for now)

### QuickReviewHeader
- Logo (left)
- "Sign In" link (right) — only shown if user is not authenticated
- No navigation, no sidebar, no complexity

---

## 7. Copy Requirements

The entire experience must be understandable at a glance.

| Element | Copy | Rationale |
|---------|------|-----------|
| Title above text area | *(none)* | The text area IS the title. Don't add words. |
| Button | "Review My Code" | Personal. Action-oriented. Not "Submit." |
| Example label | "Try an example →" | Low-commitment invitation |
| Comparison header | "What ChatGPT would have shipped" | Direct. Memorable. Provable. |
| Comparison subtext | "Without AgentForge: would have shipped X bugs + 0 tests. With AgentForge: caught X bugs, generated Y tests." | Proves value in one sentence |
| Issue severity | 🔴 Critical / 🟠 Major / 🟢 Improvement | One emoji is worth 100 words |
| Sign up prompt | "🔒 Sign up to save this review and track your stats" | Value-focused, not fear-based |
| How it works | "① Paste code ② AI review ③ Get results" | Three steps, no jargon |

**Tone:** Direct. Confident. Never defensive. Never technical.

---

## 8. Animation Requirements

- Text area: subtle pulse on load to draw attention
- "Review My Code" button: subtle gradient shimmer (only on first visit)
- Progress bar: smooth animated segments (not blocky)
- Results: staggered fade-in (comparison → issues → tests)
- Issue expansion: smooth height transition (0.2s ease)
- "Review Another" click: text area clears, cursor focuses, slight yellow highlight on text area

---

## 9. Acceptance Criteria

- [ ] Unauthenticated user can paste code and get a review
- [ ] Review completes in <30 seconds (P95)
- [ ] Comparison panel shows "what ChatGPT would have shipped" vs "what AgentForge caught"
- [ ] Issues are sorted by severity (Security > Bugs > Missing Tests)
- [ ] Each issue shows severity, title, line number, description, and fix suggestion
- [ ] Generated tests are displayed with code blocks
- [ ] Example buttons populate the text area with realistic code
- [ ] "Review Another" clears the UI and resets to text area
- [ ] Sign up prompt is non-blocking
- [ ] No model names, token counts, or pipeline details visible anywhere
- [ ] Works on mobile (responsive text area, stacked comparison on small screens)
- [ ] Character limit (50K) with clear error message if exceeded
- [ ] Language auto-detection (Python, JavaScript, TypeScript, Go, Rust, SQL)

---

## 10. What NOT to Build

| Feature | Rejection Reason |
|---------|-----------------|
| Account creation gate | The #1 barrier. Quick Review works without an account. |
| Model selector | Users should not know models exist. |
| Team creation | Irrelevant to the value proposition. |
| Token counts | Meaningless to users. |
| Syntax highlighting | Adds latency, no value for review. |
| Edit-in-place | Users paste to review, not to edit. |
| Save history without account | Require sign up for persistence. |
| Share reviews | Premature social feature. |
| Export to GitHub | Enterprise feature. |

---

## 11. Edge Cases

| Case | Handling |
|------|----------|
| Empty paste | Button disabled. Text area shakes slightly. |
| Very short code (<10 lines) | Review still runs. Comparison may show "no significant issues found." |
| Very large code (>50K chars) | Clear error: "Code is too long. Maximum 50,000 characters." |
| Non-code content | Language detection fails - shows "Language not detected. We'll do our best." |
| Server error | Shows "Something went wrong. Try again." with retry button. No stack traces. |
| Timeout (>45 seconds) | Shows "This is taking longer than expected. We'll notify you." (future: email) |
| Rate limit | Show friendly: "You've done 10 reviews recently. Take a 30-second break." |
| All models busy | Queue position: "You're #3 in line. Estimated wait: 45 seconds." |
