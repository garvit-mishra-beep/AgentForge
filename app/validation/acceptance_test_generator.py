"""
Acceptance Test Generator for AgentForge.
Generates test cases from acceptance criteria.
"""
from typing import List, Dict, Any, Optional
from .core import AcceptanceTest, AcceptanceCriteria
import uuid
import re


class AcceptanceTestGenerator:
    """
    Generates test cases from acceptance criteria.
    Creates test steps, expected results, and test data based on
    the Given-When-Then format of acceptance criteria.
    """

    def __init__(self):
        # Templates for different test types
        self.test_templates = {
            "functional": {
                "name_template": "Verify {description}",
                "steps_template": [
                    "Given: {given}",
                    "When: {when}",
                    "Then: {then}"
                ]
            },
            "negative": {
                "name_template": "Verify error handling for {description}",
                "steps_template": [
                    "Given: {given} with invalid input",
                    "When: {when}",
                    "Then: System should handle error gracefully"
                ]
            },
            "boundary": {
                "name_template": "Verify boundary conditions for {description}",
                "steps_template": [
                    "Given: {given} at boundary values",
                    "When: {when}",
                    "Then: System should behave correctly at boundaries"
                ]
            },
            "performance": {
                "name_template": "Performance test for {description}",
                "steps_template": [
                    "Given: {given} under load conditions",
                    "When: {when}",
                    "Then: System should respond within performance thresholds"
                ]
            },
            "security": {
                "name_template": "Security test for {description}",
                "steps_template": [
                    "Given: {given} with security context",
                    "When: {when} (attempting unauthorized access)",
                    "Then: System should prevent unauthorized access"
                ]
            }
        }

    def generate_from_criteria(self, criteria: AcceptanceCriteria,
                             test_types: Optional[List[str]] = None) -> List[AcceptanceTest]:
        """
        Generate test cases from a single acceptance criterion.

        Args:
            criteria: The acceptance criterion to generate tests for
            test_types: Optional list of test types to generate (functional, negative, boundary, etc.)

        Returns:
            List of generated acceptance tests
        """
        if test_types is None:
            test_types = ["functional", "negative", "boundary"]

        tests = []

        # Generate primary functional test
        if "functional" in test_types:
            functional_test = self._create_functional_test(criteria)
            tests.append(functional_test)

        # Generate negative test
        if "negative" in test_types:
            negative_test = self._create_negative_test(criteria)
            tests.append(negative_test)

        # Generate boundary test
        if "boundary" in test_types:
            boundary_test = self._create_boundary_test(criteria)
            tests.append(boundary_test)

        # Generate performance test if criteria is performance-related
        if "performance" in test_types and criteria.category in ["performance", "functional"]:
            perf_test = self._create_performance_test(criteria)
            tests.append(perf_test)

        # Generate security test if criteria is security-related
        if "security" in test_types and criteria.category in ["security", "functional"]:
            sec_test = self._create_security_test(criteria)
            tests.append(sec_test)

        return tests

    def generate_from_criteria_list(self, criteria_list: List[AcceptanceCriteria],
                                  test_types_per_criteria: Optional[Dict[str, List[str]]] = None) -> List[AcceptanceTest]:
        """
        Generate test cases from a list of acceptance criteria.

        Args:
            criteria_list: List of acceptance criteria
            test_types_per_criteria: Optional dict mapping criteria IDs to test types to generate

        Returns:
            List of all generated acceptance tests
        """
        all_tests = []

        for criteria in criteria_list:
            test_types = None
            if test_types_per_criteria and criteria.id in test_types_per_criteria:
                test_types = test_types_per_criteria[criteria.id]

            tests = self.generate_from_criteria(criteria, test_types)
            all_tests.extend(tests)

        return all_tests

    def _create_functional_test(self, criteria: AcceptanceCriteria) -> AcceptanceTest:
        """Create a functional test from acceptance criteria."""
        return AcceptanceTest(
            id=str(uuid.uuid4()),
            criteria_id=criteria.id,
            name=f"Verify: {criteria.description}",
            description=f"Test to verify: {criteria.then}",
            test_type="functional",
            steps=[
                f"Given: {criteria.given}",
                f"When: {criteria.when}",
                f"Then: {criteria.then}"
            ],
            expected_results=[criteria.then],
            pass_criteria=[criteria.then],
            fail_criteria=[f"System does not satisfy: {criteria.then}"],
            estimated_effort=15,  # Default 15 minutes
            metadata={
                "generated_from": "acceptance_criteria",
                "generation_type": "functional",
                "priority": criteria.priority
            }
        )

    def _create_negative_test(self, criteria: AcceptanceCriteria) -> AcceptanceTest:
        """Create a negative test from acceptance criteria."""
        return AcceptanceTest(
            id=str(uuid.uuid4()),
            criteria_id=criteria.id,
            name=f"Validate error handling for: {criteria.description}",
            description=f"Test invalid inputs/error conditions for: {criteria.description}",
            test_type="negative",
            steps=[
                f"Given: {criteria.given} with invalid or unexpected input",
                f"When: {criteria.when}",
                "Then: System should provide appropriate error handling",
                "And: System should not crash or corrupt data"
            ],
            expected_results=[
                "System handles error gracefully",
                "Appropriate error message is displayed",
                "System remains in stable state"
            ],
            pass_criteria=[
                "Error is handled gracefully",
                "Meaningful error message provided",
                "No system crash or data corruption"
            ],
            fail_criteria=[
                "System crashes or throws unhandled exception",
                "No error message provided",
                "System enters invalid state"
            ],
            estimated_effort=20,
            metadata={
                "generated_from": "acceptance_criteria",
                "generation_type": "negative",
                "priority": criteria.priority
            }
        )

    def _create_boundary_test(self, criteria: AcceptanceCriteria) -> AcceptanceTest:
        """Create a boundary test from acceptance criteria."""
        return AcceptanceTest(
            id=str(uuid.uuid4()),
            criteria_id=criteria.id,
            name=f"Validate boundary conditions for: {criteria.description}",
            description=f"Test boundary/edge cases for: {criteria.description}",
            test_type="boundary",
            steps=[
                f"Given: {criteria.given} at minimum/maximum limits",
                f"When: {criteria.when}",
                "Then: System should handle boundary values correctly",
                "And: No buffer overflows or underflows should occur"
            ],
            expected_results=[
                "System processes boundary values correctly",
                "Output is within expected ranges",
                "No memory corruption occurs"
            ],
            pass_criteria=[
                "All boundary values processed correctly",
                "Output validation passes",
                "Memory integrity maintained"
            ],
            fail_criteria=[
                "Boundary value causes incorrect output",
                "Memory corruption detected",
                "System fails to handle edge case"
            ],
            estimated_effort=25,
            metadata={
                "generated_from": "acceptance_criteria",
                "generation_type": "boundary",
                "priority": criteria.priority
            }
        )

    def _create_performance_test(self, criteria: AcceptanceCriteria) -> AcceptanceTest:
        """Create a performance test from acceptance criteria."""
        return AcceptanceTest(
            id=str(uuid.uuid4()),
            criteria_id=criteria.id,
            name=f"Performance test: {criteria.description}",
            description=f"Measure performance of: {criteria.description}",
            test_type="performance",
            steps=[
                f"Given: {criteria.given} with typical load",
                f"When: {criteria.when} is executed repeatedly",
                "Then: Measure response time and throughput",
                "And: Verify performance meets requirements"
            ],
            expected_results=[
                "Response time within acceptable limits",
                "Throughput meets minimum requirements",
                "Resource usage within acceptable bounds"
            ],
            pass_criteria=[
                "Average response time < 2s (configurable)",
                "95th percentile response time < 5s (configurable)",
                "No performance degradation over time"
            ],
            fail_criteria=[
                "Response time exceeds threshold",
                "Throughput below minimum requirement",
                "Memory leak detected during test"
            ],
            estimated_effort=30,
            data_requirements=["Load test data", "Baseline performance metrics"],
            metadata={
                "generated_from": "acceptance_criteria",
                "generation_type": "performance",
                "priority": criteria.priority
            }
        )

    def _create_security_test(self, criteria: AcceptanceCriteria) -> AcceptanceTest:
        """Create a security test from acceptance criteria."""
        return AcceptanceTest(
            id=str(uuid.uuid4()),
            criteria_id=criteria.id,
            name=f"Security test: {criteria.description}",
            description=f"Verify security aspects of: {criteria.description}",
            test_type="security",
            steps=[
                f"Given: {criteria.given} with security considerations",
                f"When: {criteria.when} (attempting potential security breach)",
                "Then: Security controls should prevent unauthorized action",
                "And: Security event should be logged"
            ],
            expected_results=[
                "Unauthorized access is prevented",
                "Security event is logged and alerted",
                "No sensitive data is exposed"
            ],
            pass_criteria=[
                "Access control enforced correctly",
                "Audit trail created for attempt",
                "Data confidentiality maintained"
            ],
            fail_criteria=[
                "Unauthorized access successful",
                "Security event not logged",
                "Sensitive data exposed or leaked"
            ],
            estimated_effort=35,
            data_requirements=["Test user accounts with various roles", "Security test scripts"],
            metadata={
                "generated_from": "acceptance_criteria",
                "generation_type": "security",
                "priority": criteria.priority
            }
        )

    def generate_test_suite(self, criteria_list: List[AcceptanceCriteria],
                          include_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a complete test suite from acceptance criteria.

        Args:
            criteria_list: List of acceptance criteria
            include_types: Optional list of test types to include in suite

        Returns:
            Dictionary representing the test suite with statistics
        """
        if include_types is None:
            include_types = ["functional", "negative", "boundary"]

        tests = self.generate_from_criteria_list(criteria_list,
                                               {c.id: include_types for c in criteria_list})

        # Group tests by type and priority
        tests_by_type = {}
        tests_by_priority = {"high": [], "medium": [], "low": []}

        for test in tests:
            # By type
            if test.test_type not in tests_by_type:
                tests_by_type[test.test_type] = []
            tests_by_type[test.test_type].append(test)

            # By priority (from criteria)
            criteria = next((c for c in criteria_list if c.id == test.criteria_id), None)
            if criteria:
                priority = criteria.priority
                if priority in tests_by_priority:
                    tests_by_priority[priority].append(test)

        # Calculate estimates
        total_estimated_time = sum(t.estimated_effort or 0 for t in tests if t.estimated_effort)

        return {
            "test_suite_id": str(uuid.uuid4()),
            "generated_at": datetime.now().isoformat(),
            "source_criteria_count": len(criteria_list),
            "total_tests": len(tests),
            "tests_by_type": {k: len(v) for k, v in tests_by_type.items()},
            "tests_by_priority": {k: len(v) for k, v in tests_by_priority.items()},
            "estimated_total_time_minutes": total_estimated_time,
            "estimated_total_time_hours": round(total_estimated_time / 60, 1),
            "tests": tests
        }

    def to_junit_xml(self, test: AcceptanceTest) -> str:
        """Convert a single test to JUnit XML format (simplified)."""
        # This would generate actual JUnit XML in a real implementation
        return f"""<testcase classname="{test.criteria_id}" name="{test.name}">
    <!-- Test steps: {chr(10).join(test.steps)} -->
    <!-- Expected: {chr(10).join(test.expected_results)} -->
</testcase>"""

    def to_testng_xml(self, tests: List[AcceptanceTest]) -> str:
        """Convert multiple tests to TestNG XML format (simplified)."""
        # This would generate actual TestNG XML in a real implementation
        test_refs = "\n".join([f'        <include name="{test.name}"/>' for test in tests])
        return f"""<!DOCTYPE suite SYSTEM "https://testng.org/testng-1.0.dtd" >
<suite name="Acceptance Test Suite">
    <test name="Generated Acceptance Tests">
        <classes>
            <class name="generated.tests">
                <methods>
{test_refs}
                </methods>
            </class>
        </classes>
    </test>
</suite>"""

    def to_cucumber_feature(self, criteria: AcceptanceCriteria,
                          tests: List[AcceptanceTest]) -> str:
        """Convert criteria and tests to Cucumber feature format."""
        feature_lines = [
            f"Feature: {criteria.description}",
            "",
            f"  Background:",
            f"    Given {criteria.given}",
            "",
            f"  Scenario: {tests[0].name if tests else 'Main scenario'}"
        ]

        for test in tests:
            feature_lines.extend([
                "",
                f"  Scenario: {test.name}",
                f"    Given {test.steps[0].split(': ', 1)[1] if ': ' if ': ' in test.steps[0] else test.steps[0] if len(test.steps) > 0 else ''}",
                f"    When {test.steps[1].split(': ', 1)[1] if ': ' in test.steps[1] and len(test.steps) > 1 else test.steps[1] if len(test.steps) > 1 else ''}",
                f"    Then {test.steps[2].split(': ', 1)[1] if ': ' in test.steps[2] and len(test.steps) > 2 else test.steps[2] if len(test.steps) > 2 else ''}"
            ])

        return "\n".join(feature_lines)

    def to_json(self, tests: List[AcceptanceTest]) -> str:
        """Convert test list to JSON string."""
        return json.dumps([self._test_to_dict(t) for t in tests], indent=2)

    def from_json(self, json_str: str) -> List[AcceptanceTest]:
        """Create test list from JSON string."""
        data = json.loads(json_str)
        return [self._dict_to_test(item) for item in data]

    def _test_to_dict(self, test: AcceptanceTest) -> Dict[str, Any]:
        """Convert AcceptanceTest to dictionary."""
        return {
            "id": test.id,
            "criteria_id": test.criteria_id,
            "name": test.name,
            "description": test.description,
            "test_type": test.test_type,
            "steps": test.steps,
            "expected_results": test.expected_results,
            "test_data": test.test_data,
            "automation_script": test.automation_script,
            "pass_criteria": test.pass_criteria,
            "fail_criteria": test.fail_criteria,
            "estimated_effort": test.estimated_effort,
            "actual_result": test.actual_result,
            "status": test.status,
            "executed_at": test.executed_at.isoformat() if test.executed_at else None,
            "executed_by": test.executed_by,
            "metadata": test.metadata
        }

    def _dict_to_test(self, data: Dict[str, Any]) -> AcceptanceTest:
        """Convert dictionary to AcceptanceTest."""
        return AcceptanceTest(
            id=data["id"],
            criteria_id=data["criteria_id"],
            name=data["name"],
            description=data["description"],
            test_type=data["test_type"],
            steps=data["steps"],
            expected_results=data["expected_results"],
            test_data=data.get("test_data", {}),
            automation_script=data.get("automation_script"),
            pass_criteria=data.get("pass_criteria", []),
            fail_criteria=data.get("fail_criteria", []),
            estimated_effort=data.get("estimated_effort"),
            actual_result=data.get("actual_result"),
            status=data.get("status", "not_run"),
            executed_at=datetime.fromisoformat(data["executed_at"]) if data.get("executed_at") else None,
            executed_by=data.get("executed_by"),
            metadata=data.get("metadata", {})
        )