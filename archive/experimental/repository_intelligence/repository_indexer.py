"""
Repository Indexer for AgentForge.
Responsible for walking the repository and collecting basic file information.
"""
import os
import os.path
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field
import pathspec
import pathspec.patterns.gitwildmatch


@dataclass
class FileInfo:
    """Information about a file in the repository."""
    path: str
    absolute_path: str
    size: int
    modified_time: float
    is_file: bool
    is_directory: bool
    extension: str
    language: Optional[str] = None


class RepositoryIndexer:
    """
    Walks the repository and indexes files, respecting .gitignore patterns.
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.files: Dict[str, FileInfo] = {}
        self.directories: Set[str] = set()
        self._load_gitignore_patterns()

    def _load_gitignore_patterns(self) -> None:
        """Load .gitignore patterns to ignore during indexing."""
        gitignore_path = self.repo_path / ".gitignore"
        self.gitignore_patterns = []

        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                lines = f.readlines()
                self.gitignore_patterns = pathspec.patterns.gitwildmatch.GitWildMatchPattern \
                    .compile_lines(lines)
        else:
            self.gitignore_patterns = []

    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored based on .gitignore patterns."""
        try:
            relative_path = path.relative_to(self.repo_path)
            return self.gitignore_patterns.match_file(str(relative_path))
        except ValueError:
            # Path is not relative to repo_path
            return True

    def index_repository(self) -> Dict[str, FileInfo]:
        """
        Walk the repository and index all files.

        Returns:
            Dictionary mapping file paths to FileInfo objects
        """
        self.files.clear()
        self.directories.clear()

        for root, dirs, files in os.walk(self.repo_path):
            # Filter out ignored directories
            rel_root = Path(root).relative_to(self.repo_path)
            dirs[:] = [d for d in dirs if not self._should_ignore(Path(root) / d)]

            # Add directory to tracking
            self.directories.add(str(rel_root))

            for file in files:
                file_path = Path(root) / file

                # Skip if ignored
                if self._should_ignore(file_path):
                    continue

                # Get file info
                stat = file_path.stat()
                ext = file_path.suffix.lower()

                # Determine language based on extension
                language = self._detect_language(ext)

                file_info = FileInfo(
                    path=str(file_path.relative_to(self.repo_path)),
                    absolute_path=str(file_path),
                    size=stat.st_size,
                    modified_time=stat.st_mtime,
                    is_file=True,
                    is_directory=False,
                    extension=ext,
                    language=language
                )

                self.files[file_info.path] = file_info

        return self.files

    def _detect_language(self, extension: str) -> Optional[str]:
        """Detect programming language from file extension."""
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sh': 'shell',
            '.bash': 'bash',
            '.zsh': 'zsh',
            '.fish': 'fish',
            '.sql': 'sql',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'ini',
            '.conf': 'conf',
            '.md': 'markdown',
            '.markdown': 'markdown',
            '.txt': 'text',
            '.yml': 'yaml',
        }
        return language_map.get(extension)

    def get_files_by_language(self, language: str) -> List[FileInfo]:
        """Get all files of a specific language."""
        return [f for f in self.files.values() if f.language == language]

    def get_files_by_extension(self, extension: str) -> List[FileInfo]:
        """Get all files with a specific extension."""
        return [f for f in self.files.values() if f.extension == extension.lower()]

    def get_directory_structure(self) -> Dict[str, List[str]]:
        """Get the directory structure as a nested dictionary."""
        structure = {}
        for file_path, file_info in self.files.items():
            parts = Path(file_path).parts
            current = structure
            for part in parts[:-1]:  # All but the filename
                if part not in current:
                    current[part] = {}
                current = current[part]
            # Add the file to the final directory
            filename = parts[-1]
            if '_files' not in current:
                current['_files'] = []
            current['_files'].append(filename)
        return structure
