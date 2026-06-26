"""Tests for file parser edge cases."""

import tempfile
from pathlib import Path

from app.file_parser import parse_file, detect_language


def test_detect_language_known_extensions():
    assert detect_language("main.py") == "python"
    assert detect_language("app.js") == "javascript"
    assert detect_language("styles.css") == "css"
    assert detect_language("index.html") == "html"
    assert detect_language("schema.sql") == "sql"


def test_detect_language_unknown():
    result = detect_language("Makefile")
    assert result == ""  # Unknown extensions return empty string
    assert detect_language("notes.txt") == ""


def test_parse_empty_file():
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("")
        path = f.name
    try:
        result = parse_file("test-id", path)
        assert result.language == "python"
        assert result.symbols == []
        assert result.imports == []
    finally:
        Path(path).unlink(missing_ok=True)


def test_parse_python_with_symbols():
    code = '''
import os
import sys

class MyClass:
    def my_method(self):
        pass

def my_function():
    """Docstring."""
    return 42
'''
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        result = parse_file("test-id", path)
        assert result.language == "python"
        assert len(result.imports) == 2
        assert any(i.source == "os" for i in result.imports)
        assert any(i.source == "sys" for i in result.imports)
        assert len(result.symbols) >= 2
        assert any(s.name == "MyClass" for s in result.symbols)
        assert any(s.name == "my_function" for s in result.symbols)
    finally:
        Path(path).unlink(missing_ok=True)


def test_parse_non_python_file():
    code = '{"key": "value"}'
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        result = parse_file("test-id", path)
        assert result.language == "json"
    finally:
        Path(path).unlink(missing_ok=True)


def test_parse_large_python_no_crash():
    code = "\n".join(f"x{i} = {i}" for i in range(10000))
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        result = parse_file("test-id", path)
        assert result.language == "python"
    finally:
        Path(path).unlink(missing_ok=True)


def test_parse_python_with_syntax_error():
    code = "def broken(\n    pass\n"
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        result = parse_file("test-id", path)
        assert result.language == "python"
    finally:
        Path(path).unlink(missing_ok=True)


def test_parse_nonexistent_file():
    result = parse_file("test-id", "/nonexistent/path/file.py")
    # Language is detected from path extension even if file doesn't exist
    assert result.symbols == []
    assert result.imports == []


def test_parse_binary_bytes():
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(b"\x00\x01\x02\x03")
        path = f.name
    try:
        result = parse_file("test-id", path)
        assert result is not None
    finally:
        Path(path).unlink(missing_ok=True)
