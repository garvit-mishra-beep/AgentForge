"""
Architecture Analyzer for AgentForge.
Analyzes architectural patterns, layers, domains, services, and structural relationships.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ArchitectureComponent:
    """Represents an architectural component (layer, service, module, etc.)."""
    name: str
    component_type: str  # layer, domain, service, repository, controller, etc.
    file_path: str
    description: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)  # Other components this depends on
    dependents: List[str] = field(default_factory=list)  # Components that depend on this
    is_core: bool = False
    volatility: str = "medium"  # low, medium, high
    lines_of_code: int = 0
    complexity: float = 0.0


@dataclass
class ArchitectureAnalysis:
    """Results of architectural analysis."""
    components: List[ArchitectureComponent] = field(default_factory=list)
    layers: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    repositories: List[str] = field(default_factory=list)
    controllers: List[str] = field(default_factory=list)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    architectural_patterns: List[str] = field(default_factory=list)
    total_components: int = 0
    total_dependencies: int = 0


class ArchitectureAnalyzer:
    """
    Analyzes software architecture by identifying layers, domains, services,
    and other structural elements.
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.components: List[ArchitectureComponent] = []
        self.dependency_map: Dict[str, Set[str]] = defaultdict(set)

    def analyze_architecture(self, call_graph_result=None) -> ArchitectureAnalysis:
        """
        Analyze the repository's architecture.

        Args:
            call_graph_result: Optional result from CallGraphBuilder to reuse data

        Returns:
            ArchitectureAnalysis object containing architectural insights
        """
        self.components.clear()
        self.dependency_map.clear()

        # Identify architectural components
        self._identify_components()

        # Analyze dependencies between components
        self._analyze_component_dependencies(call_graph_result)

        # Identify architectural layers
        self._identify_layers()

        # Identify business domains
        self._identify_domains()

        # Identify services
        self._identify_services()

        # Identify repositories and data access patterns
        self._identify_repositories()

        # Identify controllers and presentation layer
        self._identify_controllers()

        # Detect architectural patterns
        self._detect_architectural_patterns()

        # Calculate metrics
        self._calculate_metrics()

        return ArchitectureAnalysis(
            components=self.components.copy(),
            layers=self._get_layer_names(),
            domains=self._get_domain_names(),
            services=self._get_service_names(),
            repositories=self._get_repository_names(),
            controllers=self._get_controller_names(),
            dependency_graph=dict(self.dependency_map),
            architectural_patterns=self.architectural_patterns,
            total_components=len(self.components),
            total_dependencies=sum(len(deps) for deps in self.dependency_map.values())
        )

    def _identify_components(self) -> None:
        """Identify potential architectural components based on file structure and naming."""
        # Walk the repository to find structural patterns
        for root, dirs, files in os.walk(self.repo_path):
            # Skip ignored directories
            rel_root = Path(root).relative_to(self.repo_path)
            if self._should_ignore_path(Path(root)):
                continue

            # Analyze directory structure for architectural hints
            self._analyze_directory_structure(rel_root, dirs, files)

            # Analyze files for component indicators
            for file in files:
                file_path = Path(root) / file
                if self._should_ignore_path(file_path):
                    continue

                rel_file_path = file_path.relative_to(self.repo_path)
                self._analyze_file_for_components(rel_file_path, file_path)

    def _should_ignore_path(self, path: Path) -> bool:
        """Check if a path should be ignored during analysis."""
        ignore_patterns = [
            'node_modules', '.git', '__pycache__', '.pytest_cache',
            'dist', 'build', '.venv', 'venv', 'env', '.env',
            'vendor', 'bower_components', 'target', 'out',
            'bin', 'obj', '.idea', '.vs', '.vscode',
            'coverage', '.nyc_output', '.cache', '.temp', 'temp'
        ]

        path_str = str(path)
        for pattern in ignore_patterns:
            if pattern in path_str:
                return True

        # Skip certain file types
        skip_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.ico',  # Images
            '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',  # Media
            '.zip', '.tar', '.gz', '.rar', '.7z', '.pkg', '.msi',   # Archives
            '.exe', '.dll', '.so', '.bin', '.out', '.o', '.obj',    # Binaries
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',  # Docs
            '.ttf', '.otf', '.woff', '.woff2', '.eot',              # Fonts
            '.map', '.lock'                                         # Build artifacts
        }

        if path.suffix.lower() in skip_extensions:
            return True

        return False

    def _analyze_directory_structure(self, rel_path: Path, dirs: List[str], files: List[str]) -> None:
        """Analyze directory structure to identify architectural components."""
        path_str = str(rel_path)

        # Common architectural directory patterns
        layer_indicators = {
            'presentation': ['views', 'controllers', 'pages', 'components', 'templates'],
            'application': ['services', 'use_cases', 'interactors', 'app'],
            'domain': ['models', 'entities', 'aggregates', 'domain'],
            'infrastructure': ['repositories', 'dao', 'gateways', 'external', 'persistence'],
            'interface': ['api', 'web', 'http', 'rest', 'graphql', 'grpc']
        }

        for layer, indicators in layer_indicators.items():
            if any(indicator in path_str.lower() for indicator in indicators):
                self._add_component(
                    name=path_str,
                    component_type="layer",
                    description=f"{layer.title()} layer",
                    file_path=str(rel_path),
                    is_core=(layer in ['domain', 'application'])
                )

        # Domain-driven design patterns
        domain_indicators = ['domain', 'bounded-context', 'bc', 'subdomain']
        if any(indicator in path_str.lower() for indicator in domain_indicators):
            self._add_component(
                name=path_str,
                component_type="domain",
                description=f"Business domain: {path_str.name}",
                file_path=str(rel_path)
            )

        # Service patterns
        service_indicators = ['service', 'services', 'micro-service', 'microservice']
        if any(indicator in path_str.lower() for indicator in service_indicators):
            self._add_component(
                name=path_str,
                component_type="service",
                description=f"Service: {path_str.name}",
                file_path=str(rel_path)
            )

        # Repository patterns
        repo_indicators = ['repository', 'repo', 'dao', 'data']
        if any(indicator in path_str.lower() for indicator in repo_indicators):
            self._add_component(
                name=path_str,
                component_type="repository",
                description=f"Data access component: {path_str.name}",
                file_path=str(rel_path)
            )

        # Controller patterns
        controller_indicators = ['controller', 'handler', 'endpoint', 'route']
        if any(indicator in path_str.lower() for indicator in controller_indicators):
            self._add_component(
                name=path_str,
                component_type="controller",
                description=f"Controller/Handler: {path_str.name}",
                file_path=str(rel_path)
            )

    def _analyze_file_for_components(self, rel_file_path: Path, full_path: Path) -> None:
        """Analyze individual files for architectural significance."""
        file_str = str(rel_file_path)
        name = full_path.stem  # filename without extension

        # Skip if already processed as directory component
        # Check if this file represents a significant component

        # Controller/Web layer files
        controller_patterns = [
            r'.*[Cc]ontroller\.[tj]sx?$',
            r'.*[Hh]andler\.[tj]sx?$',
            r'.*[Rr]oute\.[tj]sx?$',
            r'.*[Aa]pi\.[tj]sx?$',
            r'.*[Vv]iew[^a-zA-Z]*\.[tj]sx?$',
            r'.*[Pp]age\.[tj]sx?$'
        ]

        service_patterns = [
            r'.*[Ss]ervice\.[tj]sx?$',
            r'.*[Mm]anager\.[tj]sx?$',
            r'.*[Pp]rovider\.[tj]sx?$'
        ]

        repository_patterns = [
            r'.*[Rr]epository\.[tj]sx?$',
            r'.*[Dd][Aa]o\.[tj]sx?$',
            r'.*[Gg]ateway\.[tj]sx?$'
        ]

        model_patterns = [
            r'.*[Mm]odel\.[tj]sx?$',
            r'.*[Ee]ntity\.[tj]sx?$',
            r'.*[Vv]iew[Mm]odel\.[tj]sx?$',
            r'.*[Dd]to\.[tj]sx?$'
        ]

        # Check patterns
        for pattern in controller_patterns:
            if re.match(pattern, file_str, re.IGNORECASE):
                self._add_component(
                    name=name,
                    component_type="controller",
                    description=f"Controller: {name}",
                    file_path=file_str
                )
                break

        for pattern in service_patterns:
            if re.match(pattern, file_str, re.IGNORECASE):
                self._add_component(
                    name=name,
                    component_type="service",
                    description=f"Service: {name}",
                    file_path=file_str
                )
                break

        for pattern in repository_patterns:
            if re.match(pattern, file_str, re.IGNORECASE):
                self._add_component(
                    name=name,
                    component_type="repository",
                    description=f"Repository: {name}",
                    file_path=file_str
                )
                break

        for pattern in model_patterns:
            if re.match(pattern, file_str, re.IGNORECASE):
                self._add_component(
                    name=name,
                    component_type="domain_model",
                    description=f"Domain model: {name}",
                    file_path=file_str
                )
                break

        # Configuration files that might indicate architectural boundaries
        config_indicators = [
            'application.properties', 'application.yml', 'application.yaml',
            'config.js', 'config.ts', 'config.json', 'settings.xml',
            'web.config', 'app.config', '.env', 'docker-compose.yml'
        ]

        if file_str in config_indicators or any(file_str.endswith(ind) for ind in config_indicators):
            self._add_component(
                name=name,
                component_type="configuration",
                description=f"Configuration: {name}",
                file_path=file_str,
                is_core=True
            )

    def _add_component(self, name: str, component_type: str, description: Optional[str] = None,
                      file_path: str = "", dependencies: List[str] = None,
                      is_core: bool = False, volatility: str = "medium") -> None:
        """Add an architectural component."""
        # Avoid duplicates
        for comp in self.components:
            if comp.name == name and comp.file_path == file_path:
                return  # Already exists

        component = ArchitectureComponent(
            name=name,
            component_type=component_type,
            description=description or f"{component_type.title()}: {name}",
            file_path=file_path,
            dependencies=dependencies or [],
            is_core=is_core,
            volatility=volatility
        )

        # Try to estimate lines of code
        if file_path and not file_path.endswith(('.json', '.yml', '.yaml', '.xml', '.txt', '.md')):
            full_path = self.repo_path / file_path
            if full_path.exists() and full_path.is_file():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        component.lines_of_code = len([line for line in lines if line.strip()])
                except:
                    component.lines_of_code = 0

        self.components.append(component)

    def _analyze_component_dependencies(self, call_graph_result=None) -> None:
        """Analyze dependencies between architectural components."""
        # Use call graph if available for more accurate dependencies
        if call_graph_result and hasattr(call_graph_result, 'edges'):
            # Build dependency map from call graph
            for edge in call_graph_result.edges:
                caller_comp = self._find_component_by_file(edge.caller_file)
                callee_comp = self._find_component_by_file(edge.callee_file)
                if caller_comp and callee_comp and caller_comp.name != callee_comp.name:
                    self.dependency_map[caller_comp.name].add(callee_comp.name)
        else:
            # Fallback: analyze import/include statements
            self._analyze_import_dependencies()

    def _analyze_import_dependencies(self) -> None:
        """Analyze import statements to determine dependencies."""
        for component in self.components:
            if not component.file_path:
                continue

            full_path = self.repo_path / component.file_path
            if not full_path.exists() or not full_path.is_file():
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                imports = self._extract_imports(content, full_path.suffix)

                # For each import, try to find a corresponding component
                for imp in imports:
                    imported_component = self._find_component_by_import(imp, component.file_path)
                    if imported_component and imported_component.name != component.name:
                        self.dependency_map[component.name].add(imported_component.name)
            except Exception as e:
                logger.warning(f"Could not analyze imports in {component.file_path}: {e}")

    def _extract_imports(self, content: str, file_extension: str) -> List[str]:
        """Extract import statements from file content."""
        imports = []

        if file_extension == '.py':
            # Python imports
            import_patterns = [
                r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_\.]*)',
                r'^\s*from\s+([a-zA-Z_][a-zA-Z0-9_\.]*)\s+import'
            ]
            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                imports.extend(matches)

        elif file_extension in ['.js', '.ts', '.jsx', '.tsx']:
            # JavaScript/TypeScript imports
            import_patterns = [
                r'^\s*import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'^\s*import\s+[\'"]([^\'"]+)[\'"]',
                r'^\s*const\s+.*?\s*=\s*require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'^\s*require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
            ]
            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                imports.extend(matches)

        elif file_extension == '.java':
            # Java imports
            import_pattern = r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_\.]*);'
            matches = re.findall(import_pattern, content, re.MULTILINE)
            imports.extend(matches)

        elif file_extension in ['.cpp', '.c', '.h', '.hpp']:
            # C/C++ includes
            include_pattern = r'^\s*#\s*include\s*[<"]([^">]+)[>"]'
            matches = re.findall(include_pattern, content, re.MULTILINE)
            imports.extend(matches)

        elif file_extension == '.cs':
            # C# using statements
            using_pattern = r'^\s*using\s+([a-zA-Z_][a-zA-Z0-9_\.]*);'
            matches = re.findall(using_pattern, content, re.MULTILINE)
            imports.extend(matches)

        elif file_extension == '.go':
            # Go imports
            import_pattern = r'^\s*import\s+[\'"]([^\'"]+)[\'"]'
            matches = re.findall(import_pattern, content, re.MULTILINE)
            imports.extend(matches)

            # Go parenthesized imports
            import_block_pattern = r'import\s*\(([^)]+)\)'
            blocks = re.findall(import_block_pattern, content, re.MULTILINE | re.DOTALL)
            for block in blocks:
                block_imports = re.findall(r'[\'"]([^\'"]+)[\'"]', block)
                imports.extend(block_imports)

        return imports

    def _find_component_by_file(self, file_path: str) -> Optional[ArchitectureComponent]:
        """Find a component by its file path."""
        for component in self.components:
            if component.file_path == file_path:
                return component
        return None

    def _find_component_by_import(self, import_str: str, current_file: str) -> Optional[ArchitectureComponent]:
        """Find a component that corresponds to an import statement."""
        # This is simplified - real implementation would need to map imports to actual files
        # For now, we'll do basic string matching
        import_clean = import_str.strip().strip('./')

        for component in self.components:
            if not component.file_path:
                continue

            # Check if the import matches the component's file path or name
            comp_path = Path(component.file_path)
            comp_name = comp_path.stem

            # Various matching strategies
            if (import_clean == comp_name or
                import_clean == str(comp_path) or
                import_clean == str(comp_path.with_suffix('')) or
                any(import_clean in part for part in comp_path.parts)):
                return component

        return None

    def _identify_layers(self) -> None:
        """Identify architectural layers."""
        # This would analyze the dependency graph to identify layering violations
        # For now, we'll identify components labeled as layers
        pass

    def _identify_domains(self) -> None:
        """Identify business domains."""
        # Components marked as domain type
        pass

    def _identify_services(self) -> None:
        """Identify services."""
        # Components marked as service type
        pass

    def _identify_repositories(self) -> None:
        """Identify repositories."""
        # Components marked as repository type
        pass

    def _identify_controllers(self) -> None:
        """Identify controllers."""
        # Components marked as controller type
        pass

    def _detect_architectural_patterns(self) -> None:
        """Detect common architectural patterns."""
        self.architectural_patterns = []

        # Check for layered architecture
        if self._has_layered_architecture():
            self.architectural_patterns.append("Layered Architecture")

        # Check for MVC
        if self._has_mvc_pattern():
            self.architectural_patterns.append("MVC (Model-View-Controller)")

        # Check for Microservices
        if self._has_microservices_pattern():
            self.architectural_patterns.append("Microservices")

        # Check for Hexagonal/Ports and Adapters
        if self._has_hexagonal_pattern():
            self.architectural_patterns.append("Hexagonal Architecture")

        # Check for Event-Driven
        if self._has_event_driven_pattern():
            self.architectural_patterns.append("Event-Driven Architecture")

        # Check for Pipe-and-Filter
        if self._has_pipe_filter_pattern():
            self.architectural_patterns.append("Pipe-and-Filter Architecture")

    def _has_layered_architecture(self) -> bool:
        """Check if the architecture follows a layered pattern."""
        # Simplified check: look for distinct layer components
        layer_types = {'presentation', 'application', 'domain', 'infrastructure'}
        found_layers = set()
        for comp in self.components:
            if comp.component_type in layer_types:
                found_layers.add(comp.component_type)
        return len(found_layers) >= 3  # At least presentation, domain, infrastructure

    def _has_mvc_pattern(self) -> bool:
        """Check for MVC pattern."""
        has_model = any(comp.component_type in ['domain_model', 'model', 'entity'] for comp in self.components)
        has_view = any(comp.component_type in ['view', 'page', 'template'] for comp in self.components)
        has_controller = any(comp.component_type == 'controller' for comp in self.components)
        return has_model and has_view and has_controller

    def _has_microservices_pattern(self) -> bool:
        """Check for microservices pattern."""
        service_comps = [comp for comp in self.components if comp.component_type == 'service']
        # Look for multiple services with limited inter-dependencies
        return len(service_comps) >= 3

    def _has_hexagonal_pattern(self) -> bool:
        """Check for hexagonal (ports and adapters) pattern."""
        # Look for clear separation between core and adapters
        has_core = any(comp.is_core for comp in self.components)
        has_adapters = any('adapter' in comp.name.lower() or 'gateway' in comp.name.lower()
                          for comp in self.components)
        return has_core and has_adapters

    def _has_event_driven_pattern(self) -> bool:
        """Check for event-driven architecture."""
        # Look for event-related naming
        event_indicators = ['event', 'listener', 'handler', 'publisher', 'subscriber', 'queue', 'topic']
        has_event_elements = any(
            any(indicator in comp.name.lower() for indicator in event_indicators)
            for comp in self.components
        )
        return has_event_elements

    def _has_pipe_filter_pattern(self) -> bool:
        """Check for pipe-and-filter architecture."""
        # Look for filter/processor naming
        filter_indicators = ['filter', 'processor', 'transformer', 'pipe', 'pipeline']
        has_filter_elements = any(
            any(indicator in comp.name.lower() for indicator in filter_indicators)
            for comp in self.components
        )
        return has_filter_elements

    def _calculate_metrics(self) -> None:
        """Calculate architectural metrics."""
        for component in self.components:
            # Volatility based on dependencies and dependents
            dep_count = len(self.dependency_map.get(component.name, set()))
            dep_count_reverse = sum(1 for deps in self.dependency_map.values()
                                  if component.name in deps)

            # High volatility = many dependents (many things depend on it, so changing it affects many)
            # Low volatility = few dependents (safe to change)
            if dep_count_reverse > 5:
                component.volatility = "high"
            elif dep_count_reverse > 2:
                component.volatility = "medium"
            else:
                component.volatility = "low"

            # Complexity based on lines of code and dependencies
            if component.lines_of_code > 0:
                # Simple complexity formula
                component.complexity = min(100, (component.lines_of_code / 100) * 10 + dep_count * 5)

    def _get_layer_names(self) -> List[str]:
        """Get names of identified layers."""
        return [comp.name for comp in self.components if comp.component_type == 'layer']

    def _get_domain_names(self) -> List[str]:
        """Get names of identified domains."""
        return [comp.name for comp in self.components if comp.component_type == 'domain']

    def _get_service_names(self) -> List[str]:
        """Get names of identified services."""
        return [comp.name for comp in self.components if comp.component_type == 'service']

    def _get_repository_names(self) -> List[str]:
        """Get names of identified repositories."""
        return [comp.name for comp in self.components if comp.component_type == 'repository']

    def _get_controller_names(self) -> List[str]:
        """Get names of identified controllers."""
        return [comp.name for comp in self.components if comp.component_type == 'controller']

    def get_architecture_summary(self) -> Dict[str, Any]:
        """Get a summary of the architectural analysis."""
        # Group components by type
        by_type = defaultdict(list)
        for component in self.components:
            by_type[component.component_type].append(component.name)

        # Calculate stability (inverse of volatility)
        stability_counts = {'low': 0, 'medium': 0, 'high': 0}
        for component in self.components:
            stability_counts[component.volatility] += 1

        return {
            "total_components": len(self.components),
            "by_type": dict(by_type),
            "layers": self._get_layer_names(),
            "domains": self._get_domain_names(),
            "services": self._get_service_names(),
            "repositories": self._get_repository_names(),
            "controllers": self._get_controller_names(),
            "dependency_graph": dict(self.dependency_map),
            "architectural_patterns": self.architectural_patterns,
            "stability_distribution": dict(stability_counts),
            "avg_lines_per_component": sum(comp.lines_of_code for comp in self.components) / max(len(self.components), 1),
            "avg_complexity": sum(comp.complexity for comp in self.components) / max(len(self.components), 1)
        }