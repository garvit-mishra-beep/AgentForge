"""
Basic test for the Repository Intelligence Engine.
"""
import tempfile
import os
from pathlib import Path

def test_repository_intelligence_basic():
    """Test that the repository intelligence engine can be imported and instantiated."""
    # Try to import the modules
    try:
        from app.repository_intelligence import (
            RepositoryIndexer,
            DependencyAnalyzer,
            SymbolExtractor,
            CallGraphBuilder,
            ArchitectureAnalyzer,
            RepositoryKnowledgeGraph,
            analyze_repository
        )
        print("✓ All modules imported successfully")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

    # Create a temporary directory with some test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a simple Python file
        test_file = temp_path / "test_module.py"
        test_file.write_text("""
def hello_world():
    """Say hello to the world."""
    print("Hello, World!")
    return "Hello"

class Calculator:
    """A simple calculator class."""

    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b

def main():
    calc = Calculator()
    result = calc.add(2, 3)
    print(f"2 + 3 = {result}")

if __name__ == "__main__":
    main()
""")

        # Create a requirements.txt file
        req_file = temp_path / "requirements.txt"
        req_file.write_text("""
requests==2.28.1
numpy>=1.21.0
""")

        # Create a simple JSON config
        config_file = temp_path / "config.json"
        config_file.write_text('{"debug": true, "version": "1.0"}')

        try:
            # Test the indexer
            indexer = RepositoryIndexer(str(temp_path))
            files = indexer.index_repository()
            print(f"✓ Indexer found {len(files)} files")

            # Test the dependency analyzer
            dep_analyzer = DependencyAnalyzer(str(temp_path))
            deps = dep_analyzer.analyze_dependencies()
            print(f"✓ Dependency analyzer found {len(deps.dependencies)} dependencies")

            # Test the symbol extractor
            symbol_extractor = SymbolExtractor(str(temp_path))
            symbols = symbol_extractor.extract_symbols()
            print(f"✓ Symbol extractor found {len(symbols.symbols)} symbols")

            # Test the call graph builder
            call_builder = CallGraphBuilder(str(temp_path))
            call_graph = call_builder.build_call_graph(symbols)
            print(f"✓ Call graph builder found {call_graph.total_nodes} nodes and {call_graph.total_edges} edges")

            # Test the architecture analyzer
            arch_analyzer = ArchitectureAnalyzer(str(temp_path))
            arch_result = arch_analyzer.analyze_architecture(call_graph)
            print(f"✓ Architecture analyzer found {len(arch_result.components)} components")

            # Test the knowledge graph
            kg = RepositoryKnowledgeGraph(str(temp_path))
            result = kg.analyze_repository()
            print(f"✓ Knowledge graph analysis completed in {result['duration_seconds']:.2f} seconds")
            print(f"  - Files: {result['indexing']['total_files']}")
            print(f"  - Dependencies: {result['dependencies']['total_dependencies']}")
            print(f"  - Symbols: {result['symbols']['total_symbols']}")
            print(f"  - Calls: {result['call_graph']['total_edges']}")
            print(f"  - Components: {result['architecture']['total_components']}")

            return True

        except Exception as e:
            print(f"✗ Error during testing: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("Testing Repository Intelligence Engine...")
    success = test_repository_intelligence_basic()
    if success:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed!")
        exit(1)