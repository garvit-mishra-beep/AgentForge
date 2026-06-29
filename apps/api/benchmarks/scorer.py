"""Deterministic scorer for generated code against a labeled rubric.

The scorer is the honest core of the benchmark: given an agent's free-text
output and a task rubric, it produces a reproducible 0..1 score with a per-check
breakdown. No LLM is involved in scoring, so results are stable and auditable.

Checks (Python):
  - extraction:   a fenced/derivable code block exists
  - must_define:  required functions/classes are defined (AST)
  - required:     required substrings present (``required_any`` => at least one)
  - forbidden:    none of the forbidden substrings present
  - tests:        rubric assertions pass when executed in a subprocess sandbox
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_code(output: str, language: str = "python") -> str:
    """Pull a code block out of an agent's output.

    Prefers fenced blocks; also handles outputs that embed a JSON
    ``{"files": [{"content": ...}]}`` builder payload; falls back to the raw
    text (it may already be bare code).
    """
    if not output:
        return ""
    blocks = _FENCE_RE.findall(output)
    if blocks:
        # Concatenate all python blocks (helpers may be split across fences).
        return "\n\n".join(b.strip() for b in blocks)

    # Builder-style JSON payload with file contents.
    if '"files"' in output and "content" in output:
        import json

        start = output.find("{")
        end = output.rfind("}")
        if start != -1 and end != -1:
            try:
                data = json.loads(output[start : end + 1])
                files = data.get("files") or []
                code = "\n\n".join(
                    f.get("content", "") for f in files if isinstance(f, dict)
                )
                if code.strip():
                    return code
            except (ValueError, TypeError):
                pass

    return output.strip()


def _defined_names(code: str) -> set[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names


@dataclass
class CheckResult:
    name: str
    passed: bool
    weight: float
    detail: str = ""


@dataclass
class ScoreResult:
    task_id: str
    score: float
    passed: bool
    checks: list[CheckResult] = field(default_factory=list)
    code_chars: int = 0

    def as_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "score": round(self.score, 4),
            "passed": self.passed,
            "code_chars": self.code_chars,
            "checks": [
                {"name": c.name, "passed": c.passed, "weight": c.weight, "detail": c.detail}
                for c in self.checks
            ],
        }


def _run_tests_sandbox(code: str, tests: str, timeout: float = 10.0) -> tuple[bool, str]:
    """Execute ``code`` + ``tests`` in a separate Python process.

    Isolation is via a subprocess (no network needed, bounded by timeout). This
    is not a hardened security sandbox â€” the dataset is trusted â€” but it prevents
    a hung/exiting snippet from taking down the harness.
    """
    script = f"{code}\n\n# --- rubric tests ---\n{tests}\n"
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "candidate.py"
        path.write_text(script, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, str(path)],
                capture_output=True, text=True, timeout=timeout,
                cwd=td,
            )
        except subprocess.TimeoutExpired:
            return False, "timeout"
        if proc.returncode == 0:
            return True, "ok"
        return False, (proc.stderr or proc.stdout or "nonzero exit").strip().splitlines()[-1:][0] if (proc.stderr or proc.stdout) else "failed"


# Weights for each check category (normalized at the end).
_WEIGHTS = {"extraction": 1.0, "must_define": 2.0, "required": 1.0, "forbidden": 1.0, "tests": 5.0}


def score_output(task: dict, output: str, run_tests: bool = True) -> ScoreResult:
    """Score one agent output against one task's rubric."""
    rubric = task.get("rubric", {})
    language = task.get("language", "python")
    code = extract_code(output, language)
    checks: list[CheckResult] = []

    # 1. Extraction
    extracted = bool(code.strip())
    checks.append(CheckResult("extraction", extracted, _WEIGHTS["extraction"]))

    # 2. must_define (AST)
    must_define = rubric.get("must_define", [])
    if must_define:
        defined = _defined_names(code)
        missing = [n for n in must_define if n not in defined]
        checks.append(CheckResult(
            "must_define", not missing, _WEIGHTS["must_define"],
            detail="" if not missing else f"missing: {missing}",
        ))

    # 3. required substrings
    required = rubric.get("required", [])
    if required:
        any_mode = rubric.get("required_any", False)
        present = [r for r in required if r in code]
        ok = bool(present) if any_mode else len(present) == len(required)
        checks.append(CheckResult(
            "required", ok, _WEIGHTS["required"],
            detail="" if ok else f"have {present} of {required}",
        ))

    # 4. forbidden substrings
    forbidden = rubric.get("forbidden", [])
    if forbidden:
        hits = [f for f in forbidden if f in code]
        checks.append(CheckResult(
            "forbidden", not hits, _WEIGHTS["forbidden"],
            detail="" if not hits else f"found: {hits}",
        ))

    # 5. tests (sandboxed)
    tests = rubric.get("tests")
    if tests and run_tests:
        ok, detail = (_run_tests_sandbox(code, tests) if extracted else (False, "no code"))
        checks.append(CheckResult("tests", ok, _WEIGHTS["tests"], detail=detail))

    total_w = sum(c.weight for c in checks) or 1.0
    earned = sum(c.weight for c in checks if c.passed)
    score = earned / total_w
    # "passed" requires the heavily-weighted functional test (if present) to pass.
    test_check = next((c for c in checks if c.name == "tests"), None)
    passed = (test_check.passed if test_check else score >= 0.99)
    return ScoreResult(task["id"], score, passed, checks, code_chars=len(code))


def load_dataset(path: str | Path | None = None) -> list[dict]:
    """Load the labeled JSONL dataset."""
    import json

    if path is None:
        path = Path(__file__).parent / "dataset" / "tasks.jsonl"
    path = Path(path)
    tasks = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            tasks.append(json.loads(line))
    return tasks


if __name__ == "__main__":  # tiny self-test
    ds = load_dataset()
    good = "```python\ndef fib(n):\n    a,b=0,1\n    for _ in range(n): a,b=b,a+b\n    return a\n```"
    res = score_output(ds[0], good)
    print(f"self-test fib -> score={res.score:.2f} passed={res.passed}")
    assert res.passed, "fib reference solution should pass"
    print("OK")
