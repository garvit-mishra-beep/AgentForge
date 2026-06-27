"""
Call Graph Builder for AgentForge.
Builds call graphs showing function calls, method invocations, and dependencies.
"""
import ast
import re
import os
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class CallEdge:
    """Represents a call from one function to another."""
    caller: str  # Function/method that makes the call
    callee: str  # Function/method being called
    caller_file: str
    callee_file: str
    caller_line: int
    callee_line: int
    call_type: str = "direct"  # direct, indirect, dynamic, method
    context: Optional[str] = None  # Additional context about the call


@dataclass
class CallGraphNode:
    """Represents a node (function/method) in the call graph."""
    name: str
    function_type: str  # function, method, constructor, etc.
    file_path: str
    line_number: int
    calls: List[str] = field(default_factory=list)  # Functions this function calls
    called_by: List[str] = field(default_factory=list)  # Functions that call this function
    is_entry_point: bool = False
    is_public_api: bool = False
    complexity: int = 0  # Cyclomatic complexity approximation


@dataclass
class CallGraph:
    """Represents a complete call graph."""
    nodes: Dict[str, CallGraphNode] = field(default_factory=dict)
    edges: List[CallEdge] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    cycles: List[List[str]] = field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0


class CallGraphBuilder:
    """
    Builds call graphs from source code by analyzing function calls.
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.nodes: Dict[str, CallGraphNode] = {}
        self.edges: List[CallEdge] = []

    def build_call_graph(self, symbol_extractor_result=None) -> CallGraph:
        """
        Build a call graph for the repository.

        Args:
            symbol_extractor_result: Optional result from SymbolExtractor to reuse symbols

        Returns:
            CallGraph object representing the call relationships in the codebase
        """
        self.nodes.clear()
        self.edges.clear()

        # First, identify all functions and methods (nodes)
        self._identify_functions(symbol_extractor_result)

        # Then, analyze function bodies to find calls (edges)
        self._analyze_function_calls(symbol_extractor_result)

        # Identify entry points
        self._identify_entry_points()

        # Detect cycles
        self._detect_cycles()

        # Calculate statistics
        self._calculate_statistics()

        return CallGraph(
            nodes=self.nodes.copy(),
            edges=self.edges.copy(),
            entry_points=self._get_entry_point_names(),
            cycles=self.cycles,
            total_nodes=len(self.nodes),
            total_edges=len(self.edges)
        )

    def _identify_functions(self, symbol_extractor_result=None) -> None:
        """Identify all functions and methods to create nodes."""
        if symbol_extractor_result and hasattr(symbol_extractor_result, 'symbols'):
            # Use pre-extracted symbols if available
            for symbol in symbol_extractor_result.symbols:
                if symbol.symbol_type in ['function', 'method', 'staticmethod', 'classmethod',
                                          'async_function']:
                    self._add_function_node(symbol)
        else:
            # Extract symbols ourselves
            from .symbol_extractor import SymbolExtractor
            extractor = SymbolExtractor(str(self.repo_path))
            symbols_result = extractor.extract_symbols()
            for symbol in symbols_result.symbols:
                if symbol.symbol_type in ['function', 'method', 'staticmethod', 'classmethod',
                                          'async_function']:
                    self._add_function_node(symbol)

    def _add_function_node(self, symbol) -> None:
        """Add a function/method as a node in the call graph."""
        # Create a unique identifier for the function
        if symbol.parent:
            # Method: ClassName.methodName
            func_id = f"{symbol.parent}.{symbol.name}"
            display_name = f"{symbol.parent}.{symbol.name}"
        else:
            # Function: just the name (might need disambiguation)
            func_id = f"{symbol.file_path}::{symbol.name}"
            display_name = symbol.name

        # Handle potential name collisions by including file path
        func_id = f"{symbol.file_path}::{symbol.name}"
        if symbol.parent:
            func_id = f"{symbol.file_path}::{symbol.parent}.{symbol.name}"

        self.nodes[func_id] = CallGraphNode(
            name=display_name,
            function_type=symbol.symbol_type,
            file_path=symbol.file_path,
            line_number=symbol.line_number,
            is_public_api=self._is_public_api(symbol),
            complexity=self._estimate_complexity(symbol)
        )

    def _is_public_api(self, symbol) -> bool:
        """Determine if a function/method is part of the public API."""
        # Simple heuristic: public if not starting with _
        if hasattr(symbol, 'name') and not symbol.name.startswith('_'):
            return True
        # Check for public modifiers
        if hasattr(symbol, 'modifiers'):
            return 'public' in symbol.modifiers
        return False

    def _estimate_complexity(self, symbol) -> int:
        """Estimate cyclomatic complexity (simplified)."""
        # This would be more accurate with actual AST analysis
        # For now, return a basic estimate
        return 1  # Base complexity

    def _analyze_function_calls(self, symbol_extractor_result=None) -> None:
        """Analyze function bodies to find calls to other functions."""
        if symbol_extractor_result and hasattr(symbol_extractor_result, 'symbols'):
            # Use pre-extracted symbols
            symbols_by_file = defaultdict(list)
            for symbol in symbol_extractor_result.symbols:
                symbols_by_file[symbol.file_path].append(symbol)
        else:
            # Extract symbols ourselves
            from .symbol_extractor import SymbolExtractor
            extractor = SymbolExtractor(str(self.repo_path))
            symbols_result = extractor.extract_symbols()
            symbols_by_file = defaultdict(list)
            for symbol in symbols_result.symbols:
                symbols_by_file[symbol.file_path].append(symbol)

        # Process each file
        for file_path, symbols in symbols_by_file.items():
            full_path = self.repo_path / file_path
            if not full_path.exists():
                continue

            try:
                # Parse based on file type
                if file_path.endswith('.py'):
                    self._analyze_python_calls(file_path, full_path, symbols_by_file)
                elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
                    self._analyze_js_ts_calls(file_path, full_path, symbols_by_file)
                elif file_path.endswith('.java'):
                    self._analyze_java_calls(file_path, full_path, symbols_by_file)
                # Add more language parsers as needed
            except Exception as e:
                logger.warning(f"Failed to analyze calls in {file_path}: {e}")

    def _analyze_python_calls(self, relative_path: str, full_path: Path,
                            symbols_by_file: Dict[str, List]) -> None:
        """Analyze Python function calls using AST."""
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(full_path))
        except SyntaxError as e:
            logger.warning(f"Syntax error in Python file {relative_path}: {e}")
            return

        # Find all function definitions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name
                # Find the class if this is a method
                class_name = None
                # We'd need to walk the tree to find the parent class - simplified for now
                func_id = f"{relative_path}::{func_name}"
                # Look for exact match in nodes (this is simplified)
                caller_node = None
                for nid, node_obj in self.nodes.items():
                    if node_obj.name == func_name and node_obj.file_path == relative_path:
                        caller_node = node_obj
                        break

                if not caller_node:
                    continue

                # Find all function calls in this function's body
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        called_func = self._resolve_function_call(child, node, relative_path)
                        if called_func:
                            # Try to find the callee in our nodes
                            callee_node = self._find_function_node(called_func, relative_path)
                            if callee_node:
                                self._add_call_edge(caller_node, callee_node, child.lineno)

    def _resolve_function_call(self, call_node: ast.Call, context_node: ast.AST,
                             current_file: str) -> Optional[str]:
        """Resolve what function is being called."""
        if isinstance(call_node.func, ast.Name):
            # Direct function call: func()
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            # Method call: obj.method() or module.function()
            if isinstance(call_node.func.value, ast.Name):
                # obj.method() - we'd need to know what obj is
                # For now, return the attribute name
                return call_node.func.attr
            # TODO: Handle more complex cases like module.function()
        return None

    def _find_function_node(self, function_name: str, current_file: str) -> Optional[CallGraphNode]:
        """Find a function node by name, preferably in the same file."""
        # First try exact match in same file
        for node_id, node in self.nodes.items():
            if (node.name == function_name and
                node.file_path == current_file):
                return node

        # Then try any file with matching name
        for node in self.nodes.values():
            if node.name == function_name:
                return node

        return None

    def _add_call_edge(self, caller: CallGraphNode, callee: CallGraphNode,
                      line_number: int) -> None:
        """Add a call edge from caller to callee."""
        # Create edge identifier to avoid duplicates
        edge_id = f"{caller.name}->{callee.name}@{line_number}"

        # Check if we already have this edge (simplified deduplication)
        duplicate = False
        for edge in self.edges:
            if (edge.caller == caller.name and
                edge.callee == callee.name and
                abs(edge.caller_line - line_number) < 2):  # Close line numbers
                duplicate = True
                break

        if not duplicate:
            edge = CallEdge(
                caller=caller.name,
                callee=callee.name,
                caller_file=caller.file_path,
                callee_file=callee.file_path,
                caller_line=line_number,
                callee_line=callee.line_number,
                call_type="direct"
            )
            self.edges.append(edge)

            # Update node connections
            if callee.name not in caller.calls:
                caller.calls.append(callee.name)
            if caller.name not in callee.called_by:
                callee.called_by.append(caller.name)

    def _analyze_js_ts_calls(self, relative_path: str, full_path: Path,
                           symbols_by_file: Dict[str, List]) -> None:
        """Analyze JavaScript/TypeScript function calls (simplified)."""
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find function declarations
        function_patterns = [
            r'function\s+(\w+)\s*\(',  # function foo()
            r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>',  # const foo = () =>
            r'(?:const|let|var)\s+(\w+)\s*=\s*function\s*\(',  # const foo = function()
            r'(\w+)\s*:\s*(?:async\s+)?function\s*\(',  # foo: function()
        ]

        for pattern in function_patterns:
            for match in re.finditer(pattern, content):
                func_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1

                # Find function body to analyze for calls
                # This is simplified - real JS parsing is much more complex
                func_id = f"{relative_path}::{func_name}"
                caller_node = None
                for node_id, node in self.nodes.items():
                    if (node.name == func_name and
                        node.file_path == relative_path):
                        caller_node = node
                        break

                if caller_node:
                    # Find function calls in the vicinity (simplified)
                    call_pattern = r'(\w+)\s*\('
                    # Look in a reasonable range around the function definition
                    search_start = max(0, match.start() - 1000)
                    search_end = min(len(content), match.end() + 2000)
                    search_area = content[search_start:search_end]

                    for call_match in re.finditer(call_pattern, search_area):
                        called_name = call_match.group(1)
                        # Skip common language constructs
                        if called_name not in ['if', 'for', 'while', 'switch', 'return',
                                             'typeof', 'instanceof', 'new', 'delete',
                                             'function', 'var', 'let', 'const']:
                            callee_node = self._find_function_node(called_name, relative_path)
                            if callee_node:
                                call_line = content[:call_match.start()].count('\n') + 1
                                self._add_call_edge(caller_node, callee_node, call_line)

    def _analyze_java_calls(self, relative_path: str, full_path: Path,
                          symbols_by_file: Dict[str, List]) -> None:
        """Analyze Java method calls (simplified)."""
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find method declarations
        method_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:static\s+)?[\w\<\>\[\]]+\s+(\w+)\s*\([^)]*\)\s*\{'
        for match in re.finditer(method_pattern, content):
            method_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Find method body (simplified brace matching)
            brace_count = 0
            method_start = match.end()
            i = method_start
            while i < len(content):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        method_end = i
                        break
                i += 1
            else:
                method_end = len(content)

            method_body = content[method_start:method_end]

            # Find caller node
            caller_node = None
            for node_id, node in self.nodes.items():
                if (node.name == method_name and
                    node.file_path == relative_path):
                    caller_node = node
                    break

            if caller_node:
                # Find method calls in the body
                call_pattern = r'(\w+)\s*\('
                for call_match in re.finditer(call_pattern, method_body):
                    called_name = call_match.group(1)
                    # Skip Java keywords and common types
                    if called_name not in ['if', 'for', 'while', 'do', 'switch', 'return',
                                         'instanceof', 'new', 'try', 'catch', 'finally',
                                         'synchronized', 'return', 'void', 'int', 'String',
                                         'boolean', 'double', 'float', 'long', 'char']:
                        # Calculate absolute line number
                        lines_before = content[:method_start].count('\n')
                        call_line = lines_before + call_match.start() // 80 + 1  # Rough estimate
                        callee_node = self._find_function_node(called_name, relative_path)
                        if callee_node:
                            self._add_call_edge(caller_node, callee_node, call_line)

    def _identify_entry_points(self) -> None:
        """Identify potential entry points in the application."""
        for node_id, node in self.nodes.items():
            # Common entry point patterns
            if (node.name in ['main', 'Main'] or
                'main' in node.name.lower() or
                node.is_public_api and len(node.called_by) == 0):  # Public but not called by anything
                node.is_entry_point = True

    def _detect_cycles(self) -> None:
        """Detect cycles in the call graph using DFS."""
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node_id: str):
            if node_id in rec_stack:
                # Found a cycle
                cycle_start = path.index(node_id)
                cycle = path[cycle_start:] + [node_id]
                self.cycles.append(cycle)
                return

            if node_id in visited:
                return

            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            # Visit neighbors (functions this function calls)
            if node_id in self.nodes:
                node = self.nodes[node_id]
                for called_func_name in node.calls:
                    # Find the node ID for the called function
                    for nid, n in self.nodes.items():
                        if n.name == called_func_name and n.file_path == node.file_path:
                            dfs(nid)
                            break

            rec_stack.remove(node_id)
            path.pop()

        # Start DFS from each unvisited node
        for node_id in list(self.nodes.keys()):
            if node_id not in visited:
                dfs(node_id)

    def _calculate_statistics(self) -> None:
        """Calculate additional statistics for the call graph."""
        # Already calculated in constructor, but could add more here
        pass

    def _get_entry_point_names(self) -> List[str]:
        """Get names of identified entry points."""
        entry_points = []
        for node_id, node in self.nodes.items():
            if node.is_entry_point:
                entry_points.append(node.name)
        return entry_points

    def get_call_graph_summary(self) -> Dict[str, Any]:
        """Get a summary of the call graph."""
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "entry_points": len(self._get_entry_point_names()),
            "cycles_detected": len(self.cycles),
            "most_called": self._get_most_called_functions(),
            "callers_with_most_calls": self._get_callers_with_most_calls()
        }

    def _get_most_called_functions(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get functions that are called the most."""
        call_count = defaultdict(int)
        for edge in self.edges:
            call_count[edge.callee] += 1

        return sorted(call_count.items(), key=lambda x: x[1], reverse=True)[:limit]

    def _get_callers_with_most_calls(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get functions that make the most calls."""
        call_count = defaultdict(int)
        for edge in self.edges:
            call_count[edge.caller] += 1

        return sorted(call_count.items(), key=lambda x: x[1], reverse=True)[:limit]