from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, dict] = {}

    def register(self, name: str, func: Callable, description: str = "", parameters: Optional[dict] = None):
        self._tools[name] = {
            "func": func,
            "description": description,
            "parameters": parameters or {"type": "object", "properties": {}, "required": []},
        }

    def get(self, name: str) -> Optional[dict]:
        return self._tools.get(name)

    def list(self) -> List[dict]:
        return [
            {"name": name, "description": meta["description"], "parameters": meta["parameters"]}
            for name, meta in self._tools.items()
        ]

    async def execute(self, name: str, args: dict) -> Any:
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        return await tool["func"](**args)


registry = ToolRegistry()


async def web_search(query: str) -> str:
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api.duckduckgo.com/?q={query}&format=json", timeout=5)
            return resp.text[:2000]
    except Exception:
        return f"[Search results for: {query}]"


async def calculator(expression: str) -> str:
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


async def current_datetime() -> str:
    from datetime import datetime
    return datetime.utcnow().isoformat()


registry.register("web_search", web_search, description="Search the web for information", parameters={
    "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"],
})
registry.register("calculator", calculator, description="Evaluate a mathematical expression", parameters={
    "type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"],
})
registry.register("current_datetime", current_datetime, description="Get the current date and time", parameters={
    "type": "object", "properties": {}, "required": [],
})
