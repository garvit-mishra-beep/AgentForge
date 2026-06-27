# ── Build initial state ──────────────────────────────────────────
        initial_state = {
            "task": {
                "id": task_row["id"],
                "title": task_row["title"],
                "description": task_row["description"],
            },
            "team_config": team_config,
            "plan": None,
            "planner_output": None,
            "builder_output": None,
            "review": None,
            "tester_output": None,
            "security_output": None,
            "architect_output": None,
            "deployment_output": None,
            "aggregator_output": None,
            "delivery": None,
            "current_step": "team_lead_plan",
            "messages": [],
            "errors": [],
            "fast_demo_mode": settings.fast_demo_mode,
            "timed_out_agents": [],
            "repository_context": repository_context,
            "relevant_memories": [
                {"key": m["key"], "content": m["content"], "memory_type": m["memory_type"], "importance": m["importance"]}
                for m in relevant_memories
            ],
            "learned_signal": learned_signal,
            # BYOK fields - pass user and project context to agent nodes
            "user_id": user_id,
            "project_id": project_id,
            # Database session for provider lookup
            "db": db,
        }