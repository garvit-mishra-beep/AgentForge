import type { TaskMessage, Task, Execution, Team } from "./types";

const BASE_TIME = new Date();

function addSeconds(s: number): string {
  return new Date(BASE_TIME.getTime() + s * 1000).toISOString();
}

export interface DemoScenario {
  id: string;
  title: string;
  description: string;
  team: Team;
  task: Task;
  execution: Execution;
  messages: TaskMessage[];
  timing: {
    planDelay: number;
    builderDelay: number;
    reviewerDelay: number;
    testerDelay: number;
    deliverDelay: number;
    totalSteps: number;
  };
  tokenCounts: number[];
}

const jwtTeam: Team = {
  id: "demo-team",
  name: "Software Engineering Team",
  description: "Full-stack AI development team",
  created_by: "demo",
  created_at: BASE_TIME.toISOString(),
  updated_at: BASE_TIME.toISOString(),
  members: [
    { id: "m1", team_id: "demo-team", role: "team_lead", model: "gpt-4o-mini", status: "idle", created_at: BASE_TIME.toISOString() },
    { id: "m2", team_id: "demo-team", role: "builder", model: "gpt-4o", status: "idle", created_at: BASE_TIME.toISOString() },
    { id: "m3", team_id: "demo-team", role: "reviewer", model: "gpt-4o-mini", status: "idle", created_at: BASE_TIME.toISOString() },
    { id: "m4", team_id: "demo-team", role: "tester", model: "gpt-4o-mini", status: "idle", created_at: BASE_TIME.toISOString() },
  ],
};

function buildJwtScenario(): DemoScenario {
  const plan = JSON.stringify({
    plan_summary: "Build a FastAPI JWT auth module with /login, /verify, and /refresh endpoints using python-jose for HS256 token handling.",
    steps: [
      { step: 1, description: "Create auth module with JWT utility functions", files_to_create: ["app/auth/__init__.py", "app/auth/jwt.py"], acceptance_criteria: ["Token generation works", "Token verification works", "Token refresh works"] },
      { step: 2, description: "Create API endpoints for login, verify, refresh", files_to_create: ["app/auth/routes.py"], acceptance_criteria: ["POST /login returns token", "GET /verify validates token", "POST /refresh rotates token"] },
    ],
    risks: ["Token expiry needs careful handling", "Secret key must be configured via env"],
  }, null, 2);

  const code = JSON.stringify({
    summary: "Implemented JWT authentication module with FastAPI. Three endpoints: login, verify, refresh.",
    files: [
      { path: "app/auth/jwt.py", language: "python", content: `from datetime import datetime, timedelta
from jose import JWTError, jwt

SECRET_KEY = "change-me-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None` },
      { path: "app/auth/routes.py", language: "python", content: `from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.auth.jwt import create_access_token, verify_token

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(req: LoginRequest):
    if req.username != "admin" or req.password != "secret":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_access_token({"sub": req.username}), "token_type": "bearer"}

@router.get("/verify")
async def verify(token: str):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"valid": True, "sub": payload.get("sub")}

@router.post("/refresh")
async def refresh(token: str):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"access_token": create_access_token({"sub": payload.get("sub")}), "token_type": "bearer"}` },
    ],
  }, null, 2);

  const review = JSON.stringify({
    verdict: "PASS",
    findings: [
      { severity: "minor", description: "Secret key is hardcoded - should use environment variable", recommendation: "Move SECRET_KEY to .env and load via os.getenv" },
      { severity: "minor", description: "No input validation on username/password length", recommendation: "Add min/max length validation to LoginRequest model" },
    ],
  }, null, 2);

  const test = JSON.stringify({
    verdict: "PASS",
    summary: "All tests passing. 12 test cases covering login, token verification, refresh, and error paths.",
    tests: [
      { name: "test_login_success", status: "passed", duration: "0.23s" },
      { name: "test_login_invalid_credentials", status: "passed", duration: "0.12s" },
      { name: "test_verify_valid_token", status: "passed", duration: "0.15s" },
      { name: "test_verify_expired_token", status: "passed", duration: "0.18s" },
      { name: "test_refresh_token", status: "passed", duration: "0.21s" },
    ],
    coverage: "87%",
  }, null, 2);

  const delivery = JSON.stringify({
    verdict: "approved",
    delivery_summary: "Built a complete JWT authentication module for FastAPI with three endpoints: /auth/login, /auth/verify, /auth/refresh. Uses HS256 signing with 30-minute expiry. All tests passing.",
    deliverables: { files: ["app/auth/jwt.py", "app/auth/routes.py"] },
    next_steps: ["Move SECRET_KEY to environment variable", "Add rate limiting to login endpoint"],
  }, null, 2);

  return {
    id: "jwt-auth",
    title: "JWT Authentication Module",
    description: "Build a FastAPI JWT authentication module with login, verify, and refresh endpoints using HS256 signing.",
    team: jwtTeam,
    task: {
      id: "demo-task", team_id: "demo-team",
      title: "JWT Authentication Module",
      description: "Build a FastAPI JWT authentication module with login, verify, and refresh endpoints using HS256 signing.",
      status: "running", created_by: "demo",
      created_at: BASE_TIME.toISOString(), updated_at: BASE_TIME.toISOString(),
      completed_at: null, error_message: null,
    },
    execution: {
      id: "demo-exec", task_id: "demo-task", status: "running",
      current_node: "team_lead_plan",
      started_at: BASE_TIME.toISOString(), completed_at: null, error_message: null,
    },
    messages: [
      { id: "demo-msg-1", task_id: "demo-task", step_order: 1, role: "team_lead", model: "gpt-4o-mini", message_type: "plan", content: plan, created_at: addSeconds(1), tokens: 142 },
      { id: "demo-msg-2", task_id: "demo-task", step_order: 2, role: "builder", model: "gpt-4o", message_type: "code", content: code, created_at: addSeconds(4), tokens: 486 },
      { id: "demo-msg-3", task_id: "demo-task", step_order: 3, role: "reviewer", model: "gpt-4o-mini", message_type: "review", content: review, created_at: addSeconds(7), tokens: 89 },
      { id: "demo-msg-4", task_id: "demo-task", step_order: 4, role: "tester", model: "gpt-4o-mini", message_type: "test", content: test, created_at: addSeconds(9), tokens: 156 },
      { id: "demo-msg-5", task_id: "demo-task", step_order: 5, role: "team_lead", model: "gpt-4o-mini", message_type: "delivery", content: delivery, created_at: addSeconds(11), tokens: 201 },
    ],
    timing: { planDelay: 800, builderDelay: 2500, reviewerDelay: 2000, testerDelay: 1500, deliverDelay: 1000, totalSteps: 5 },
    tokenCounts: [142, 486, 89, 156, 201],
  };
}

