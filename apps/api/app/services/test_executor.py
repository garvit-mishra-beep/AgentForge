"""
Test Execution Service with Sandbox Security
Executes generated tests in secure, isolated environments.
"""
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

# Import the sandbox executor and related types
from app.services.sandbox_executor import (
    NetworkPolicy,
    ResourceLimits,
    SandboxConfig,
    SandboxExecutor,
    SecurityLevel,
)

logger = logging.getLogger(__name__)


class TestFramework(str, Enum):
    PYTEST = "pytest"
    VITEST = "vitest"
    JEST = "jest"


class TestResultStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class TestResult:
    """Result of executing a test suite."""
    status: TestResultStatus
    passed: int
    failed: int
    skipped: int
    duration_ms: int
    stdout: str
    stderr: str
    coverage_percent: float | None = None
    details: list[dict[str, Any]] | None = None


class TestExecutor:
    """Executes test code in secure, isolated sandbox environments."""

    def __init__(self):
        self.sandbox = SandboxExecutor()
        self.timeout_seconds = 30

        # Define Docker images for different languages/test frameworks
        self.images = {
            TestFramework.PYTEST: "python:3.11-slim",
            TestFramework.VITEST: "node:18-slim",
            TestFramework.JEST: "node:18-slim"
        }

    async def execute_python_tests(self, source_files: dict[str, str], test_files: dict[str, str]) -> TestResult:
        """
        Execute Python tests using pytest in a secure sandbox.

        Args:
            source_files: Dictionary mapping source file paths to their content
            test_files: Dictionary mapping test file paths to their content

        Returns:
            TestResult with execution outcome
        """
        start_time = time.time()

        try:
            # Prepare files for the sandbox
            all_files = {}

            # Add source files
            for file_path, content in source_files.items():
                all_files[f"src/{file_path}"] = content

            # Add test files
            for file_path, content in test_files.items():
                all_files[f"tests/{file_path}"] = content

            # Create a simple test runner script
            test_runner = '''import os
import sys
import subprocess
import json

def run_tests():
    try:
        # Change to workspace directory
        os.chdir("/workspace")

        # Install pytest if not available
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "-q"],
                      capture_output=True)

        # Run pytest with coverage if we have source files
        # Check if we have_source = os.path.exists("src") and bool(os.listdir("src"))
        cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]

        if have_source:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Parse results
        output = result.stdout + result.stderr
        passed = failed = skipped = 0

        # Simple parsing of pytest output
        import re
        match = re.search(r'(\\d+)\\s+passed', output)
        if match:
            passed = int(match.group(1))
        match = re.search(r'(\\d+)\\s+failed', output)
        if match:
            failed = int(match.group(1))
        match = re.search(r'(\\d+)\\s+skipped', output)
        if match:
            skipped = int(match.group(1))

        # Determine status
        if result.returncode == 0 and failed == 0:
            status = "PASSED"
        elif result.returncode != 0:
            status = "FAILED"
        else:
            status = "ERROR"

        # Extract coverage if available
        coverage = None
        if "TOTAL" in output and "%" in output:
            try:
                lines = output.split('\\n')
                for line in lines:
                    if "TOTAL" in line and "%" in line:
                        parts = line.split()
                        for part in parts:
                            if "%" in part and part.replace("%", "").replace(".", "").isdigit():
                                coverage = float(part.replace("%", ""))
                                break
                        break
            except (ValueError, IndexError):
                pass

        print(json.dumps({
            "status": status,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "coverage": coverage
        }))

    except Exception as e:
        print(json.dumps({
            "status": "ERROR",
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "stdout": "",
            "stderr": str(e),
            "coverage": None
        }))

if __name__ == "__main__":
    run_tests()
'''

            all_files["run_tests.py"] = test_runner

            # Configure sandbox for Python testing
            config = SandboxConfig(
                security_level=SecurityLevel.MAXIMUM,
                network_policy=NetworkPolicy.NONE,  # No network needed for basic testing
                resource_limits=ResourceLimits(
                    cpu_cpus=1.0,
                    memory_mb=512,
                    disk_mb=200,
                    max_processes=10
                ),
                max_execution_time=self.timeout_seconds,
                read_only_root=False,  # Need to write to /workspace for pytest-cache etc.
                tmpfs_size="64M"
            )

            # Execute in sandbox
            result = await self.sandbox.execute_in_sandbox(
                image=self.images[TestFramework.PYTEST],
                command=["python", "run_tests.py"],
                files=all_files,
                config=config
            )

            # Parse the result
            try:
                # Find the JSON line in stdout (last non-empty line that looks like JSON)
                result_json = None
                for line in reversed(result.stdout.strip().split('\n')):
                    if line.strip().startswith('{') and line.strip().endswith('}'):
                        try:
                            result_json = json.loads(line)
                            break
                        except json.JSONDecodeError:
                            continue

                if result_json is None:
                    raise ValueError("Could not find JSON result in output")

                status_map = {
                    "PASSED": TestResultStatus.PASSED,
                    "FAILED": TestResultStatus.FAILED,
                    "ERROR": TestResultStatus.ERROR
                }

                return TestResult(
                    status=status_map.get(result_json["status"], TestResultStatus.ERROR),
                    passed=result_json["passed"],
                    failed=result_json["failed"],
                    skipped=result_json["skipped"],
                    duration_ms=result.execution_time_ms,
                    stdout=result_json["stdout"],
                    stderr=result_json["stderr"],
                    coverage_percent=result_json.get("coverage"),
                    details=[{"sandbox_info": result.metadata}] if result.metadata else None
                )
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Failed to parse test result JSON: {e}")
                # Fallback to basic result parsing
                return TestResult(
                    status=TestResultStatus.FAILED if result.exit_code != 0 else TestResultStatus.PASSED,
                    passed=0,
                    failed=1 if result.exit_code != 0 else 0,
                    skipped=0,
                    duration_ms=result.execution_time_ms,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    details=[{"parse_error": str(e), "raw_output": result.stdout[:500]}]
                )

        except Exception as e:
            logger.error(f"Error executing Python tests: {e}")
            return TestResult(
                status=TestResultStatus.ERROR,
                passed=0,
                failed=0,
                skipped=0,
                duration_ms=int((time.time() - start_time) * 1000),
                stdout="",
                stderr=str(e),
                details=[{"error": str(e)}]
            )

    async def execute_javascript_tests(self, source_files: dict[str, str], test_files: dict[str, str], package_json: dict[str, Any] | None = None) -> TestResult:
        """
        Execute JavaScript/TypeScript tests using Vitest or Jest in a secure sandbox.

        Args:
            source_files: Dictionary mapping source file paths to their content
            test_files: Dictionary mapping test file paths to their content
            package_json: Package.json configuration

        Returns:
            TestResult with execution outcome
        """
        start_time = time.time()

        try:
            # Determine test framework from package.json or default to vitest
            framework = TestFramework.VITEST  # Default
            if package_json:
                deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
                if "jest" in deps:
                    framework = TestFramework.JEST
                elif "vitest" in deps:
                    framework = TestFramework.VITEST

            # Prepare files for the sandbox
            all_files = {}

            # Add source files
            for file_path, content in source_files.items():
                all_files[f"src/{file_path}"] = content

            # Add test files
            for file_path, content in test_files.items():
                all_files[f"tests/{file_path}"] = content

            # Create package.json if not provided or enhance existing one
            if not package_json:
                package_json = {
                    "name": "agentforge-test",
                    "version": "1.0.0",
                    "scripts": {
                        "test": "vitest run"  # Default to vitest
                    },
                    "devDependencies": {
                        "vitest": "^1.0.0"
                    }
                }
            else:
                # Ensure test script exists
                if "scripts" not in package_json:
                    package_json["scripts"] = {}
                if "test" not in package_json["scripts"]:
                    # Auto-detect based on dependencies
                    deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
                    if "vitest" in deps:
                        package_json["scripts"]["test"] = "vitest run"
                    elif "jest" in deps:
                        package_json["scripts"]["test"] = "jest"
                    else:
                        package_json["scripts"]["test"] = "vitest run"  # Default

            all_files["package.json"] = json.dumps(package_json, indent=2)

            # Create a test runner script for Node.js
            test_runner = '''const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

try {
    // Change to workspace directory
    process.chdir('/workspace');

    // Install dependencies
    console.log('Installing dependencies...');
    execSync('npm install', { stdio: 'pipe' });

    // Run tests
    console.log('Running tests...');
    const result = execSync('npm test', {
        encoding: 'utf8',
        maxBuffer: 1024 * 1024  // 1MB buffer
    });

    // Parse vitest/jest output (simple approach)
    const output = result;
    let passed = 0, failed = 0, skipped = 0;

    // Look for test results in output
    const passedMatch = output.match(/(\\d+)\\s+passed/);
    if (passedMatch) passed = parseInt(passedMatch[1]);

    const failedMatch = output.match(/(\\d+)\\s+failed/);
    if (failedMatch) failed = parseInt(failedMatch[1]);

    const skippedMatch = output.match(/(\\d+)\\s+skipped/);
    if (skippedMatch) skipped = parseInt(skippedMatch[1]);

    // Determine status
    let status;
    if (failed === 0) {
        status = "PASSED";
    } else {
        status = "FAILED";
    }

    console.log(JSON.stringify({
        status: status,
        passed: passed,
        failed: failed,
        skipped: skipped,
        stdout: result,
        stderr: ""
    }));

} catch (error) {
    console.log(JSON.stringify({
        status: "ERROR",
        passed: 0,
        failed: 0,
        skipped: 0,
        stdout: "",
        stderr: error.message || String(error)
    }));
}
'''

            all_files["run_tests.js"] = test_runner

            # Configure sandbox for Node.js testing
            config = SandboxConfig(
                security_level=SecurityLevel.MAXIMUM,
                network_policy=NetworkPolicy.RESTRICTED,  # Allow npm registry access
                resource_limits=ResourceLimits(
                    cpu_cpus=1.0,
                    memory_mb=512,
                    disk_mb=300,
                    max_processes=15
                ),
                max_execution_time=self.timeout_seconds + 30,  # Extra time for npm install
                read_only_root=False,  # Need to write node_modules etc.
                tmpfs_size="64M",
                environment_vars={
                    "NODE_ENV": "test"
                }
            )

            # Execute in sandbox
            result = await self.sandbox.execute_in_sandbox(
                image=self.images[framework],
                command=["node", "run_tests.js"],
                files=all_files,
                config=config
            )

            # Parse the result
            try:
                # Find the JSON line in stdout
                result_json = None
                for line in reversed(result.stdout.strip().split('\n')):
                    if line.strip().startswith('{') and line.strip().endswith('}'):
                        try:
                            result_json = json.loads(line)
                            break
                        except json.JSONDecodeError:
                            continue

                if result_json is None:
                    raise ValueError("Could not find JSON result in output")

                status_map = {
                    "PASSED": TestResultStatus.PASSED,
                    "FAILED": TestResultStatus.FAILED,
                    "ERROR": TestResultStatus.ERROR
                }

                return TestResult(
                    status=status_map.get(result_json["status"], TestResultStatus.ERROR),
                    passed=result_json["passed"],
                    failed=result_json["failed"],
                    skipped=result_json["skipped"],
                    duration_ms=result.execution_time_ms,
                    stdout=result_json["stdout"],
                    stderr=result_json["stderr"],
                    details=[{"sandbox_info": result.metadata, "framework": framework.value}] if result.metadata else None
                )
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Failed to parse JS test result JSON: {e}")
                # Fallback to basic result parsing
                return TestResult(
                    status=TestResultStatus.FAILED if result.exit_code != 0 else TestResultStatus.PASSED,
                    passed=0,
                    failed=1 if result.exit_code != 0 else 0,
                    skipped=0,
                    duration_ms=result.execution_time_ms,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    details=[{"parse_error": str(e), "framework": framework.value, "raw_output": result.stdout[:500]}]
                )

        except Exception as e:
            logger.error(f"Error executing JavaScript tests: {e}")
            return TestResult(
                status=TestResultStatus.ERROR,
                passed=0,
                failed=0,
                skipped=0,
                duration_ms=int((time.time() - start_time) * 1000),
                stdout="",
                stderr=str(e),
                details=[{"error": str(e)}]
            )

    # Keep the original method signatures for compatibility but delegate to secure versions
    async def execute_tests(
        self,
        source_files: dict[str, str],
        test_files: dict[str, str],
        framework: TestFramework = TestFramework.PYTEST,
        package_json: dict[str, Any] | None = None
    ) -> TestResult:
        """
        Execute tests in the specified framework using secure sandboxes.

        Args:
            source_files: Source files to test against
            test_files: Test files to execute
            framework: Test framework to use
            package_json: Package configuration for JS/TS projects

        Returns:
            TestResult with execution outcome
        """
        if framework == TestFramework.PYTEST:
            return await self.execute_python_tests(source_files, test_files)
        elif framework in (TestFramework.VITEST, TestFramework.JEST):
            return await self.execute_javascript_tests(source_files, test_files, package_json)
        else:
            raise ValueError(f"Unsupported test framework: {framework}")


# Global instance for backward compatibility
test_executor = TestExecutor()
