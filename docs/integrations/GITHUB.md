# GitHub App Native Integration — AgentForge

AgentForge features a native GitHub App integration that automatically runs multi-agent code audits on Pull Requests and writes comments directly onto line diffs.

---

## 1. Webhook Operational Flow

```text
GitHub Event               AgentForge Backend API
    │                                │
    │ 1. PR Opened Webhook           │
    ├───────────────────────────────►│  (Verify HMAC signature)
    │                                │
    │ 2. Sync Repository Branches    │
    │◄───────────────────────────────┤  (Git fetch / pull)
    │                                │
    │ 3. Execute Reviewer Pipeline   │
    │◄───────────────────────────────┤  (Parallel Review/Test/Security)
    │                                │
    │ 4. Publish Review Comments     │
    │◄───────────────────────────────┼  (Post comments to lines on PR)
```

---

## 2. Configuration Settings

To register your AgentForge GitHub App, add these keys to your backend environment:

* **`GITHUB_APP_ID`:** Your registered GitHub App ID.
* **`GITHUB_PRIVATE_KEY`:** Plaintext PEM format private key string or path to your private key file.
* **`GITHUB_WEBHOOK_SECRET`:** Secret key configured in your App settings to verify webhook request HMAC headers.

---

## 3. Webhook Handling Logic

The gateway API endpoint at `/api/v1/github/webhook` processes events:
1. **Signature Check:** Validates signature using the `GITHUB_WEBHOOK_SECRET` header.
2. **Payload Extraction:** Checks for events `pull_request.opened` or `pull_request.synchronize`.
3. **Execution Task Queueing:** Queues a background review job targeting the PR's specific branch and commit SHA.
4. **GitHub Commenting:** Once the reviewer and security agent nodes complete execution, the backend publishes code changes and quality warnings as line review comment threads back to the GitHub PR.
5. **PR Check Status:** Sets the commit validation check status (`success` or `failure`) depending on the validation gate outcome.
