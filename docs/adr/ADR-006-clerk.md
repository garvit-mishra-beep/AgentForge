# ADR-006: Clerk for Authentication

## Status
Accepted

## Context
AgentForge AI requires authentication for:

- **User authentication**: Login/signup for the web application
- **Session management**: Persistent authenticated sessions
- **Multi-provider support**: Email/password, Google, GitHub, SSO (enterprise)
- **Organization management**: Team accounts, multi-tenancy
- **API authentication**: JWT verification for backend API calls
- **Webhook integration**: User creation/deletion events for backend synchronization
- **Role-based access control**: Admin, member, viewer roles

## Alternatives Considered

### 1. Auth0
- **Pros**: Enterprise-grade, extensive social providers, MFA, breach detection, extensive SDK support
- **Cons**: Expensive at scale ($0.023/MAU + enterprise tiers), complex pricing, feature overload for MVP, heavy SDK

### 2. Supabase Auth
- **Pros**: Open source, PostgreSQL-backed, Row Level Security (RLS), included with Supabase stack, good pricing
- **Cons**: Tied to Supabase ecosystem, less mature multi-tenant features, limited social login providers without additional config, self-hosting Supabase adds operational overhead

### 3. Firebase Authentication
- **Pros**: Generous free tier, Google ecosystem, easy social login, mature SDK
- **Cons**: Google Cloud vendor lock-in, no multi-tenant support (tenants are workaround via custom claims), limited enterprise SSO, no built-in organization management

### 4. Clerk (Selected)
- **Pros**: Developer experience is best-in-class, prebuilt UI components (Clerk Elements), multi-tenant/org support built-in, webhook-first design, generous free tier (10K MAU), Next.js integration is seamless (App Router, Server Components, Middleware), JWT forwarding to backend, Magic URL, social login, enterprise SSO all included, active development and modern DX
- **Cons**: Relatively new (less enterprise track record), fewer social login options than Auth0, managed-only (no self-hosting), pricing changes possible as company grows, data residency concerns for some regions

### 5. NextAuth.js / Auth.js
- **Pros**: Open source, self-hosted, framework-native for Next.js, extensive adapter system
- **Cons**: No built-in multi-tenancy, no prebuilt UI components, requires self-hosting database for sessions, more boilerplate for organization management

## Decision
Use **Clerk** for authentication and user management.

Key integration:
- Clerk `<SignIn />`, `<SignUp />`, `<UserButton />` components in Next.js
- Clerk middleware for route protection
- Clerk webhooks (user.created, user.deleted, organization.created) to synchronize with PostgreSQL
- JWT template configured to forward user ID and organization ID to FastAPI backend
- FastAPI middleware to verify Clerk JWTs on API requests

## Consequences

### Positive
- Drop-in authentication UI components save weeks of development
- Multi-tenant organization support built-in (no custom implementation)
- Webhook-first design means we can synchronize auth state with PostgreSQL reliably
- Next.js middleware integration provides route protection at the edge
- Free tier (10K MAU) covers MVP and early traction
- JWT forwarding means no custom token service needed

### Negative
- Vendor lock-in for auth (migrating away from Clerk would require reimplementing auth UIs, org management, and session handling)
- No self-hosting option (enterprise customers with strict data residency may require Auth0 or self-hosted Auth.js)
- Data residency limited to Clerk's available regions

## Tradeoffs
- Clerk was chosen over Auth0 because of superior developer experience, better Next.js integration, and simpler pricing. If an enterprise customer requires self-hosting, we can evaluate Auth0 Enterprise or self-hosted Auth.js at that point.
- Clerk was chosen over Auth.js despite the vendor lock-in because multi-tenant org management and prebuilt UIs save significant development time. We'll structure our backend to keep auth abstracted behind middleware so migration is less painful.
- The data residency concern is real but acceptable for MVP. If it becomes a blocker for enterprise deals, we'd evaluate alternatives.

## References
- [Clerk Documentation](https://clerk.com/docs)
- [Clerk Next.js Integration](https://clerk.com/docs/quickstarts/nextjs)
- [Clerk Webhooks](https://clerk.com/docs/webhooks/overview)
- [Clerk Organizations](https://clerk.com/docs/organizations/overview)
