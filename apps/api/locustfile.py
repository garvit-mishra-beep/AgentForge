"""Locust load testing script for AgentForge API.

Usage:
    locust -f locustfile.py --host=http://localhost:8000
    locust -f locustfile.py --headless -u 10 -r 2 --run-time 30s --host=http://localhost:8000
"""

import random
import uuid

from locust import HttpUser, between, task


class AgentForgeUser(HttpUser):
    wait_time = between(1, 3)
    token: str = ""
    project_id: str = ""
    task_id: str = ""

    def on_start(self):
        email = f"loadtest-{uuid.uuid4().hex[:8]}@test.com"
        resp = self.client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "testpassword123",
            "name": "Load Tester",
        })
        if resp.status_code == 201:
            data = resp.json()
            self.token = data["token"]
        else:
            resp = self.client.post("/api/v1/auth/login", json={
                "email": "demo@agentforge.dev",
                "password": "changeme",
            })
            if resp.status_code == 200:
                self.token = resp.json()["token"]

    @task(3)
    def health_check(self):
        self.client.get("/api/v1/health")

    @task(2)
    def list_providers(self):
        self.client.get("/api/v1/keys/providers")

    @task(2)
    def create_and_list_teams(self):
        if not self.token:
            return
        name = f"team-{uuid.uuid4().hex[:6]}"
        resp = self.client.post("/api/v1/teams", json={
            "name": name,
            "roles": [
                {"role": "lead", "model": "qwen3.5:4b"},
                {"role": "builder", "model": "qwen2.5-coder:7b"},
                {"role": "reviewer", "model": "phi4-mini"},
            ],
        }, headers={"Authorization": f"Bearer {self.token}"})
        if resp.status_code == 201:
            self.client.get("/api/v1/teams", headers={"Authorization": f"Bearer {self.token}"})

    @task(1)
    def submit_review(self):
        if not self.token:
            return
        code_snippets = [
            "def hello(): print('world')",
            "const x = 1; console.log(x);",
            "SELECT * FROM users WHERE id = $1",
            '<div class="container">Hello</div>',
            "fn main() { println!(\"hi\"); }",
        ]
        self.client.post("/api/v1/review", json={
            "code": random.choice(code_snippets),
            "language": "python",
        }, headers={"Authorization": f"Bearer {self.token}"})

    @task(1)
    def auth_refresh(self):
        if not self.token:
            return
        resp = self.client.post("/api/v1/auth/refresh", json={
            "refresh_token": self.token,
        })
        if resp.status_code == 200:
            self.token = resp.json()["token"]

    @task(1)
    def metrics(self):
        self.client.get("/api/v1/metrics")

    @task(1)
    def create_project(self):
        if not self.token:
            return
        resp = self.client.post("/api/v1/projects", json={
            "name": f"project-{uuid.uuid4().hex[:6]}",
            "description": "Load test project",
        }, headers={"Authorization": f"Bearer {self.token}"})
        if resp.status_code == 201:
            self.project_id = resp.json()["id"]

    @task(1)
    def list_projects(self):
        if not self.token:
            return
        self.client.get("/api/v1/projects", headers={"Authorization": f"Bearer {self.token}"})
