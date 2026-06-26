# Pricing — AgentForge

**Last Updated:** June 2026
**Currency:** USD

---

## Plans

| Feature | Free | Pro ($29/mo) | Team ($99/mo) | Enterprise (Custom) |
|---------|------|-------------|---------------|---------------------|
| Projects | 3 | Unlimited | Unlimited | Unlimited |
| Tasks/day | 5 | 100 | 500 | Custom |
| Task history retention | 7 days | 1 year | 1 year | Indefinite |
| Models available | GPT-4o-mini, Claude Haiku, Gemini Flash | All models | All models | All models + custom |
| Seats | 1 | 1 | 5 | Custom |
| Priority support | Community (GitHub) | Email (24hr response) | Email + Slack (4hr response) | Dedicated support, SLA |
| WebSocket streaming | ✅ | ✅ | ✅ | ✅ |
| All 6 agent roles | ✅ | ✅ | ✅ | ✅ |
| Agent memory (pgvector) | Last 30 days | Full retention | Full retention | Full retention |
| Token cost tracking | ❌ | ✅ | ✅ | ✅ |
| Usage dashboard | ❌ | ✅ | ✅ | ✅ |
| Team analytics | ❌ | ❌ | ✅ | ✅ |
| Admin controls | ❌ | ❌ | ✅ | ✅ |
| SAML/SSO | ❌ | ❌ | ❌ | ✅ |
| Audit logs | ❌ | ❌ | ❌ | ✅ |
| On-premise deployment | ❌ | ❌ | ❌ | ✅ |
| SLA guarantee | ❌ | ❌ | 99.5% uptime | 99.9% uptime |

---

## AI Cost Passthrough

AI provider API costs are passed through to the user with a 20% margin. Each task records the exact token usage (input + output) per agent step and computes the cost based on the model's pricing.

### Pricing Per Model

| Model | Cost/1K Input | Cost/1K Output |
|-------|--------------|---------------|
| GPT-4o-mini | $0.00015 | $0.00060 |
| Claude Haiku 4.5 | $0.00025 | $0.00125 |
| Gemini 1.5 Flash | $0.000075 | $0.00030 |
| Qwen-72B-Instruct | $0.00050 | $0.00100 |
| Gemini 1.5 Pro | $0.00125 | $0.00500 |
| GPT-4o | $0.00250 | $0.01000 |
| Claude Sonnet 4.6 | $0.00300 | $0.01500 |

### Example Cost: "Build JWT Auth" Task

| Step | Model | Input Tokens | Output Tokens | Cost |
|------|-------|-------------|--------------|------|
| 1. Team Lead (plan) | Gemini 1.5 Pro | 4,500 | 1,200 | $0.00713 |
| 2. Backend Engineer | Claude Sonnet 4.6 | 3,200 | 2,800 | $0.03960 |
| 3. Reviewer | GPT-4o | 2,100 | 800 | $0.00845 |
| 4. Backend (revision) | Claude Sonnet 4.6 | 1,500 | 900 | $0.01305 |
| 5. QA Engineer | Qwen-72B | 2,800 | 1,200 | $0.00170 |
| 6. Security Engineer | GPT-4o | 1,200 | 600 | $0.00450 |
| 7. Team Lead (deliver) | Gemini 1.5 Pro | 1,000 | 500 | $0.00163 |
| **Total** | | **16,300** | **8,000** | **$0.076** |

After 20% margin: **$0.091** per task.

### Free Tier Allowance

**100,000 tokens/month** (input + output, combined) across GPT-4o-mini, Claude Haiku, and Gemini Flash models only.

| Monthly Token Usage | Free | Pro | Team |
|-------------------|------|-----|------|
| 0 – 100K | Included | Included | Included |
| 100K – 1M | N/A | $0.50/100K tokens | $0.50/100K tokens |
| 1M – 10M | N/A | $0.40/100K tokens | $0.40/100K tokens |
| 10M+ | N/A | $0.30/100K tokens | $0.30/100K tokens |

---

## Usage Dashboard

The usage dashboard (available on Pro and Team plans) shows:

- **Per-project cost** — Total AI costs broken down by project
- **Per-model cost** — Which models are driving costs (bar chart)
- **Per-task cost** — Individual task cost breakdown
- **Token usage trends** — Daily/weekly/monthly token consumption
- **Cost by role** — Which agent roles consume the most tokens

---

## Billing

- Monthly billing only (annual plans coming in V1.5)
- Credits cards accepted: Visa, Mastercard, Amex (via Stripe)
- Invoices available in dashboard (Pro and Team only)
- Overages billed at end of billing cycle
- No refunds for partial months
- Downgrade takes effect at next billing cycle
- Account deletion: close account, final invoice, data retained for 30 days (grace period for reactivation)

---

## Enterprise Pricing

Enterprise pricing is custom based on:
- Number of seats
- Task volume
- AI model cost passthrough (at cost, no margin)
- Support SLA (response time)
- SSO implementation
- On-premise deployment support

Contact: enterprise@agentforge.dev
