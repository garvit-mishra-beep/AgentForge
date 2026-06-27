# Data Privacy Policy — AgentForge

**Last Updated:** June 1, 2026

---

## 1. Data We Collect and Store

### Task Data
- Task prompts and descriptions (submitted by users)
- Agent outputs (generated code, text, JSON, configuration files)
- Task metadata (model used, token count, latency, timestamps, cost)
- Task steps, messages, and output files

### Account Data
- Name and email address (provided during sign-up/authentication)
- Account tier and billing information (processed by Stripe — AgentForge does not store full payment details)
- User preferences (display name, avatar URL, theme preference)

### Project and Team Configuration
- Project names and descriptions
- Team composition (role-to-model assignments)
- Agent assignments and any custom system prompt overrides

### Technical Data
- Application logs (request paths, status codes, error messages — no PII or secrets)
- Usage metrics (page views, feature usage, session duration via PostHog)

---

## 2. Data We Do NOT Store

| Data Type | Why NOT stored |
|-----------|---------------|
| Plaintext AI provider API keys | Encrypted at rest with AES-256; only decrypted in memory at execution time |
| Raw WebSocket frame payloads after session end | Ephemeral — published to Redis pub/sub and delivered to browser; not persisted after session closes |
| Browser fingerprints or behavioral analytics | Not collected beyond basic PostHog page views |
| Passwords | Hashed using bcrypt in our database; plaintext passwords are never stored |
| Full credit card numbers | Stripe processes all payments; AgentForge stores only a payment method reference token |

---

## 3. Data Retention

| Data Category | Free Tier | Pro Tier | Team Tier | Enterprise |
|--------------|-----------|---------|-----------|------------|
| Task inputs and outputs | 7 days | 1 year | 1 year | Indefinite (configurable) |
| Agent memories (pgvector) | 30 days | 1 year | 1 year | Indefinite (configurable) |
| Account data | Duration of account + 30 days | Duration of account + 30 days | Duration of account + 30 days | Duration of account + 30 days |
| Logs | 30 days | 90 days | 90 days | 1 year |
| Usage analytics | 90 days (aggregated) | 90 days (aggregated) | 90 days (aggregated) | 90 days (aggregated) |

**Deletion after account closure:** All user data is permanently deleted 30 days after account closure (grace period for reactivation). After 30 days, data is irrecoverable.

---

## 4. GDPR Compliance

### Right to Erasure ("Right to be Forgotten")

You can request deletion of all your data:

```
DELETE /api/v1/user/data
Authorization: Bearer <jwt_access_token>
```

This will:
1. Delete all projects, teams, tasks, and outputs associated with your account
2. Delete all agent memories associated with your projects
3. Anonymize logs (replace user_id with a random hash)
4. Delete user account from database
5. Send confirmation email

**Processing time:** Within 30 days of request.

### Data Portability

You can export all your data:

```
GET /api/v1/user/export
Authorization: Bearer <jwt_access_token>
```

Response is a JSON file containing:
- All projects and their configurations
- All teams and agent assignments
- All tasks with their steps, messages, and outputs
- All agent memories (vector embeddings excluded — text content included)

### Lawful Basis for Processing

| Processing Activity | Lawful Basis |
|--------------------|-------------|
| Task execution (processing prompts and generating outputs) | Performance of a contract (providing the Service) |
| Account management (name, email storage) | Performance of a contract |
| Usage analytics | Legitimate interest (improving the Service) |
| Email notifications (product updates, billing) | Consent (opt-out available) |
| Security monitoring (log analysis) | Legitimate interest (service security) |

---

## 5. India DPDP Act 2023 Compliance

AgentForge complies with the Digital Personal Data Protection Act, 2023 (India) for users who are data principals under the Act:

- **Consent management:** Consent for data processing is obtained at account creation and can be withdrawn at any time via Settings → Privacy
- **Data fiduciary:** AgentForge is the data fiduciary for user-provided task data
- **Data processor:** AI model providers (OpenAI, Anthropic, Google, Alibaba) are data processors
- **Grievance officer:** privacy@agentforge.dev (response within 24 hours)
- **Data localisation:** User data is primarily stored in US-based data centers (AWS us-east-1 via Railway). Users requiring Indian data residency should contact enterprise@agentforge.dev

---

## 6. Data Deletion Flow

```
User: Settings → "Delete Account"
    │
    ▼
System: "Are you sure?" confirmation dialog
    │
    ▼
System: 30-day grace period begins
    │  - Account is deactivated (cannot log in)
    │  - Data is preserved but inaccessible
    │  - User can reactivate by contacting support
    │
    ▼
After 30 days:
    ├── Delete all tasks, steps, messages, outputs
    ├── Delete all teams, agents, project configurations
    ├── Delete all agent memories and embeddings
    ├── Anonymize log entries (replace user_id with hash)
    ├── Delete user account from database
    └── Send final deletion confirmation email
```

---

## 7. Third-Party Processors

| Processor | Service | Data Shared | Location |
|-----------|---------|-------------|----------|
| Railway | Application hosting | All application data (PostgreSQL, Redis) | US (us-east-1) |
| Vercel | CDN and frontend hosting | IP address, request headers | Global edge network |
| OpenAI | AI inference (GPT-4o, GPT-4o-mini) | Task prompts and agent outputs | US |
| Anthropic | AI inference (Claude Sonnet, Claude Haiku) | Task prompts and agent outputs | US |
| Google DeepMind | AI inference (Gemini 1.5 Pro, Flash) | Task prompts and agent outputs | US |
| Alibaba Cloud | AI inference (Qwen-72B) | Task prompts and agent outputs | China (for Qwen models) |
| PostHog | Product analytics | Page views, feature usage (anonymized) | US (EU option available) |
| Stripe | Payment processing | Billing info, payment method token | US |

**Note:** Using Qwen models (Alibaba) sends data to servers in China. If this is not acceptable, do not assign Qwen models to any agent in your team.

---

## 8. Data Processing Agreement (DPA)

A Data Processing Agreement is available for Team and Enterprise customers. Contact privacy@agentforge.dev to request a signed DPA.

---

## 9. Contact

- Privacy inquiries: privacy@agentforge.dev
- Data protection officer: dpo@agentforge.dev
- GDPR representative (EU): gdpr@agentforge.dev
- India grievance officer: grievance@agentforge.dev
