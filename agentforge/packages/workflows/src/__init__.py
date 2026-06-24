from __future__ import annotations

import ast
import asyncio
import logging
import operator
from typing import Any, Dict, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict

logger = logging.getLogger(__name__)

ALLOWED_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.And: lambda a, b: a and b,
    ast.Or: lambda a, b: a or b,
    ast.Not: operator.not_,
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class SafeEvalError(ValueError):
    pass


def safe_eval(expression: str, context: dict[str, Any]) -> Any:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise SafeEvalError(f"Syntax error: {e}")

    return _eval_node(tree.body, context)


def _eval_node(node: ast.AST, context: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        if node.id in context:
            return context[node.id]
        raise SafeEvalError(f"Name '{node.id}' is not defined")

    if isinstance(node, ast.UnaryOp):
        op_func = ALLOWED_OPS.get(type(node.op))
        if op_func is None:
            raise SafeEvalError(f"Unary operator '{type(node.op).__name__}' is not allowed")
        return op_func(_eval_node(node.operand, context))

    if isinstance(node, ast.BinOp):
        op_func = ALLOWED_OPS.get(type(node.op))
        if op_func is None:
            raise SafeEvalError(f"Binary operator '{type(node.op).__name__}' is not allowed")
        return op_func(_eval_node(node.left, context), _eval_node(node.right, context))

    if isinstance(node, ast.BoolOp):
        values = [_eval_node(v, context) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        elif isinstance(node.op, ast.Or):
            return any(values)
        raise SafeEvalError(f"Boolean operator '{type(node.op).__name__}' is not allowed")

    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, context)
        for op, comparator in zip(node.ops, node.comparators):
            op_func = ALLOWED_OPS.get(type(op))
            if op_func is None:
                raise SafeEvalError(f"Comparison operator '{type(op).__name__}' is not allowed")
            right = _eval_node(comparator, context)
            if not op_func(left, right):
                return False
            left = right
        return True

    if isinstance(node, ast.List):
        return [_eval_node(el, context) for el in node.elts]

    if isinstance(node, ast.Dict):
        return {_eval_node(k, context): _eval_node(v, context) for k, v in zip(node.keys, node.values) if k is not None}

    if isinstance(node, ast.Subscript):
        return _eval_node(node.value, context)[_eval_node(node.slice, context)]

    if isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Name) and node.value.id in context:
            obj = context[node.value.id]
            if isinstance(obj, dict):
                return obj.get(node.attr)
            return getattr(obj, node.attr)
        raise SafeEvalError(f"Attribute access on non-context object is not allowed")

    raise SafeEvalError(f"Expression type '{type(node).__name__}' is not allowed")


class WorkflowState(TypedDict):
    input: dict
    output: Optional[dict]
    current_node: str
    node_results: Dict[str, Any]
    errors: List[str]


class WorkflowEngine:
    def __init__(self):
        self.graphs: Dict[str, StateGraph] = {}
        self.checkpointer = MemorySaver()

    def build_graph(self, workflow_id: str, definition: dict) -> StateGraph:
        graph = StateGraph(WorkflowState)
        nodes = definition.get("nodes", [])
        edges = definition.get("edges", [])

        for node in nodes:
            node_id = node["id"]
            node_type = node.get("type", "agent")
            if node_type == "agent":
                agent_id = node.get("agent_id", "")
                graph.add_node(node_id, lambda state, aid=agent_id: self._run_agent_node(state, aid))
            elif node_type == "condition":
                expression = node.get("config", {}).get("expression", "True")
                graph.add_node(node_id, lambda state, expr=expression: self._run_condition_node(state, expr))
            elif node_type == "output":
                graph.add_node(node_id, lambda state: self._run_output_node(state))

        for edge in edges:
            from_node = edge.get("from")
            to_node = edge.get("to", END)
            condition = edge.get("condition")
            if condition:
                graph.add_conditional_edges(from_node, lambda state, cond=condition: to_node if safe_eval(cond, {"state": state}) else END)
            else:
                graph.add_edge(from_node, to_node)

        if nodes:
            graph.set_entry_point(nodes[0]["id"])

        compiled = graph.compile(checkpointer=self.checkpointer)
        self.graphs[workflow_id] = compiled
        return compiled

    async def execute(self, workflow_id: str, input_data: dict) -> dict:
        graph = self.graphs.get(workflow_id)
        if not graph:
            raise ValueError(f"Workflow '{workflow_id}' not compiled")
        initial_state = WorkflowState(input=input_data, output=None, current_node="", node_results={}, errors=[])
        result = await graph.ainvoke(initial_state, config={"configurable": {"thread_id": workflow_id}})
        return result

    async def _run_agent_node(self, state: WorkflowState, agent_id: str) -> WorkflowState:
        from apps.api.services import AgentService, ExecutionService
        from apps.api.core.database import async_session
        async with async_session() as db:
            agent_svc = AgentService(db)
            exec_svc = ExecutionService(db)
            agent = await agent_svc.get(agent_id)
            if not agent:
                return {**state, "errors": state["errors"] + [f"Agent {agent_id} not found"]}
            from packages.llm.src import get_llm
            llm = get_llm(provider=agent.llm_config.get("provider", "openai"))
            messages = [{"role": "system", "content": agent.system_prompt or "You are a helpful assistant."}]
            messages.append({"role": "user", "content": str(state["input"])})
            response = await llm.generate(messages, temperature=agent.llm_config.get("temperature", 0.7))
            node_results = {**state["node_results"], agent_id: response.get("content", "")}
            return {**state, "node_results": node_results}

    def _run_condition_node(self, state: WorkflowState, expression: str) -> WorkflowState:
        try:
            context = {"state": state, "output": state.get("output")}
            result = safe_eval(expression, context)
            return {**state, "current_node": str(result)}
        except SafeEvalError as e:
            return {**state, "errors": state["errors"] + [f"Condition security error: {e}"]}
        except Exception as e:
            return {**state, "errors": state["errors"] + [f"Condition error: {e}"]}

    async def _run_output_node(self, state: WorkflowState) -> WorkflowState:
        return {**state, "output": state["node_results"]}


engine = WorkflowEngine()
