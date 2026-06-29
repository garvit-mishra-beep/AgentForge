"""
Symbol Extractor for AgentForge.
Extracts symbols (classes, functions, interfaces, etc.) from source code files.
"""
import ast
import re
import os
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Symbol:
    """Represents a code symbol (function, class, etc.)."""
    name: str
    symbol_type: str  # 'class', 'function', 'method', 'interface', 'enum', 'variable', etc.
    file_path: str
    line_number: int
    column_number: int
    end_line_number: Optional[int] = None
    end_column_number: Optional[int] = None
    signature: Optional[str] = None
    docstring: Optional[str] = None
    modifiers: List[str] = field(default_factory=list)  # public, private, static, etc.
    parent: Optional[str] = None  # Parent class or namespace
    is_async: bool = False
    is_static: bool = False
    is_abstract: bool = False
    return_type: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SymbolExtractionResult:
    """Results of symbol extraction."""
    symbols: List[Symbol] = field(default_factory=list)
    files_processed: int = 0
    total_symbols: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_file: Dict[str, List[str]] = field(default_factory=dict)


class SymbolExtractor:
    """
    Extracts symbols from source code files using language-specific parsers.
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.symbols: List[Symbol] = []

    def extract_symbols(self, file_patterns: Optional[List[str]] = None) -> SymbolExtractionResult:
        """
        Extract symbols from source code files in the repository.

        Args:
            file_patterns: Optional list of file patterns to include (e.g., ['*.py', '*.js'])
                          If None, uses default set of programming language files

        Returns:
            SymbolExtractionResult containing all extracted symbols
        """
        self.symbols.clear()

        # Default file patterns for common programming languages
        if file_patterns is None:
            file_patterns = [
                '*.py',           # Python
                '*.js', '*.jsx',  # JavaScript
                '*.ts', '*.tsx',  # TypeScript
                '*.java',         # Java
                '*.cpp', '*.c', '*.h', '*.hpp',  # C/C++
                '*.cs',           # C#
                '*.go',           # Go
                '*.rs',           # Rust
                '*.php',          # PHP
                '*.rb',           # Ruby
                '*.swift',        # Swift
                '*.kt',           # Kotlin
                '*.scala',        # Scala
            ]

        # Find all matching files
        files_to_process = []
        for pattern in file_patterns:
            # Handle both simple extensions and glob patterns
            if '*' in pattern:
                import glob
                matches = glob.glob(str(self.repo_path / '**' / pattern), recursive=True)
                for match in matches:
                    if not self._should_skip_file(Path(match)):
                        files_to_process.append(Path(match))
            else:
                # Direct file match
                matches = list(self.repo_path.rglob(pattern))
                for match in matches:
                    if not self._should_skip_file(match):
                        files_to_process.append(match)

        # Process each file
        for file_path in files_to_process:
            try:
                self._extract_symbols_from_file(file_path)
            except Exception as e:
                logger.warning(f"Failed to extract symbols from {file_path}: {e}")

        # Organize results
        result = SymbolExtractionResult()
        result.symbols = self.symbols.copy()
        result.files_processed = len(files_to_process)
        result.total_symbols = len(self.symbols)

        # Group by type
        for symbol in self.symbols:
            if symbol.symbol_type not in result.by_type:
                result.by_type[symbol.symbol_type] = 0
            result.by_type[symbol.symbol_type] += 1

        # Group by file
        for symbol in self.symbols:
            if symbol.file_path not in result.by_file:
                result.by_file[symbol.file_path] = []
            result.by_file[symbol.file_path].append(symbol.name)

        return result

    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if a file should be skipped during symbol extraction."""
        skip_patterns = [
            # Directories
            'node_modules',
            '.git',
            '__pycache__',
            '.pytest_cache',
            'dist',
            'build',
            '.venv',
            'venv',
            'env',
            'vendor',
            'bower_components',
            # Minified files
            '.min.js',
            '.min.css',
            # Map files
            '.map',
            # Lock files
            'package-lock.json',
            'yarn.lock',
            'pnpm-lock.yaml',
            'Pipfile.lock',
            'poetry.lock',
            'Cargo.lock',
            'Gemfile.lock',
            # Generated files (common patterns)
            '.generated.',
            '_generated.',
            '.pb.go',  # Protocol Buffers generated Go
        ]

        path_str = str(file_path)
        for pattern in skip_patterns:
            if pattern in path_str:
                return True

        # Skip files in certain directories
        parts = file_path.parts
        skip_dirs = {'node_modules', '.git', '__pycache__', '.pytest_cache', 'dist', 'build', 'vendor'}
        if any(part in skip_dirs for part in parts):
            return True

        return False

    def _extract_symbols_from_file(self, file_path: Path) -> None:
        """Extract symbols from a single file based on its extension."""
        relative_path = str(file_path.relative_to(self.repo_path))
        extension = file_path.suffix.lower()

        try:
            if extension == '.py':
                self._extract_python_symbols(file_path, relative_path)
            elif extension in ['.js', '.jsx', '.ts', '.tsx']:
                self._extract_javascript_typescript_symbols(file_path, relative_path)
            elif extension == '.java':
                self._extract_java_symbols(file_path, relative_path)
            elif extension in ['.cpp', '.c', '.h', '.hpp']:
                self._extract_c_cpp_symbols(file_path, relative_path)
            elif extension == '.cs':
                self._extract_csharp_symbols(file_path, relative_path)
            elif extension == '.go':
                self._extract_go_symbols(file_path, relative_path)
            elif extension == '.rs':
                self._extract_rust_symbols(file_path, relative_path)
            elif extension == '.php':
                self._extract_php_symbols(file_path, relative_path)
            elif extension == '.rb':
                self._extract_ruby_symbols(file_path, relative_path)
            elif extension == '.swift':
                self._extract_swift_symbols(file_path, relative_path)
            # Add more language parsers as needed
        except Exception as e:
            logger.warning(f"Error extracting symbols from {relative_path}: {e}")

    def _extract_python_symbols(self, file_path: Path, relative_path: str) -> None:
        """Extract symbols from Python files using AST."""
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read(), filename=str(file_path))
            except SyntaxError as e:
                logger.warning(f"Syntax error in Python file {relative_path}: {e}")
                return

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Class definition
                decorators = [self._get_source_slice(f.lineno, f.end_lineno, f.col_offset, f.end_col_offset)
                             for f in node.decorator_list if hasattr(f, 'lineno')]
                modifiers = []
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Name):
                        modifiers.append(dec.id)
                    elif isinstance(dec, ast.Attribute):
                        modifiers.append(dec.attr)

                self.symbols.append(Symbol(
                    name=node.name,
                    symbol_type='class',
                    file_path=relative_path,
                    line_number=node.lineno,
                    column_number=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', node.lineno),
                    end_column_number=getattr(node, 'end_col_offset', node.col_offset + len(node.name)),
                    decorator_list=decorators,
                    modifiers=modifiers,
                    docstring=ast.get_docstring(node)
                ))

                # Process methods within the class
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self._add_function_symbol(item, relative_path, node.name, is_method=True)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Function definition (not in a class)
                self._add_function_symbol(node, relative_path)

            elif isinstance(node, ast.AsyncFunctionDef):
                # Async function - handled above with FunctionDef check
                pass

    def _add_function_symbol(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
                           file_path: str, class_name: Optional[str] = None,
                           is_method: bool = False) -> None:
        """Add a function or method symbol."""
        # Get arguments
        args_info = []
        for arg in node.args.args:
            arg_info = {
                'name': arg.arg,
                'type': None  # Would need type annotation parsing for full type info
            }
            args_info.append(arg_info)

        # Handle *args and **kwargs
        if node.args.vararg:
            args_info.append({'name': '*' + node.args.vararg.arg, 'type': None})
        if node.args.kwarg:
            args_info.append({'name': '**' + node.args.kwarg.arg, 'type': None})

        # Get decorator info
        decorators = []
        modifiers = []
        is_static = False
        is_async = isinstance(node, ast.AsyncFunctionDef)

        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorator_name = dec.id
                decorators.append(decorator_name)
                if decorator_name in ['staticmethod', 'classmethod']:
                    modifiers.append(decorator_name)
                    if decorator_name == 'staticmethod':
                        is_static = True
            elif isinstance(dec, ast.Attribute):
                decorator_name = dec.attr
                decorators.append(decorator_name)
                if decorator_name in ['staticmethod', 'classmethod']:
                    modifiers.append(decorator_name)
                    if decorator_name == 'staticmethod':
                        is_static = True

        # Determine symbol type
        if is_method:
            symbol_type = 'method'
            if is_static:
                symbol_type = 'staticmethod'
            elif 'classmethod' in modifiers:
                symbol_type = 'classmethod'
        else:
            symbol_type = 'function'
            if is_async:
                symbol_type = 'async_function'

        self.symbols.append(Symbol(
            name=node.name,
            symbol_type=symbol_type,
            file_path=file_path,
            line_number=node.lineno,
            column_number=node.col_offset,
            end_line_number=getattr(node, 'end_lineno', node.lineno),
            end_column_number=getattr(node, 'end_col_offset', node.col_offset + len(node.name)),
            signature=self._get_function_signature(node),
            docstring=ast.get_docstring(node),
            modifiers=modifiers,
            parent=class_name,
            is_async=is_async,
            is_static=is_static,
            parameters=args_info
        ))

    def _get_function_signature(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
        """Generate a string representation of the function signature."""
        parts = []

        # Positional arguments
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                # Simplified annotation representation
                try:
                    ann_str = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)
                    arg_str += f": {ann_str}"
                except Exception:
                    arg_str += ": <type>"
            args.append(arg_str)

        # *args
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")

        # Keyword-only arguments
        for arg in node.args.kwonlyargs:
            arg_str = arg.arg
            if arg.annotation:
                try:
                    ann_str = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)
                    arg_str += f": {ann_str}"
                except Exception:
                    arg_str += ": <type>"
            args.append(arg_str)

        # **kwargs
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")

        # Returns
        returns = ""
        if node.returns:
            try:
                ret_str = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
                returns = f" -> {ret_str}"
            except Exception:
                returns = " -> <type>"

        return f"({', '.join(args)}){returns}"

    def _get_source_slice(self, start_line: int, end_line: int, start_col: int, end_col: int) -> str:
        """Get a slice of source code (placeholder - would need actual file reading)."""
        # This would need to read the actual file content to return the string
        # For now, returning a placeholder
        return f"<lines {start_line}-{end_line}>"

    # Placeholder methods for other languages - would be implemented similarly
    def _extract_javascript_typescript_symbols(self, file_path: Path, relative_path: str) -> None:
        """Extract symbols from JavaScript/TypeScript files."""
        # This would use a JS/TS parser like esprima or typescript compiler API
        # For now, we'll use regex-based extraction as a placeholder
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Simple regex for function declarations
        func_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)'
        for match in re.finditer(func_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=match.group(1),
                symbol_type='function',
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

        # Simple regex for class declarations
        class_pattern = r'(?:export\s+)?class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=match.group(1),
                symbol_type='class',
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

    def _extract_java_symbols(self, file_path: Path, relative_path: str) -> None:
        """Extract symbols from Java files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Class/interface/enum patterns
        class_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:abstract\s+|final\s+)?(class|interface|enum)\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            symbol_type = match.group(1).lower()
            name = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=name,
                symbol_type=symbol_type,
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

        # Method patterns
        method_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:final\s+)?[\w\<\>\[\]]+\s+(\w+)\s*\([^}]*\)\s*(?:throws\s+[\w\s,]+)?\{'
        for match in re.finditer(method_pattern, content):
            # This is a simplified pattern - real Java parsing is more complex
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=name,
                symbol_type='method',
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

    def _extract_c_cpp_symbols(self, file_path: Path, relative_path: str) -> None:
        """Extract symbols from C/C++ files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Class/struct patterns
        class_pattern = r'(?:typedef\s+)?(?:struct|class)\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=name,
                symbol_type='class',
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

        # Function patterns
        func_pattern = r'(?:inline\s+|static\s+|virtual\s+|explicit\s+)?[\w\~\:]+\s+(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{'
        for match in re.finditer(func_pattern, content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=name,
                symbol_type='function',
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

    def _extract_csharp_symbols(self, file_path: Path, relative_path: str) -> None:
        """Extract symbols from C# files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Namespace, class, struct, interface, enum patterns
        type_pattern = r'(?:public\s+|private\s+|protected\s+|internal\s+)?(?:new\s+|abstract\s+|sealed\s+|static\s+)?(?:class|struct|interface|enum)\s+(\w+)'
        for match in re.finditer(type_pattern, content):
            # Determine type from matched text
            match_text = match.group(0)
            if 'class' in match_text:
                symbol_type = 'class'
            elif 'struct' in match_text:
                symbol_type = 'struct'
            elif 'interface' in match_text:
                symbol_type = 'interface'
            elif 'enum' in match_text:
                symbol_type = 'enum'
            else:
                symbol_type = 'type'

            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=name,
                symbol_type=symbol_type,
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

        # Method patterns
        method_pattern = r'(?:public\s+|private\s+|protected\s+|internal\s+)?(?:static\s+|virtual\s+|abstract\s+|override\s+)?[\w\<\>\[\]]+\s+(\w+)\s*\([^)]*\)'
        for match in re.finditer(method_pattern, content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=name,
                symbol_type='method',
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

    def _extract_go_symbols(self, file_path: Path, relative_path: str) -> None:
        """Extract symbols from Go files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Function declarations
        func_pattern = r'func\s+(?:\([^)]*\)\s+)?(\w+)\s*\('
        for match in re.finditer(func_pattern, content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=name,
                symbol_type='function',
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

        # Type declarations (struct, interface)
        type_pattern = r'type\s+(\w+)\s+(struct|interface)'
        for match in re.finditer(type_pattern, content):
            name = match.group(1)
            type_str = match.group(2)
            symbol_type = 'struct' if type_str == 'struct' else 'interface'
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=name,
                symbol_type=symbol_type,
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

    def _extract_rust_symbols(self, file_path: Path, relative_path: str) -> None:
        """Extract symbols from Rust files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Function declarations
        func_pattern = r'fn\s+(\w+)\s*\<[^>]*\>\s*\([^)]*\)'
        for match in re.finditer(func_pattern, content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=name,
                symbol_type='function',
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

        # Struct/enum/trait definitions
        type_pattern = r'(pub\s+)?(struct|enum|trait)\s+(\w+)'
        for match in re.finditer(type_pattern, content):
            type_str = match.group(2)
            name = match.group(3)
            symbol_type = type_str.lower()
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=name,
                symbol_type=symbol_type,
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

        # Impl blocks
        impl_pattern = r'impl(?:<[^>]*>)?\s+(\w+(?:<[^>]*>)?)'
        for match in re.finditer(impl_pattern, content):
            # This is simplified - real impl parsing is more complex
            type_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=f"impl_{type_name}",
                symbol_type='impl',
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

    def _extract_php_symbols(self, file_path: Path, relative_path: str) -> None:
        """Extract symbols from PHP files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Class/interface/trait declarations
        type_pattern = r'(?:abstract\s+|final\s+)?(class|interface|trait)\s+(\w+)'
        for match in re.finditer(type_pattern, content):
            type_str = match.group(1).lower()
            name = match.group(2)
            symbol_type = type_str
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=name,
                symbol_type=symbol_type,
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

        # Function/method declarations
        method_pattern = r'(?:public\s+|private\s+|protected\s+|static\s+)?function\s+(\w+)\s*\('
        for match in re.finditer(method_pattern, content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=name,
                symbol_type='method',
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

    def _extract_ruby_symbols(self, file_path: Path, relative_path: str) -> None:
        """Extract symbols from Ruby files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Class/module definitions
        type_pattern = r'(class|module)\s+([A-Z][a-zA-Z0-9_]*)'
        for match in re.finditer(type_pattern, content):
            type_str = match.group(1)
            name = match.group(2)
            symbol_type = type_str.lower()
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=name,
                symbol_type=symbol_type,
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

        # Method definitions
        method_pattern = r'(?:def\s+|\|)\s*([a-zA-Z_][a-zA-Z0-9_]*(?|[?!]|=(?!=))?)'
        for match in re.finditer(method_pattern, content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=name,
                symbol_type='method',
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

    def _extract_swift_symbols(self, file_path: Path, relative_path: str) -> None:
        """Extract symbols from Swift files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Class/struct/enum/protocol definitions
        type_pattern = r'(?:public\s+|private\s+|internal\s+|fileprivate\s+)?(class|struct|enum|protocol)\s+(\w+)'
        for match in re.finditer(type_pattern, content):
            type_str = match.group(1)
            name = match.group(2)
            symbol_type = type_str.lower()
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=name,
                symbol_type=symbol_type,
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

        # Function/method declarations
        func_pattern = r'(?:public\s+|private\s+|internal\s+|fileprivate\s+)?(?:static\s+|class\s+)?func\s+(\w+)\s*\('
        for match in re.finditer(func_pattern, content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            self.symbols.append(Symbol(
                name=name,
                symbol_type='function',
                file_path=relative_path,
                line_number=line_num,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1
            ))

    def get_symbols_by_type(self, symbol_type: str) -> List[Symbol]:
        """Get all symbols of a specific type."""
        return [s for s in self.symbols if s.symbol_type == symbol_type]

    def get_symbols_by_file(self, file_path: str) -> List[Symbol]:
        """Get all symbols from a specific file."""
        return [s for s in self.symbols if s.file_path == file_path]

    def get_symbol_summary(self) -> Dict[str, Any]:
        """Get a summary of extracted symbols."""
        by_type = {}
        for symbol in self.symbols:
            if symbol.symbol_type not in by_type:
                by_type[symbol.symbol_type] = 0
            by_type[symbol.symbol_type] += 1

        by_file = {}
        for symbol in self.symbols:
            if symbol.file_path not in by_file:
                by_file[symbol.file_path] = []
            by_file[symbol.file_path].append(symbol.name)

        return {
            "total_symbols": len(self.symbols),
            "by_type": by_type,
            "by_file": {k: len(v) for k, v in by_file.items()},
            "files_with_symbols": len(by_file)
        }
