# System Architecture Blueprint — V1

This document outlines the actual system design, data routing pipelines, and component relationships implemented in AgentForge.

---

## 1. Request Lifecycle Flow

```mermaid
sequenceDiagram
    participant User as Web/CLI Client
    participant CORS as CORS Middleware
    participant RL as Redis Rate Limiter
    participant CID as Correlation ID Middleware
    participant Auth as JWT Auth Middleware
    participant Router as API Route Endpoint
    
    User->>CORS: API Request (HTTP/WS)
    activate CORS
    CORS->>CORS: Validate Origin Headers
    CORS->>RL: Forward Request
    activate RL
    RL->>RL: Check IP count against Redis
    alt Limit Exceeded
        RL-->>User: HTTP 429 Too Many Requests
    else Limit OK
        RL->>CID: Forward Request
        activate CID
        CID->>CID: Inject/Retrieve Correlation ID
        CID->>Auth: Forward Request
        activate Auth
        Auth->>Auth: Decode Bearer Token / Verify Claims
        alt Auth Enabled & Invalid Token
            Auth-->>User: HTTP 415/401 Unauthorized
        else Auth OK
            Auth->>Router: Execute Route Handler
            activate Router
            Router-->>User: Return JSON Response
            deactivate Router
        end
        deactivate Auth
        deactivate CID
    end
    deactivate RL
    deactivate CORS
```

---

## 2. Authentication and Session Flow

```mermaid
sequenceDiagram
    participant Client as Client Client (Web/CLI)
    participant AuthAPI as app/routes/auth.py
    participant AuthHelper as app/auth.py
    participant DB as PostgreSQL
    
    Note over Client, DB: 1. User Registration
    Client->>AuthAPI: POST /auth/register {email, password}
    AuthAPI->>AuthHelper: Hash password with bcrypt
    AuthHelper->>DB: INSERT INTO users (email, hashed_password)
    DB-->>AuthAPI: OK
    AuthAPI-->>Client: HTTP 201 Created
    
    Note over Client, DB: 2. User Login
    Client->>AuthAPI: POST /auth/login {email, password}
    AuthAPI->>DB: SELECT hashed_password FROM users WHERE email = ?
    DB-->>AuthAPI: hashed_password
    AuthAPI->>AuthHelper: Validate password via bcrypt
    AuthAPI->>AuthHelper: Generate PyJWT (AccessToken + RefreshToken)
    AuthAPI->>DB: INSERT INTO refresh_tokens (user_id, token_hash)
    DB-->>AuthAPI: OK
    AuthAPI-->>Client: Returns {token, refresh_token}
    
    Note over Client, DB: 3. Session Refreshing
    Client->>AuthAPI: Request with Expired Access Token
    AuthAPI-->>Client: HTTP 401 Unauthorized
    Client->>AuthAPI: POST /auth/refresh {refresh_token}
    AuthAPI->>DB: SELECT user_id FROM refresh_tokens WHERE token_hash = ?
    DB-->>AuthAPI: user_id
    AuthAPI->>AuthHelper: Generate New PyJWT Tokens
    AuthAPI-->>Client: Returns {token, refresh_token}
```

---

## 3. Orchestration Engine State Flow

AgentForge coordinates executions using a LangGraph workspace layout:

```mermaid
graph TD
    Start([Task Created]) --> Plan[Team Lead Plan]
    Plan --> Planner[Planner Agent]
    Planner --> PlanVal[Planner Validation Gate]
    
    PlanVal -->|Valid| Arch[Architect Agent]
    PlanVal -->|Invalid| Deliver[Team Lead Deliver]
    
    Arch --> ArchVal[Architect Validation Gate]
    ArchVal -->|Valid| Build[Builder Agent]
    ArchVal -->|Invalid| Deliver
    
    Build --> BuildVal[Builder Validation Gate]
    BuildVal -->|Invalid| Deliver
    
    BuildVal -->|Valid: Fan Out| Review[Reviewer Agent]
    BuildVal -->|Valid: Fan Out| Test[Tester Agent]
    BuildVal -->|Valid: Fan Out| Sec[Security Agent]
    
    Review --> RevVal[Reviewer Validation Gate]
    Test --> TestVal[Tester Validation Gate]
    Sec --> SecVal[Security Validation Gate]
    
    RevVal & TestVal & SecVal --> Agg[Aggregator Agent]
    Agg --> AggVal[Aggregator Validation Gate]
    
    AggVal --> Deploy[Deployment Agent]
    Deploy --> DeployVal[Deployment Validation Gate]
    
    DeployVal --> Deliver
    Deliver --> End([Task Completed])
```

---

## 4. Execution Sandbox Isolation

The `sandbox_executor.py` runs untrusted Builder outputs:

```mermaid
graph LR
    API[FastAPI Server] -->|Instantiate| Executor[SandboxExecutor]
    Executor -->|Docker SDK Available| Docker[Launch Container]
    Executor -->|Docker SDK Missing| Subprocess[Fallback: Subprocess run]
    
    subgraph Docker Hardening Policies
        Docker --> Cap[Drop Linux Capabilities]
        Docker --> SecComp[Restrict Syscalls: Seccomp]
        Docker --> Net[Network Namespace: None]
        Docker --> Res[Limits: CPU & Memory caps]
    end
```

---

## 5. Deployment Topology

```mermaid
graph TD
    Internet((Internet)) -->|Reverse Proxy| Nginx[NGINX / Gateway]
    
    subgraph Local Server / Node
        Nginx -->|Port 3000| Next[Next.js Frontend]
        Nginx -->|Port 8000| FastAPI[FastAPI Backend]
        
        FastAPI -->|TCP 6379| Redis[Redis Caching & Limit]
        FastAPI -->|TCP 5432| DB[(PostgreSQL Database)]
        
        FastAPI -->|Unix Socket /var/run/docker.sock| HostDocker[Host Docker Engine]
        HostDocker -->|Spawn| Sandbox1[Sandbox Container 1]
        HostDocker -->|Spawn| Sandbox2[Sandbox Container 2]
    end
```
