"""
Repository Intelligence Engine for AgentForge.

This package provides tools for deep repository analysis including:
- Repository indexing
- Dependency analysis
- Symbol extraction
- Call graph building
- Architecture analysis
- Knowledge graph persistence
"""

from .repository_indexer import RepositoryIndexer, FileInfo
from .dependency_analyzer import DependencyAnalyzer, Dependency, DependencyAnalysis
from .symbol_extractor import SymbolExtractor, Symbol, SymbolExtractionResult
from .call_graph_builder import CallGraphBuilder, CallEdge, CallGraphNode, CallGraph
from .architecture_analyzer import ArchitectureAnalyzer, ArchitectureComponent, ArchitectureAnalysis
from .repository_knowledge_graph import RepositoryKnowledgeGraph, analyze_repository

__all__ = [
    # Indexer
    "RepositoryIndexer",
    "FileInfo",

    # Dependency Analyzer
    "DependencyAnalyzer",
    "Dependency",
    "DependencyAnalysis",

    # Symbol Extractor
    "SymbolExtractor",
    "Symbol",
    "SymbolExtractionResult",

    # Call Graph Builder
    "CallGraphBuilder",
    "CallEdge",
    "CallGraphNode",
    "CallGraph",

    # Architecture Analyzer
    "ArchitectureAnalyzer",
    "ArchitectureComponent",
    "ArchitectureAnalysis",

    # Knowledge Graph
    "RepositoryKnowledgeGraph",
    "analyze_repository"
]