function buildCrudScenario(): DemoScenario {
  const plan = JSON.stringify({
    plan_summary: "Build a RESTful CRUD API for a task management app using Express.js with MongoDB. Include create, read, update, delete endpoints with validation and error handling.",
    steps: [
      { step: 1, description: "Set up Express server with MongoDB connection", files_to_create: ["server.js", "db.js"], acceptance_criteria: ["Server starts on port 3000", "MongoDB connection works"] },
      { step: 2, description: "Create Task model and CRUD routes", files_to_create: ["models/Task.js", "routes/tasks.js"], acceptance_criteria: ["All CRUD endpoints work", "Input validation is in place"] },
    ],
    risks: ["No authentication middleware", "Missing rate limiting"],
  }, null, 2);

  const code = JSON.stringify({
    summary: "Built a complete CRUD API for task management with Express.js and MongoDB. Five endpoints: create, list, get, update, delete.",
    files: [
      { path: "server.js", language: "javascript", content: `const express = require("express");
const mongoose = require("mongoose");
const taskRoutes = require("./routes/tasks");

const app = express();
app.use(express.json());
app.use("/api/tasks", taskRoutes);

mongoose.connect(process.env.MONGO_URI || "mongodb://localhost:27017/tasks")
  .then(() => app.listen(3000, () => console.log("Server running on port 3000")))
  .catch((err) => console.error("MongoDB connection error:", err));

module.exports = app;` },
      { path: "models/Task.js", language: "javascript", content: `const mongoose = require("mongoose");

const taskSchema = new mongoose.Schema({
  title: { type: String, required: true, trim: true, maxlength: 200 },
  description: { type: String, trim: true, maxlength: 1000 },
  status: { type: String, enum: ["todo", "in_progress", "done"], default: "todo" },
  priority: { type: String, enum: ["low", "medium", "high"], default: "medium" },
  dueDate: { type: Date },
}, { timestamps: true });

module.exports = mongoose.model("Task", taskSchema);` },
      { path: "routes/tasks.js", language: "javascript", content: `const router = require("express").Router();
const Task = require("../models/Task");

router.get("/", async (req, res) => {
  const tasks = await Task.find().sort({ createdAt: -1 });
  res.json(tasks);
});

router.get("/:id", async (req, res) => {
  const task = await Task.findById(req.params.id);
  if (!task) return res.status(404).json({ error: "Task not found" });
  res.json(task);
});

router.post("/", async (req, res) => {
  const { title, description, priority, dueDate } = req.body;
  if (!title || !title.trim()) return res.status(400).json({ error: "Title is required" });
  const task = await Task.create({ title, description, priority, dueDate });
  res.status(201).json(task);
});

router.put("/:id", async (req, res) => {
  const task = await Task.findByIdAndUpdate(req.params.id, req.body, { new: true, runValidators: true });
  if (!task) return res.status(404).json({ error: "Task not found" });
  res.json(task);
});

router.delete("/:id", async (req, res) => {
  const task = await Task.findByIdAndDelete(req.params.id);
  if (!task) return res.status(404).json({ error: "Task not found" });
  res.json({ message: "Task deleted" });
});

module.exports = router;` },
    ],
  }, null, 2);

  const review = JSON.stringify({
    verdict: "PASS",
    findings: [
      { severity: "major", description: "No error handling for MongoDB connection failures at startup", recommendation: "Add process-level error handler for unhandled rejections" },
      { severity: "minor", description: "Pagination is missing on the list endpoint", recommendation: "Add page/limit query params with defaults" },
      { severity: "info", description: "No environment variable validation", recommendation: "Add dotenv and validate required env vars on startup" },
    ],
  }, null, 2);

  const test = JSON.stringify({
    verdict: "PASS",
    summary: "All tests passing. 15 test cases covering all CRUD operations, validation, and error paths.",
    tests: [
      { name: "POST /api/tasks creates a task", status: "passed", duration: "0.31s" },
      { name: "POST /api/tasks rejects empty title", status: "passed", duration: "0.14s" },
      { name: "GET /api/tasks returns list", status: "passed", duration: "0.18s" },
      { name: "GET /api/tasks/:id returns task", status: "passed", duration: "0.12s" },
      { name: "PUT /api/tasks/:id updates task", status: "passed", duration: "0.22s" },
      { name: "DELETE /api/tasks/:id deletes task", status: "passed", duration: "0.16s" },
    ],
    coverage: "91%",
  }, null, 2);

  const delivery = JSON.stringify({
    verdict: "approved",
    delivery_summary: "Built a complete CRUD REST API for task management with Express.js and MongoDB. Five endpoints with full validation, error handling, and 91% test coverage.",
    deliverables: { files: ["server.js", "models/Task.js", "routes/tasks.js"] },
    next_steps: ["Add authentication middleware", "Add rate limiting", "Add API documentation with Swagger"],
  }, null, 2);

  const crudTeam: Team = {
    ...jwtTeam, id: "demo-team-crud", name: "Node.js Backend Team",
  };

  return {
    id: "crud-api",
    title: "Task Manager CRUD API",
    description: "Build a RESTful CRUD API for task management using Express.js, MongoDB, and Mongoose with full validation.",
    team: crudTeam,
    task: {
      id: "demo-task-crud", team_id: "demo-team-crud",
      title: "Task Manager CRUD API",
      description: "Build a RESTful CRUD API for task management using Express.js, MongoDB, and Mongoose with full validation.",
      status: "running", created_by: "demo",
      created_at: BASE_TIME.toISOString(), updated_at: BASE_TIME.toISOString(),
      completed_at: null, error_message: null,
    },
    execution: {
      id: "demo-exec-crud", task_id: "demo-task-crud", status: "running",
      current_node: "team_lead_plan",
      started_at: BASE_TIME.toISOString(), completed_at: null, error_message: null,
    },
    messages: [
      { id: "crud-msg-1", task_id: "demo-task-crud", step_order: 1, role: "team_lead", model: "gpt-4o-mini", message_type: "plan", content: plan, created_at: addSeconds(1), tokens: 98 },
      { id: "crud-msg-2", task_id: "demo-task-crud", step_order: 2, role: "builder", model: "gpt-4o", message_type: "code", content: code, created_at: addSeconds(4), tokens: 523 },
      { id: "crud-msg-3", task_id: "demo-task-crud", step_order: 3, role: "reviewer", model: "gpt-4o-mini", message_type: "review", content: review, created_at: addSeconds(7), tokens: 112 },
      { id: "crud-msg-4", task_id: "demo-task-crud", step_order: 4, role: "tester", model: "gpt-4o-mini", message_type: "test", content: test, created_at: addSeconds(9), tokens: 178 },
      { id: "crud-msg-5", task_id: "demo-task-crud", step_order: 5, role: "team_lead", model: "gpt-4o-mini", message_type: "delivery", content: delivery, created_at: addSeconds(11), tokens: 167 },
    ],
    timing: { planDelay: 800, builderDelay: 2800, reviewerDelay: 2200, testerDelay: 1800, deliverDelay: 1200, totalSteps: 5 },
    tokenCounts: [98, 523, 112, 178, 167],
  };
}

export const DEMO_SCENARIOS: DemoScenario[] = [
  buildJwtScenario(),
  buildCrudScenario(),
];

export const DEMO_TEAM = jwtTeam;
export const DEMO_TASK = DEMO_SCENARIOS[0]!.task;
export const DEMO_EXECUTION = DEMO_SCENARIOS[0]!.execution;
export const DEMO_TIMING = DEMO_SCENARIOS[0]!.timing;

export function createDemoMessages(scenarioId = "jwt-auth"): TaskMessage[] {
  const scenario = DEMO_SCENARIOS.find((s) => s.id === scenarioId) ?? DEMO_SCENARIOS[0]!;
  return scenario.messages;
}
