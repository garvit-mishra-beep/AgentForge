"""
Repository File Parser
Parses code files to extract symbols, imports, and chunks.
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "jsx",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sql": "sql",
    ".sh": "bash",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".less": "less",
    ".vue": "vue",
    ".svelte": "svelte",
}


@dataclass
class CodeSymbol:
    symbol_type: str          # function, class, method, variable, interface, type
    name: str
    line_start: int
    line_end: int
    signature: str = ""
    docstring: str = ""
    visibility: str = "public"
    metadata: dict = field(default_factory=dict)


@dataclass
class CodeImport:
    source: str
    alias: str = ""
    is_relative: bool = False
    line_number: int = 0


@dataclass
class CodeChunk:
    chunk_type: str           # function, class, method, block
    name: str
    content: str
    line_start: int
    line_end: int
    tokens_estimate: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class ParsedFile:
    file_id: str
    file_path: str
    language: str
    symbols: list[CodeSymbol]
    imports: list[CodeImport]
    chunks: list[CodeChunk]


def detect_language(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return LANGUAGE_MAP.get(ext, "")


def _count_tokens_estimate(text: str) -> int:
    """Rough token estimation: ~4 chars per token."""
    return len(text) // 4


# ── Python Parser ────────────────────────────────────────────────────────

def _parse_python(content: str) -> tuple[list[CodeSymbol], list[CodeImport], list[CodeChunk]]:
    symbols: list[CodeSymbol] = []
    imports: list[CodeImport] = []
    chunks: list[CodeChunk] = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return symbols, imports, chunks

    for node in ast.walk(tree):
        # Imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(CodeImport(
                    source=alias.name,
                    alias=alias.asname or "",
                    line_number=node.lineno if hasattr(node, "lineno") else 0,
                ))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(CodeImport(
                    source=f"{module}.{alias.name}" if module else alias.name,
                    alias=alias.asname or "",
                    is_relative=bool(node.level),
                    line_number=node.lineno if hasattr(node, "lineno") else 0,
                ))

        # Functions
        if isinstance(node, ast.FunctionDef):
            sig = f"def {node.name}({', '.join(a.arg for a in node.args.args)})"
            if node.args.vararg:
                sig += f", *{node.args.vararg.arg}"
            if node.args.kwonlyargs:
                sig += f", *{', '.join(a.arg for a in node.args.kwonlyargs)}"
            if node.args.kwarg:
                sig += f", **{node.args.kwarg.arg}"
            doc = ast.get_docstring(node) or ""
            start = node.lineno
            end = node.end_lineno or start
            symbols.append(CodeSymbol(
                symbol_type="function",
                name=node.name,
                line_start=start,
                line_end=end,
                signature=sig,
                docstring=doc.split("\n")[0] if doc else "",
            ))
            chunk_content = "\n".join(content.splitlines()[start-1:end])
            chunks.append(CodeChunk(
                chunk_type="function",
                name=node.name,
                content=chunk_content,
                line_start=start,
                line_end=end,
                tokens_estimate=_count_tokens_estimate(chunk_content),
            ))

        # Classes
        if isinstance(node, ast.ClassDef):
            bases = [b.id if isinstance(b, ast.Name) else "" for b in node.bases]
            sig = f"class {node.name}({', '.join(filter(None, bases))})" if bases else f"class {node.name}"
            doc = ast.get_docstring(node) or ""
            start = node.lineno
            end = node.end_lineno or start
            symbols.append(CodeSymbol(
                symbol_type="class",
                name=node.name,
                line_start=start,
                line_end=end,
                signature=sig,
                docstring=doc.split("\n")[0] if doc else "",
            ))
            chunk_content = "\n".join(content.splitlines()[start-1:end])
            chunks.append(CodeChunk(
                chunk_type="class",
                name=node.name,
                content=chunk_content,
                line_start=start,
                line_end=end,
                tokens_estimate=_count_tokens_estimate(chunk_content),
            ))

            # Methods
            for item in ast.iter_child_nodes(node):
                if isinstance(item, ast.FunctionDef):
                    m_sig = f"def {item.name}({', '.join(a.arg for a in item.args.args)})"
                    m_doc = ast.get_docstring(item) or ""
                    m_start = item.lineno
                    m_end = item.end_lineno or m_start
                    symbols.append(CodeSymbol(
                        symbol_type="method",
                        name=f"{node.name}.{item.name}",
                        line_start=m_start,
                        line_end=m_end,
                        signature=m_sig,
                        docstring=m_doc.split("\n")[0] if m_doc else "",
                        visibility="public" if not item.name.startswith("_") else "private",
                    ))
                    chunk_content = "\n".join(content.splitlines()[m_start-1:m_end])
                    chunks.append(CodeChunk(
                        chunk_type="method",
                        name=f"{node.name}.{item.name}",
                        content=chunk_content,
                        line_start=m_start,
                        line_end=m_end,
                        tokens_estimate=_count_tokens_estimate(chunk_content),
                    ))

    return symbols, imports, chunks


# ── Generic Regex-based Parser ───────────────────────────────────────────

# Patterns for common languages
PATTERNS = {
    "function": re.compile(
        r"(?:export\s+)?(?:async\s+)?(?:function\s+)(\w+)\s*\(([^)]*)\)",
        re.MULTILINE,
    ),
    "arrow_function": re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*=>",
        re.MULTILINE,
    ),
    "class": re.compile(
        r"(?:export\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[^{]+)?",
        re.MULTILINE,
    ),
    "interface": re.compile(
        r"(?:export\s+)?interface\s+(\w+)",
        re.MULTILINE,
    ),
    "type": re.compile(
        r"(?:export\s+)?type\s+(\w+)\s*=",
        re.MULTILINE,
    ),
    "import": re.compile(
        r"(?:import\s+(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)(?:\s*,\s*\{[^}]*\})?\s+from\s+['\"]([^'\"]+)['\"]|import\s+['\"]([^'\"]+)['\"])",
        re.MULTILINE,
    ),
    "require": re.compile(
        r"(?:const|let|var)\s+\w+\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        re.MULTILINE,
    ),
    "function_go": re.compile(
        r"func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(([^)]*)\)",
        re.MULTILINE,
    ),
    "function_rust": re.compile(
        r"(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*\(([^)]*)\)",
        re.MULTILINE,
    ),
    "struct_rust": re.compile(
        r"(?:pub\s+)?struct\s+(\w+)",
        re.MULTILINE,
    ),
    "impl_rust": re.compile(
        r"(?:pub\s+)?impl\s+(\w+)",
        re.MULTILINE,
    ),
}


def _parse_generic(content: str, language: str, filename: str) -> tuple[list[CodeSymbol], list[CodeImport], list[CodeChunk]]:
    symbols: list[CodeSymbol] = []
    imports: list[CodeImport] = []
    chunks: list[CodeChunk] = []
    lines = content.splitlines()

    # Pick patterns based on language
    active_patterns = {}

    if language in ("javascript", "jsx", "typescript", "tsx", "vue"):
        active_patterns = {
            "function": PATTERNS["function"],
            "arrow_function": PATTERNS["arrow_function"],
            "class": PATTERNS["class"],
            "interface": PATTERNS["interface"],
            "type": PATTERNS["type"],
            "import": PATTERNS["import"],
            "require": PATTERNS["require"],
        }
    elif language == "go":
        active_patterns = {
            "function_go": PATTERNS["function_go"],
            "import": PATTERNS["import"],
        }
    elif language == "rust":
        active_patterns = {
            "function_rust": PATTERNS["function_rust"],
            "struct_rust": PATTERNS["struct_rust"],
            "impl_rust": PATTERNS["impl_rust"],
            "import": PATTERNS["import"],
        }
    else:
        active_patterns = {
            "function": PATTERNS["function"],
            "class": PATTERNS["class"],
        }

    seen_names: set[str] = set()

    for sym_type, pattern in active_patterns.items():
        for match in pattern.finditer(content):
            name = match.group(1)
            if name in seen_names:
                continue
            seen_names.add(name)

            line_no = content[:match.start()].count("\n") + 1
            sig = match.group(0).strip()

            if sym_type in ("import", "require"):
                source = match.group(1) or match.group(2) or ""
                imports.append(CodeImport(
                    source=source,
                    alias="",
                    line_number=line_no,
                ))
                continue

            found_type = sym_type.replace("_go", "").replace("_rust", "")
            symbols.append(CodeSymbol(
                symbol_type=found_type,
                name=name,
                line_start=line_no,
                line_end=line_no,
                signature=sig,
            ))

            # Extract chunk: from this match to next blank line or end
            chunk_lines: list[str] = []
            for i in range(line_no - 1, len(lines)):
                chunk_lines.append(lines[i])
                if i > line_no and lines[i].strip() == "":
                    break
                if i - line_no > 200:  # max chunk size
                    break
            chunk_content = "\n".join(chunk_lines)
            chunks.append(CodeChunk(
                chunk_type=found_type,
                name=name,
                content=chunk_content,
                line_start=line_no,
                line_end=line_no + len(chunk_lines) - 1,
                tokens_estimate=_count_tokens_estimate(chunk_content),
            ))

    return symbols, imports, chunks


# ── Public API ───────────────────────────────────────────────────────────

def parse_file(file_id: str, file_path: str, content: str | None = None) -> ParsedFile:
    """
    Parse a file and extract code structure.

    If content is None, reads the file from disk.
    """
    path = Path(file_path)
    if content is None:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            content = ""
        except Exception:
            content = ""

    language = detect_language(file_path)
    symbols: list[CodeSymbol] = []
    imports: list[CodeImport] = []
    chunks: list[CodeChunk] = []

    if not content.strip():
        return ParsedFile(
            file_id=file_id,
            file_path=file_path,
            language=language,
            symbols=symbols,
            imports=imports,
            chunks=chunks,
        )

    if language == "python":
        symbols, imports, chunks = _parse_python(content)
    elif language:
        symbols, imports, chunks = _parse_generic(content, language, path.name)
    else:
        # Unknown language - try regex anyway
        symbols, imports, chunks = _parse_generic(content, "", path.name)

    return ParsedFile(
        file_id=file_id,
        file_path=file_path,
        language=language,
        symbols=symbols,
        imports=imports,
        chunks=chunks,
    )
