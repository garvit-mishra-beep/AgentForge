"""
Dependency Analyzer for AgentForge.
Analyzes dependencies in various formats (package.json, requirements.txt, pom.xml, etc.).
"""
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
import toml
import configparser


@dataclass
class Dependency:
    """Represents a software dependency."""
    name: str
    version: str
    dependency_type: str  # e.g., "runtime", "dev", "peer", "optional"
    source_file: str
    is_resolved: bool = False
    resolved_version: Optional[str] = None


@dataclass
class DependencyAnalysis:
    """Results of dependency analysis."""
    dependencies: List[Dependency] = field(default_factory=list)
    dependency_files: List[str] = field(default_factory=list)
    ecosystem: Optional[str] = None  # e.g., "npm", "pip", "maven", "gradle"
    total_dependencies: int = 0
    direct_dependencies: int = 0
    transitive_dependencies: int = 0


class DependencyAnalyzer:
    """
    Analyzes dependencies across different ecosystems and package managers.
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.dependencies: List[Dependency] = []
        self.dependency_files: List[str] = []

    def analyze_dependencies(self) -> DependencyAnalysis:
        """
        Analyze all dependencies in the repository.

        Returns:
            DependencyAnalysis object containing all found dependencies
        """
        self.dependencies.clear()
        self.dependency_files.clear()

        # Common dependency file patterns to look for
        dependency_files = [
            # Node.js / npm
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",

            # Python
            "requirements.txt",
            "requirements-dev.txt",
            "setup.py",
            "setup.cfg",
            "pyproject.toml",
            "Pipfile",
            "Pipfile.lock",
            "poetry.lock",

            # Java / JVM
            "pom.xml",  # Maven
            "build.gradle",  # Gradle
            "build.gradle.kts",  # Gradle Kotlin DSL
            "ivy.xml",  # Ivy
            "build.sbt",  # sbt

            # .NET
            "*.csproj",
            "*.fsproj",
            "packages.config",
            "project.json",
            "project.lock.json",

            # Ruby
            "Gemfile",
            "Gemfile.lock",

            # PHP
            "composer.json",
            "composer.lock",

            # Rust
            "Cargo.toml",
            "Cargo.lock",

            # Go
            "go.mod",
            "go.sum",

            # Swift
            "Package.swift",

            # Dart
            "pubspec.yaml",

            # Elixir
            "mix.exs",
            "mix.lock",
        ]

        # Find all dependency files
        for pattern in dependency_files:
            if '*' in pattern:
                # Handle glob patterns
                import glob
                matches = glob.glob(str(self.repo_path / '**' / pattern), recursive=True)
                for match in matches:
                    rel_path = os.path.relpath(match, self.repo_path)
                    if not self._should_ignore_path(Path(match)):
                        self.dependency_files.append(rel_path)
            else:
                # Handle exact filenames
                matches = list(self.repo_path.rglob(pattern))
                for match in matches:
                    rel_path = os.path.relpath(match, self.repo_path)
                    if not self._should_ignore_path(match):
                        self.dependency_files.append(rel_path)

        # Analyze each dependency file
        for dep_file in self.dependency_files:
            file_path = self.repo_path / dep_file
            self._analyze_dependency_file(file_path, dep_file)

        # Deduplicate dependencies (by name and source file for now)
        unique_deps = {}
        for dep in self.dependencies:
            key = (dep.name, dep.source_file)
            if key not in unique_deps:
                unique_deps[key] = dep

        self.dependencies = list(unique_deps.values())

        # Determine ecosystem
        ecosystem = self._detect_ecosystem()

        return DependencyAnalysis(
            dependencies=self.dependencies,
            dependency_files=self.dependency_files,
            ecosystem=ecosystem,
            total_dependencies=len(self.dependencies),
            direct_dependencies=len([d for d in self.dependencies if d.dependency_type in ["runtime", "direct"]]),
            transitive_dependencies=len([d for d in self.dependencies if d.dependency_type in ["transitive", "indirect"]])
        )

    def _should_ignore_path(self, path: Path) -> bool:
        """Check if a path should be ignored (e.g., in node_modules, .git, etc.)."""
        # Skip common directories that contain dependencies we don't need to analyze
        ignore_patterns = [
            'node_modules',
            '.git',
            '__pycache__',
            '.pytest_cache',
            'dist',
            'build',
            '.venv',
            'venv',
            'env',
            '.env',
            'vendor',
            'bower_components',
        ]

        path_str = str(path)
        for pattern in ignore_patterns:
            if pattern in path_str:
                return True
        return False

    def _analyze_dependency_file(self, file_path: Path, rel_path: str) -> None:
        """Analyze a specific dependency file based on its name."""
        file_name = file_path.name

        try:
            if file_name == "package.json" or file_name.endswith("-package.json"):
                self._analyze_package_json(file_path, rel_path)
            elif file_name == "requirements.txt":
                self._analyze_requirements_txt(file_path, rel_path)
            elif file_name == "setup.py":
                self._analyze_setup_py(file_path, rel_path)
            elif file_name == "pyproject.toml":
                self._analyze_pyproject_toml(file_path, rel_path)
            elif file_name == "Pipfile":
                self._analyze_pipfile(file_path, rel_path)
            elif file_name == "pom.xml":
                self._analyze_pom_xml(file_path, rel_path)
            elif file_name.endswith(".gradle") or file_name.endswith(".gradle.kts"):
                self._analyze_gradle_file(file_path, rel_path)
            elif file_name == "composer.json":
                self._analyze_composer_json(file_path, rel_path)
            elif file_name == "Cargo.toml":
                self._analyze_cargo_toml(file_path, rel_path)
            elif file_name == "go.mod":
                self._analyze_go_mod(file_path, rel_path)
            elif file_name == "Gemfile":
                self._analyze_gemfile(file_path, rel_path)
            # Add more parsers as needed
        except Exception as e:
            # Log error but continue processing other files
            print(f"Warning: Could not parse {rel_path}: {e}")

    def _analyze_package_json(self, file_path: Path, rel_path: str) -> None:
        """Analyze Node.js package.json file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Analyze dependencies
        for dep_type in ['dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies']:
            if dep_type in data:
                for name, version in data[dep_type].items():
                    # Clean version string (remove ^, ~, etc.)
                    clean_version = version.lstrip('^~><=')
                    dependency_type = "dev" if dep_type == "devDependencies" else "runtime"
                    if dep_type == "peerDependencies":
                        dependency_type = "peer"
                    elif dep_type == "optionalDependencies":
                        dependency_type = "optional"

                    self.dependencies.append(Dependency(
                        name=name,
                        version=clean_version,
                        dependency_type=dependency_type,
                        source_file=rel_path
                    ))

    def _analyze_requirements_txt(self, file_path: Path, rel_path: str) -> None:
        """Analyze Python requirements.txt file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Handle -r (requirements), -c (constraints), etc.
                if line.startswith('-r ') or line.startswith('-c '):
                    continue

                # Parse package==version or package>=version, etc.
                # Using regex to capture package name and version specifier
                match = re.match(r'^([a-zA-Z0-9][a-zA-Z0-9._-]*)([\s]*[=<>!~].*)?$', line)
                if match:
                    package_name = match.group(1)
                    version_spec = match.group(2) or ""
                    # Extract version number from spec (simplified)
                    version_match = re.search(r'[=<>!~]+([0-9][a-zA-Z0-9._-]*)', version_spec)
                    version = version_match.group(1) if version_match else "unknown"

                    self.dependencies.append(Dependency(
                        name=package_name,
                        version=version,
                        dependency_type="runtime",
                        source_file=rel_path
                    ))

    def _analyze_setup_py(self, file_path: Path, rel_path: str) -> None:
        """Analyze Python setup.py file (basic implementation)."""
        # This is a simplified parser - a full implementation would need to
        # safely execute the setup.py or use ast to extract dependencies
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for install_requires or requires patterns
        install_requires_pattern = r'install_requires\s*=\s*\[([^\]]*)\]'
        matches = re.findall(install_requires_pattern, content, re.DOTALL | re.IGNORECASE)

        for match in matches:
            # Extract quoted strings
            packages = re.findall(r'["\']([^"\']*)["\']', match)
            for package in packages:
                # Parse package==version format
                if '==' in package:
                    name, version = package.split('==', 1)
                    self.dependencies.append(Dependency(
                        name=name.strip(),
                        version=version.strip(),
                        dependency_type="runtime",
                        source_file=rel_path
                    ))
                else:
                    # Just package name
                    self.dependencies.append(Dependency(
                        name=package.strip(),
                        version="unknown",
                        dependency_type="runtime",
                        source_file=rel_path
                    ))

    def _analyze_pyproject_toml(self, file_path: Path, rel_path: str) -> None:
        """Analyze Python pyproject.toml file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)

        # Check for poetry dependencies
        if 'tool' in data and 'poetry' in data['tool']:
            poetry = data['tool']['poetry']
            if 'dependencies' in poetry:
                for name, constraint in poetry['dependencies'].items():
                    if name.lower() != 'python':  # Skip Python version
                        version_str = str(constraint) if not isinstance(constraint, dict) else constraint.get('version', '*')
                        self.dependencies.append(Dependency(
                            name=name,
                            version=version_str,
                            dependency_type="runtime",
                            source_file=rel_path
                        ))

            if 'group' in poetry:
                for group_name, group_data in poetry['group'].items():
                    if 'dependencies' in group_data:
                        for name, constraint in group_data['dependencies'].items():
                            version_str = str(constraint) if not isinstance(constraint, dict) else constraint.get('version', '*')
                            self.dependencies.append(Dependency(
                                name=name,
                                version=version_str,
                                dependency_type=group_name,  # dev, test, etc.
                                source_file=rel_path
                            ))

        # Check for setuptools or flit configuration
        if 'project' in data:
            project = data['project']
            if 'dependencies' in project:
                for dep in project['dependencies']:
                    # Parse dependency specifier (e.g., "requests>=2.25.0")
                    if '>=' in dep or '==' in dep or '>' in dep or '<' in dep or '~=' in dep:
                        # Simple split on first occurrence of comparator
                        match = re.match(r'^([a-zA-Z0-9][a-zA-Z0-9._-]*)(.*)$', dep)
                        if match:
                            name = match.group(1)
                            version_spec = match.group(2).strip()
                            # Extract version number (simplified)
                            version_match = re.search(r'[0-9][a-zA-Z0-9._-]*', version_spec)
                            version = version_match.group(0) if version_match else "unknown"
                            self.dependencies.append(Dependency(
                                name=name,
                                version=version,
                                dependency_type="runtime",
                                source_file=rel_path
                            ))
                    else:
                        # Just a package name
                        self.dependencies.append(Dependency(
                            name=dep.strip(),
                            version="unknown",
                            dependency_type="runtime",
                            source_file=rel_path
                        ))

    def _analyze_pom_xml(self, file_path: Path, rel_path: str) -> None:
        """Analyze Maven pom.xml file."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Handle Maven namespace
            ns = {'mvn': 'http://maven.apache.org/POM/4.0.0'}
            if root.tag.startswith('{'):
                # Extract namespace from root tag
                ns_uri = re.match(r'\{([^}]+)\}', root.tag)
                if ns_uri:
                    ns = {'mvn': ns_uri.group(1)}

            # Find dependencies
            dependencies_elem = root.find('.//mvn:dependencies', ns)
            if dependencies_elem is not None:
                for dep_elem in dependencies_elem.findall('mvn:dependency', ns):
                    # Get groupId, artifactId, version
                    group_elem = dep_elem.find('mvn:groupId', ns)
                    artifact_elem = dep_elem.find('mvn:artifactId', ns)
                    version_elem = dep_elem.find('mvn:version', ns)
                    scope_elem = dep_elem.find('mvn:scope', ns)

                    if group_elem is not None and artifact_elem is not None:
                        group_id = group_elem.text or ""
                        artifact_id = artifact_elem.text or ""
                        version = version_elem.text if version_elem is not None else "unknown"
                        scope = scope_elem.text if scope_elem is not None else "compile"

                        # Combine groupId:artifactId for the dependency name
                        name = f"{group_id}:{artifact_id}" if group_id else artifact_id

                        self.dependencies.append(Dependency(
                            name=name,
                            version=version,
                            dependency_type=scope,
                            source_file=rel_path
                        ))
        except ET.ParseError as e:
            print(f"Warning: Could not parse XML in {rel_path}: {e}")

    def _analyze_gradle_file(self, file_path: Path, rel_path: str) -> None:
        """Analyze Gradle build file (basic implementation)."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for implementation, api, compile, etc. dependencies
        # Patterns like: implementation 'group:name:version'
        dependency_patterns = [
            r'(implementation|api|compile|compileOnly|runtimeOnly|testImplementation)'
            r'\s*[\'"]([^\'"]+)[\'"]',
            r'(implementation|api|compile|compileOnly|runtimeOnly|testImplementation)'
            r'\s*\([^)]*[\'"]([^\'"]+)[\'"]',
        ]

        for pattern in dependency_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    dependency_type = match[0].lower()
                    dependency_spec = match[1]
                else:
                    dependency_type = "implementation"
                    dependency_spec = match

                # Parse group:name:version or group:name
                parts = dependency_spec.split(':')
                if len(parts) >= 2:
                    name = ':'.join(parts[:-1])  # Everything except the last part (version)
                    version = parts[-1] if len(parts) >= 3 else "unknown"
                else:
                    name = dependency_spec
                    version = "unknown"

                self.dependencies.append(Dependency(
                    name=name,
                    version=version,
                    dependency_type=dependency_type,
                    source_file=rel_path
                ))

    def _analyze_composer_json(self, file_path: Path, rel_path: str) -> None:
        """Analyze PHP composer.json file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Analyze require and require-dev
        for dep_type in ['require', 'require-dev']:
            if dep_type in data:
                for name, version in data[dep_type].items():
                    # Skip self/package and platform packages
                    if name in ['php', 'hhvm', 'lib-*']:
                        continue

                    # Clean version constraint
                    clean_version = version.lstrip('^~><=|')
                    dependency_type = "dev" if dep_type == "require-dev" else "runtime"

                    self.dependencies.append(Dependency(
                        name=name,
                        version=clean_version,
                        dependency_type=dependency_type,
                        source_file=rel_path
                    ))

    def _analyze_cargo_toml(self, file_path: Path, rel_path: str) -> None:
        """Analyze Rust Cargo.toml file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)

        # Check dependencies, dev-dependencies, build-dependencies
        for dep_type in ['dependencies', 'dev-dependencies', 'build-dependencies']:
            if dep_type in data:
                for name, dep_info in data[dep_type].items():
                    if isinstance(dep_info, str):
                        # Simple version string
                        version = dep_info
                    elif isinstance(dep_info, dict):
                        # Complex dependency specification
                        version = dep_info.get('version', '*')
                    else:
                        version = "unknown"

                    # Map Cargo dependency types to our types
                    dependency_type_map = {
                        'dependencies': 'runtime',
                        'dev-dependencies': 'dev',
                        'build-dependencies': 'build'
                    }
                    dependency_type = dependency_type_map.get(dep_type, 'runtime')

                    self.dependencies.append(Dependency(
                        name=name,
                        version=version,
                        dependency_type=dependency_type,
                        source_file=rel_path
                    ))

    def _analyze_go_mod(self, file_path: Path, rel_path: str) -> None:
        """Analyze Go go.mod file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find require blocks
        require_pattern = r'require\s*\(([^)]+)\)'
        requires = re.findall(require_pattern, content, re.DOTALL | re.IGNORECASE)

        # Also handle single line requires
        single_require_pattern = r'require\s+[^\s]+\s+[^\s]+'
        single_matches = re.findall(single_require_pattern, content)

        all_requires = requires
        for match in single_matches:
            # Extract the part after 'require'
            parts = match.split()
            if len(parts) >= 3:
                all_requires.append(' '.join(parts[1:]))

        for require_block in all_requires:
            lines = require_block.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line or line.startswith('//'):
                    continue

                # Parse module version format: module_path version
                parts = line.split()
                if len(parts) >= 2:
                    module_path = parts[0]
                    version = parts[1]

                    # Skip go module itself
                    if not module_path.startswith('golang.org'):
                        self.dependencies.append(Dependency(
                            name=module_path,
                            version=version,
                            dependency_type="runtime",
                            source_file=rel_path
                        ))

        # Also handle replace directives if needed

    def _analyze_gemfile(self, file_path: Path, rel_path: str) -> None:
        """Analyze Ruby Gemfile (basic implementation)."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for gem declarations
        # gem 'name', 'version'
        # gem "name", "version"
        # gem 'name', '>= version'
        gem_pattern = r'gem\s*[\'"]([^\'"]+)[\'"]\s*(?:,\s*[\'"]([^\'"]+)[\'"])?'
        matches = re.findall(gem_pattern, content)

        for match in matches:
            gem_name = match[0]
            version = match[1] if len(match) > 1 and match[1] else "latest"

            self.dependencies.append(Dependency(
                name=gem_name,
                version=version,
                dependency_type="runtime",
                source_file=rel_path
            ))

    def _detect_ecosystem(self) -> Optional[str]:
        """Detect the primary ecosystem based on found dependency files."""
        if not self.dependency_files:
            return None

        # Check for ecosystem-specific files
        npm_files = ['package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml']
        pip_files = ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile']
        maven_files = ['pom.xml']
        gradle_files = ['build.gradle', 'build.gradle.kts']
        dotnet_files = ['*.csproj', '*.fsproj', 'packages.config']
        composer_files = ['composer.json']
        cargo_files = ['Cargo.toml']
        go_files = ['go.mod']
        gemfiles = ['Gemfile']

        for file in self.dependency_files:
            file_name = os.path.basename(file)
            if file_name in npm_files:
                return "npm"
            elif file_name in pip_files:
                return "pip"
            elif file_name in maven_files:
                return "maven"
            elif any(gf in file for gf in gradle_files):
                return "gradle"
            elif any(df in file for df in dotnet_files if not '*' in df) or \
                 any(fnmatch.fnmatch(file, df) for df in dotnet_files if '*' in df):
                return "dotnet"
            elif file_name in composer_files:
                return "composer"
            elif file_name in cargo_files:
                return "cargo"
            elif file_name in go_files:
                return "go"
            elif file_name in gemfiles:
                return "rubygems"

        # Default based on what we found
        if any('package.json' in f for f in self.dependency_files):
            return "npm"
        elif any(f.endswith(('.txt', '.toml')) for f in self.dependency_files):
            return "pip"
        elif any('pom.xml' in f for f in self.dependency_files):
            return "maven"

        return "unknown"

    def get_dependency_summary(self) -> Dict[str, Any]:
        """Get a summary of dependencies by type and ecosystem."""
        analysis = self.analyze_dependencies()

        # Group by dependency type
        by_type = {}
        for dep in analysis.dependencies:
            if dep.dependency_type not in by_type:
                by_type[dep.dependency_type] = []
            by_type[dep.dependency_type].append(dep.name)

        # Count by type
        type_counts = {}
        for dep_type, deps in by_type.items():
            type_counts[dep_type] = len(deps)

        return {
            "ecosystem": analysis.ecosystem,
            "total_dependencies": analysis.total_dependencies,
            "dependency_files": analysis.dependency_files,
            "by_type": type_counts,
            "dependencies": [
                {
                    "name": dep.name,
                    "version": dep.version,
                    "type": dep.dependency_type,
                    "source": dep.source_file
                }
                for dep in analysis.dependencies
            ]
        }
