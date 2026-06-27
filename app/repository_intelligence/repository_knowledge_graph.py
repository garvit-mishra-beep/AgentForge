"""
Repository Knowledge Graph for AgentForge.
Maintains a comprehensive knowledge graph of the repository structure,
integrating dependency, symbol, call, and architecture analyses.
"""
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from datetime import datetime
from dataclasses import asdict
import logging

logger = logging.getLogger(__name__)


def analyze_repository(repo_path: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to analyze a repository and return results.

    Args:
        repo_path: Path to the repository to analyze
        db_path: Optional path to the database file

    Returns:
        Dictionary containing all analysis results
    """
    kg = RepositoryKnowledgeGraph(repo_path, db_path)
    return kg.analyze_repository()


class RepositoryKnowledgeGraph:
    """
    Maintains a knowledge graph of the repository that combines
    dependency analysis, symbol extraction, call graphs, and architectural analysis.
    """

    def __init__(self, repo_path: str, db_path: Optional[str] = None):
        self.repo_path = Path(repo_path).resolve()
        self.db_path = db_path or (self.repo_path / ".agentforge" / "knowledge_graph.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize analyzers
        from .repository_indexer import RepositoryIndexer
        from .dependency_analyzer import DependencyAnalyzer
        from .symbol_extractor import SymbolExtractor
        from .call_graph_builder import CallGraphBuilder
        from .architecture_analyzer import ArchitectureAnalyzer

        self.indexer = RepositoryIndexer(str(self.repo_path))
        self.dependency_analyzer = DependencyAnalyzer(str(self.repo_path))
        self.symbol_extractor = SymbolExtractor(str(self.repo_path))
        self.call_graph_builder = CallGraphBuilder(str(self.repo_path))
        self.architecture_analyzer = ArchitectureAnalyzer(str(self.repo_path))

        # Analysis results cache
        self._index_result = None
        self._dependency_result = None
        self._symbol_result = None
        self._call_graph_result = None
        self._architecture_result = None

        # Initialize database
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the SQLite database for storing the knowledge graph."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    absolute_path TEXT NOT NULL,
                    size INTEGER,
                    modified_time REAL,
                    is_file BOOLEAN,
                    is_directory BOOLEAN,
                    extension TEXT,
                    language TEXT,
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Dependencies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    version TEXT,
                    dependency_type TEXT,
                    source_file TEXT,
                    is_resolved BOOLEAN DEFAULT FALSE,
                    resolved_version TEXT,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Symbols table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS symbols (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    symbol_type TEXT,
                    file_path TEXT,
                    line_number INTEGER,
                    column_number INTEGER,
                    end_line_number INTEGER,
                    end_column_number INTEGER,
                    signature TEXT,
                    docstring TEXT,
                    modifiers TEXT,  -- JSON array
                    parent TEXT,
                    is_async BOOLEAN DEFAULT FALSE,
                    is_static BOOLEAN DEFAULT FALSE,
                    is_abstract BOOLEAN DEFAULT FALSE,
                    return_type TEXT,
                    parameters TEXT,  -- JSON array
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Call edges table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS call_edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caller TEXT NOT NULL,
                    callee TEXT NOT NULL,
                    caller_file TEXT,
                    callee_file TEXT,
                    caller_line INTEGER,
                    callee_line INTEGER,
                    call_type TEXT DEFAULT 'direct',
                    context TEXT,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Architecture components table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS architecture_components (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    component_type TEXT,
                    description TEXT,
                    file_path TEXT,
                    dependencies TEXT,  -- JSON array
                    dependents TEXT,    -- JSON array
                    is_core BOOLEAN DEFAULT FALSE,
                    volatility TEXT DEFAULT 'medium',
                    lines_of_code INTEGER DEFAULT 0,
                    complexity REAL DEFAULT 0.0,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Analysis snapshots table (for tracking changes over time)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_files INTEGER,
                    total_dependencies INTEGER,
                    total_symbols INTEGER,
                    total_calls INTEGER,
                    total_components INTEGER,
                    analysis_data TEXT  -- JSON blob of full analysis
                )
            """)

            # Create indices for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_path ON files(path)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_path)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_calls_caller ON call_edges(caller)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_calls_callee ON call_edges(callee)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_components_name ON architecture_components(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_components_type ON architecture_components(component_type)")

            conn.commit()

    def analyze_repository(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Perform a complete analysis of the repository and store results in the knowledge graph.

        Args:
            force_refresh: If True, re-run all analyses even if cached results exist

        Returns:
            Dictionary containing all analysis results
        """
        start_time = datetime.now()

        # Check if we have recent cached results (unless forcing refresh)
        if not force_refresh and self._has_recent_analysis():
            # Return cached results
            return self._get_cached_analysis()

        # Run all analyses
        self._index_result = self.indexer.index_repository()
        self._dependency_result = self.dependency_analyzer.analyze_dependencies()
        self._symbol_result = self.symbol_extractor.extract_symbols()
        self._call_graph_result = self.call_graph_builder.build_call_graph(self._symbol_result)
        self._architecture_result = self.architecture_analyzer.analyze_architecture(self._call_graph_result)

        # Store results in database
        self._store_analysis_results()

        # Create a snapshot
        self._create_analysis_snapshot()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Return combined results
        return {
            "analysis_timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "repository_path": str(self.repo_path),
            "indexing": {
                "total_files": len(self._index_result),
                "files_by_language": self._get_files_by_language_summary()
            },
            "dependencies": asdict(self._dependency_result),
            "symbols": asdict(self._symbol_result),
            "call_graph": {
                "total_nodes": self._call_graph_result.total_nodes,
                "total_edges": self._call_graph_result.total_edges,
                "entry_points": self._call_graph_result.entry_points,
                "cycles_detected": len(self._call_graph_result.cycles)
            },
            "architecture": self._architecture_result.__dict__,
            "knowledge_graph_stats": self.get_knowledge_graph_stats()
        }

    def _has_recent_analysis(self, max_age_hours: int = 24) -> bool:
        """Check if we have a recent analysis snapshot."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT MAX(timestamp) FROM analysis_snapshots
                """)
                result = cursor.fetchone()
                if not result or not result[0]:
                    return False

                last_analysis = datetime.fromisoformat(result[0])
                age_hours = (datetime.now() - last_analysis).total_seconds() / 3600
                return age_hours < max_age_hours
        except Exception:
            return False

    def _get_cached_analysis(self) -> Dict[str, Any]:
        """Retrieve the most recent analysis from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT analysis_data FROM analysis_snapshots
                    ORDER BY timestamp DESC LIMIT 1
                """)
                result = cursor.fetchone()
                if result and result[0]:
                    return json.loads(result[0])
        except Exception as e:
            logger.warning(f"Could not load cached analysis: {e}")

        # Fall back to fresh analysis
        return self.analyze_repository(force_refresh=True)

    def _store_analysis_results(self) -> None:
        """Store all analysis results in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Clear existing data (we're doing a full refresh)
                cursor.execute("DELETE FROM files")
                cursor.execute("DELETE FROM dependencies")
                cursor.execute("DELETE FROM symbols")
                cursor.execute("DELETE FROM call_edges")
                cursor.execute("DELETE FROM architecture_components")

                # Store file index
                for file_info in self._index_result.values():
                    cursor.execute("""
                        INSERT INTO files
                        (path, absolute_path, size, modified_time, is_file, is_directory, extension, language)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        file_info.path,
                        file_info.absolute_path,
                        file_info.size,
                        file_info.modified_time,
                        file_info.is_file,
                        file_info.is_directory,
                        file_info.extension,
                        file_info.language
                    ))

                # Store dependencies
                for dep in self._dependency_result.dependencies:
                    cursor.execute("""
                        INSERT INTO dependencies
                        (name, version, dependency_type, source_file, is_resolved, resolved_version)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        dep.name,
                        dep.version,
                        dep.dependency_type,
                        dep.source_file,
                        dep.is_resolved,
                        dep.resolved_version
                    ))

                # Store symbols
                for symbol in self._symbol_result.symbols:
                    cursor.execute("""
                        INSERT INTO symbols
                        (name, symbol_type, file_path, line_number, column_number,
                         end_line_number, end_column_number, signature, docstring,
                         modifiers, parent, is_async, is_static, is_abstract,
                         return_type, parameters)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        symbol.name,
                        symbol.symbol_type,
                        symbol.file_path,
                        symbol.line_number,
                        symbol.column_number,
                        getattr(symbol, 'end_line_number', None),
                        getattr(symbol, 'end_column_number', None),
                        getattr(symbol, 'signature', None),
                        getattr(symbol, 'docstring', None),
                        json.dumps(getattr(symbol, 'modifiers', [])),
                        getattr(symbol, 'parent', None),
                        getattr(symbol, 'is_async', False),
                        getattr(symbol, 'is_static', False),
                        getattr(symbol, 'is_abstract', False),
                        getattr(symbol, 'return_type', None),
                        json.dumps(getattr(symbol, 'parameters', []))
                    ))

                # Store call edges
                for edge in self._call_graph_result.edges:
                    cursor.execute("""
                        INSERT INTO call_edges
                        (caller, callee, caller_file, callee_file, caller_line, callee_line, call_type, context)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        edge.caller,
                        edge.callee,
                        edge.caller_file,
                        edge.callee_file,
                        edge.caller_line,
                        edge.callee_line,
                        edge.call_type,
                        edge.context
                    ))

                # Store architecture components
                for component in self._architecture_result.components:
                    cursor.execute("""
                        INSERT INTO architecture_components
                        (name, component_type, description, file_path, dependencies, dependents,
                         is_core, volatility, lines_of_code, complexity)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        component.name,
                        component.component_type,
                        component.description,
                        component.file_path,
                        json.dumps(component.dependencies),
                        json.dumps(component.dependents),
                        component.is_core,
                        component.volatility,
                        component.lines_of_code,
                        component.complexity
                    ))

                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store analysis results: {e}")
            raise

    def _create_analysis_snapshot(self) -> None:
        """Create a snapshot of the current analysis for historical tracking."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Prepare summary data
                summary = {
                    "timestamp": datetime.now().isoformat(),
                    "repository_path": str(self.repo_path),
                    "counts": {
                        "files": len(self._index_result) if self._index_result else 0,
                        "dependencies": len(self._dependency_result.dependencies) if self._dependency_result else 0,
                        "symbols": len(self._symbol_result.symbols) if self._symbol_result else 0,
                        "calls": len(self._call_graph_result.edges) if self._call_graph_result else 0,
                        "components": len(self._architecture_result.components) if self._architecture_result else 0
                    }
                }

                cursor.execute("""
                    INSERT INTO analysis_snapshots
                    (total_files, total_dependencies, total_symbols, total_calls, total_components, analysis_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    summary["counts"]["files"],
                    summary["counts"]["dependencies"],
                    summary["counts"]["symbols"],
                    summary["counts"]["calls"],
                    summary["counts"]["components"],
                    json.dumps(summary)
                ))

                conn.commit()
        except Exception as e:
            logger.warning(f"Could not create analysis snapshot: {e}")

    def get_knowledge_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph stored in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                stats = {}

                # Count records in each table
                tables = ['files', 'dependencies', 'symbols', 'call_edges', 'architecture_components', 'analysis_snapshots']
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats[f"{table}_count"] = count

                # Get latest snapshot info
                cursor.execute("""
                    SELECT timestamp, total_files, total_dependencies, total_symbols, total_calls, total_components
                    FROM analysis_snapshots
                    ORDER BY timestamp DESC LIMIT 1
                """)
                snapshot = cursor.fetchone()
                if snapshot:
                    stats["last_analysis"] = {
                        "timestamp": snapshot[0],
                        "files": snapshot[1],
                        "dependencies": snapshot[2],
                        "symbols": snapshot[3],
                        "calls": snapshot[4],
                        "components": snapshot[5]
                    }

                return stats
        except Exception as e:
            logger.error(f"Could not get knowledge graph stats: {e}")
            return {}

    def query_symbols(self, name_pattern: Optional[str] = None,
                     file_path: Optional[str] = None,
                     symbol_type: Optional[str] = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query symbols from the knowledge graph.

        Args:
            name_pattern: Optional pattern to match symbol names (SQL LIKE)
            file_path: Optional file path to filter by
            symbol_type: Optional symbol type to filter by
            limit: Maximum number of results to return

        Returns:
            List of matching symbols as dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM symbols WHERE 1=1"
                params = []

                if name_pattern:
                    query += " AND name LIKE ?"
                    params.append(f"%{name_pattern}%")

                if file_path:
                    query += " AND file_path = ?"
                    params.append(file_path)

                if symbol_type:
                    query += " AND symbol_type = ?"
                    params.append(symbol_type)

                query += " ORDER BY name LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()

                results = []
                for row in rows:
                    record = dict(zip(columns, row))
                    # Parse JSON fields
                    if record['modifiers']:
                        try:
                            record['modifiers'] = json.loads(record['modifiers'])
                        except Exception:
                            pass
                    if record['parameters']:
                        try:
                            record['parameters'] = json.loads(record['parameters'])
                        except Exception:
                            pass
                    results.append(record)

                return results
        except Exception as e:
            logger.error(f"Error querying symbols: {e}")
            return []

    def query_dependencies(self, name_pattern: Optional[str] = None,
                          dependency_type: Optional[str] = None,
                          source_file: Optional[str] = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query dependencies from the knowledge graph.

        Args:
            name_pattern: Optional pattern to match dependency names
            dependency_type: Optional dependency type to filter by
            source_file: Optional source file to filter by
            limit: Maximum number of results to return

        Returns:
            List of matching dependencies as dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM dependencies WHERE 1=1"
                params = []

                if name_pattern:
                    query += " AND name LIKE ?"
                    params.append(f"%{name_pattern}%")

                if dependency_type:
                    query += " AND dependency_type = ?"
                    params.append(dependency_type)

                if source_file:
                    query += " AND source_file = ?"
                    params.append(source_file)

                query += " ORDER BY name LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()

                results = []
                for row in rows:
                    record = dict(zip(columns, row))
                    results.append(record)

                return results
        except Exception as e:
            logger.error(f"Error querying dependencies: {e}")
            return []