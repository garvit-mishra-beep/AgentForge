import type { AgentRole } from "./constants";

export interface TemplateMember {
  role: AgentRole;
  model: string;
  label: string;
  description: string;
  instructions: string;
}

export interface TeamTemplate {
  id: string;
  name: string;
  description: string;
  use_case: string;
  members: TemplateMember[];
}

export const TEAM_TEMPLATES: TeamTemplate[] = [
  {
    id: "full-stack",
    name: "Full Stack Team",
    description: "Build complete web applications with planning, coding, review, testing, and delivery",
    use_case: "End-to-end full-stack development projects",
    members: [
      {
        role: "team_lead",
        model: "gpt-4o-mini",
        label: "Planner",
        description: "Architects the solution and coordinates the team",
        instructions: "Break down the task into clear steps. Define architecture, acceptance criteria, and file structure before the builder starts.",
      },
      {
        role: "builder",
        model: "gpt-4o",
        label: "Coder",
        description: "Writes production-ready code following the plan",
        instructions: "Implement the plan exactly as specified. Write clean, documented code. Include error handling and input validation.",
      },
      {
        role: "reviewer",
        model: "gpt-4o-mini",
        label: "Code Reviewer",
        description: "Reviews code for bugs, edge cases, and best practices",
        instructions: "Check for security vulnerabilities, edge cases, performance issues, and adherence to the plan. Be thorough.",
      },
      {
        role: "tester",
        model: "gpt-4o-mini",
        label: "QA Engineer",
        description: "Writes and runs tests to verify correctness",
        instructions: "Write unit tests for all functions. Test edge cases, error paths, and happy paths. Report coverage metrics.",
      },
    ],
  },
  {
    id: "security-audit",
    name: "Security Audit Team",
    description: "Audit codebases for vulnerabilities, penetration test, and ensure compliance",
    use_case: "Security auditing and vulnerability assessment",
    members: [
      {
        role: "team_lead",
        model: "gpt-4o-mini",
        label: "Security Architect",
        description: "Defines the security audit scope and methodology",
        instructions: "Identify the security-critical parts of the codebase. Define threat models and audit checklists before the auditor starts.",
      },
      {
        role: "builder",
        model: "gpt-4o",
        label: "Auditor",
        description: "Analyzes code for vulnerabilities and weaknesses",
        instructions: "Scan for OWASP Top 10 vulnerabilities, injection flaws, authentication issues, and data exposure. Document each finding with severity.",
      },
      {
        role: "reviewer",
        model: "gpt-4o-mini",
        label: "Pen Tester",
        description: "Validates findings and probes for additional weaknesses",
        instructions: "Attempt to exploit each vulnerability found. Check for chained attacks. Verify that proposed fixes would resolve the issue.",
      },
      {
        role: "tester",
        model: "gpt-4o-mini",
        label: "Compliance Officer",
        description: "Verifies compliance with security standards",
        instructions: "Check findings against OWASP, CWE, and industry standards. Verify that the fix proposals meet compliance requirements.",
      },
    ],
  },
  {
    id: "startup-cto",
    name: "Startup CTO Team",
    description: "Rapid prototyping and product validation for early-stage startups",
    use_case: "Quick prototyping and product-market fit validation",
    members: [
      {
        role: "team_lead",
        model: "gpt-4o-mini",
        label: "CTO",
        description: "Makes architectural decisions and sets technical direction",
        instructions: "Prioritize speed-to-market. Choose simple architectures. Define MVP scope ruthlessly. Avoid over-engineering.",
      },
      {
        role: "builder",
        model: "gpt-4o",
        label: "Engineer",
        description: "Builds features fast with pragmatic code",
        instructions: "Ship working code quickly. Use established patterns. Add comments for future refactoring. Don't optimize prematurely.",
      },
      {
        role: "reviewer",
        model: "gpt-4o-mini",
        label: "Product Reviewer",
        description: "Reviews from a product and user experience perspective",
        instructions: "Evaluate the output for user experience, product-market fit, and business value. Flag anything that doesn't serve the MVP goals.",
      },
      {
        role: "tester",
        model: "gpt-4o-mini",
        label: "User Validator",
        description: "Tests from an end-user perspective",
        instructions: "Test as if you were the end user. Check for usability issues, confusing flows, and missing functionality. Prioritize critical path testing.",
      },
    ],
  },
  {
    id: "research",
    name: "Research Team",
    description: "Deep research, analysis, fact-checking, and critical review",
    use_case: "Technical research and feasibility analysis",
    members: [
      {
        role: "team_lead",
        model: "gpt-4o-mini",
        label: "Research Planner",
        description: "Designs the research methodology and scope",
        instructions: "Define research questions, methodology, and success criteria. Identify key sources and areas of investigation before the researcher starts.",
      },
      {
        role: "builder",
        model: "gpt-4o",
        label: "Researcher",
        description: "Gathers and synthesizes information",
        instructions: "Gather relevant information, code examples, and documentation. Synthesize findings into clear insights. Cite sources.",
      },
      {
        role: "reviewer",
        model: "gpt-4o-mini",
        label: "Fact Checker",
        description: "Verifies accuracy of research findings",
        instructions: "Verify all claims, code snippets, and technical assertions. Flag inaccuracies, outdated information, or misleading conclusions.",
      },
      {
        role: "tester",
        model: "gpt-4o-mini",
        label: "Critic",
        description: "Challenges assumptions and identifies gaps",
        instructions: "Identify gaps in the research. Challenge assumptions. Suggest alternative approaches. Evaluate the strength of conclusions.",
      },
    ],
  },
  {
    id: "backend-api",
    name: "Backend API Team",
    description: "Design, build, and test RESTful APIs with validation, error handling, and documentation",
    use_case: "Backend API development and microservices",
    members: [
      {
        role: "team_lead",
        model: "gpt-4o-mini",
        label: "API Architect",
        description: "Designs the API contract and data models",
        instructions: "Define the API contract first: endpoints, request/response shapes, validation rules. Plan the data layer and error handling strategy.",
      },
      {
        role: "builder",
        model: "gpt-4o",
        label: "Backend Engineer",
        description: "Implements endpoints with proper validation",
        instructions: "Implement each endpoint per the API contract. Add input validation, error handling, and proper HTTP status codes. Include request logging.",
      },
      {
        role: "reviewer",
        model: "gpt-4o-mini",
        label: "API Reviewer",
        description: "Reviews for security, performance, and correctness",
        instructions: "Check for injection vulnerabilities, broken auth, CORS misconfiguration, and performance issues. Verify error responses are informative.",
      },
      {
        role: "tester",
        model: "gpt-4o-mini",
        label: "API Tester",
        description: "Writes integration tests for all endpoints",
        instructions: "Write integration tests for every endpoint. Test happy paths, validation errors, auth failures, and edge cases. Report coverage metrics.",
      },
    ],
  },
  {
    id: "pr-review",
    name: "PR Review Team",
    description: "Review pull requests for bugs, security, style, and test coverage before merge",
    use_case: "Pull request code review automation",
    members: [
      {
        role: "team_lead",
        model: "gpt-4o-mini",
        label: "Review Coordinator",
        description: "Coordinates the review process and summarizes findings",
        instructions: "Analyze the diff scope. Assign review focus areas. Summarize findings into a clear pass/fail verdict with blocking and non-blocking items.",
      },
      {
        role: "builder",
        model: "gpt-4o",
        label: "Code Auditor",
        description: "Audits code changes for bugs and regressions",
        instructions: "Review each changed file for logic errors, edge cases, and regressions. Check that the code matches the PR description.",
      },
      {
        role: "reviewer",
        model: "gpt-4o-mini",
        label: "Security Reviewer",
        description: "Focused security review of all changes",
        instructions: "Scan for OWASP Top 10 issues, hardcoded secrets, injection points, and authentication/authorization gaps in the diff.",
      },
      {
        role: "tester",
        model: "gpt-4o-mini",
        label: "Test Coverage Analyzer",
        description: "Verifies test coverage and suggests missing tests",
        instructions: "Check that new code has adequate test coverage. Suggest specific test cases for uncovered paths. Flag if coverage drops below threshold.",
      },
    ],
  },
];
