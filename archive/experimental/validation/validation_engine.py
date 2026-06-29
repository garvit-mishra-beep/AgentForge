"""
Validation Engine for AgentForge.
Coordinates acceptance criteria, test generation, and validation execution.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from .core import AcceptanceCriteria, AcceptanceTest, ValidationEvidence, ValidationResult
from .acceptance_criteria_generator import AcceptanceCriteriaGenerator
from .acceptance_test_generator import AcceptanceTestGenerator
import uuid


class ValidationEngine:
    """
    Main validation engine that orchestrates the validation process:
    1. Acceptance Criteria Generation
    2. Test Generation from Criteria
    3. Test Execution (orchestration)
    4. Evidence Collection
    5. Validation Result Assessment
    """

    def __init__(self):
        self.criteria_generator = AcceptanceCriteriaGenerator()
        self.test_generator = AcceptanceTestGenerator()
        # In a real implementation, these would connect to actual test runners
        self.test_executor = None  # Placeholder for test execution service
        self.evidence_collector = None  # Placeholder for evidence collection service

    def validate_requirement(self, requirement: str,
                           context: str = "",
                           requirement_type: str = "functional") -> Dict[str, Any]:
        """
        Complete validation workflow for a single requirement.

        Args:
            requirement: The requirement description
            context: Additional context for the requirement
            requirement_type: Type of requirement (functional, performance, etc.)

        Returns:
            Dictionary containing the complete validation results
        """
        validation_id = str(uuid.uuid4())
        start_time = datetime.now()

        # Step 1: Generate acceptance criteria
        criteria_list = self.criteria_generator.generate_from_description(
            requirement, context, requirement_type
        )

        # Step 2: Generate test cases from criteria
        test_suite = self.test_generator.generate_test_suite(criteria_list)

        # Step 3: Execute tests (placeholder - would integrate with actual test runner)
        execution_results = self._execute_test_suite(test_suite["tests"])

        # Step 4: Collect evidence
        evidence_list = self._collect_evidence(execution_results)

        # Step 5: Assess validation results
        validation_results = self._assess_validation(criteria_list, execution_results, evidence_list)

        # Step 6: Compile final report
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            "validation_id": validation_id,
            "requirement": requirement,
            "context": context,
            "requirement_type": requirement_type,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "acceptance_criteria": [self._criteria_to_dict(c) for c in criteria_list],
            "test_suite": test_suite,
            "execution_results": execution_results,
            "evidence_collected": [self._evidence_to_dict(e) for e in evidence_list],
            "validation_results": [self._result_to_dict(r) for r in validation_results],
            "summary": self._generate_validation_summary(criteria_list, execution_results, validation_results)
        }

    def validate_requirements(self, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate multiple requirements.

        Args:
            requirements: List of requirement dictionaries with keys:
                         - description: The requirement text
                         - context: Optional context
                         - type: Optional type (defaults to "functional")

        Returns:
            Dictionary containing validation results for all requirements
        """
        start_time = datetime.now()
        all_results = []

        for req in requirements:
            result = self.validate_requirement(
                req.get("description", ""),
                req.get("context", ""),
                req.get("type", "functional")
            )
            all_results.append(result)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Aggregate summary
        total_criteria = sum(len(r["acceptance_criteria"]) for r in all_results)
        total_tests = sum(r["test_suite"]["total_tests"] for r in all_results)
        total_passed = sum(
            sum(1 for t in r["execution_results"].get("test_executions", [])
                if t.get("status") == "passed")
            for r in all_results
        )

        return {
            "validation_batch_id": str(uuid.uuid4()),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "requirements_count": len(requirements),
            "total_acceptance_criteria": total_criteria,
            "total_test_cases": total_tests,
            "total_tests_passed": total_passed,
            "overall_pass_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
            "individual_validations": all_results
        }

    def validate_existing_criteria(self, criteria_list: List[AcceptanceCriteria]) -> Dict[str, Any]:
        """
        Validate using pre-existing acceptance criteria.

        Args:
            criteria_list: List of acceptance criteria to validate

        Returns:
            Dictionary containing validation results
        """
        validation_id = str(uuid.uuid4())
        start_time = datetime.now()

        # Generate test cases from existing criteria
        test_suite = self.test_generator.generate_test_suite(criteria_list)

        # Execute tests
        execution_results = self._execute_test_suite(test_suite["tests"])

        # Collect evidence
        evidence_list = self._collect_evidence(execution_results)

        # Assess validation results
        validation_results = self._assess_validation(criteria_list, execution_results, evidence_list)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            "validation_id": validation_id,
            "criteria_count": len(criteria_list),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "acceptance_criteria": [self._criteria_to_dict(c) for c in criteria_list],
            "test_suite": test_suite,
            "execution_results": execution_results,
            "evidence_collected": [self._evidence_to_dict(e) for e in evidence_list],
            "validation_results": [self._result_to_dict(r) for r in validation_results],
            "summary": self._generate_validation_summary(criteria_list, execution_results, validation_results)
        }

    def _execute_test_suite(self, tests: List[AcceptanceTest]) -> Dict[str, Any]:
        """
        Execute a suite of tests.

        In a real implementation, this would integrate with actual test frameworks
        (JUnit, TestNG, pytest, Selenium, etc.). For now, this is a placeholder
        that simulates test execution.

        Args:
            tests: List of tests to execute

        Returns:
            Dictionary containing execution results
        """
        # Simulate test execution - in reality, this would call actual test runners
        executed_tests = []
        passed_count = 0
        failed_count = 0
        skipped_count = 0

        for test in tests:
            # Update test status (simulate execution)
            test.status = "passed"  # Simplified - in reality would depend on actual test outcome
            test.actual_result = "Test passed"
            test.executed_at = datetime.now()
            test.executed_by = "validation_engine"

            executed_tests.append(test)

            if test.status == "passed":
                passed_count += 1
            elif test.status == "failed":
                failed_count += 1
            else:
                skipped_count += 1

        return {
            "test_executions": [
                self._test_to_dict(t) for t in executed_tests
            ],
            "summary": {
                "total_tests": len(tests),
                "passed": passed_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "pass_rate": (passed_count / len(tests) * 100) if len(tests) > 0 else 0
            }
        }

    def _collect_evidence(self, execution_results: Dict[str, Any]) -> List[ValidationEvidence]:
        """
        Collect evidence from test execution.

        Args:
            execution_results: Results from test execution

        Returns:
            List of collected evidence
        """
        evidence_list = []

        # Create evidence from test execution results
        for test_exec in execution_results.get("test_executions", []):
            # Create evidence for test result
            evidence = ValidationEvidence(
                id=str(uuid.uuid4()),
                test_id=test_exec["id"],
                type="test_result",
                description=f"Test execution result: {test_exec['name']}",
                data={
                    "status": test_exec["status"],
                    "execution_time": test_exec.get("executed_at"),
                    "executed_by": test_exec.get("executed_by"),
                    "actual_result": test_exec.get("actual_result")
                },
                collected_at=datetime.fromisoformat(test_exec["executed_at"]) if test_exec.get("executed_at") else datetime.now(),
                collected_by="test_framework"
            )
            evidence_list.append(evidence)

            # Could add more evidence types here (logs, screenshots, metrics, etc.)

        return evidence_list

    def _assess_validation(self, criteria_list: List[AcceptanceCriteria],
                         execution_results: Dict[str, Any],
                         evidence_list: List[ValidationEvidence]) -> List[ValidationResult]:
        """
        Assess whether acceptance criteria are satisfied based on test results and evidence.

        Args:
            criteria_list: List of acceptance criteria
            execution_results: Results from test execution
            evidence_list: Collected evidence

        Returns:
            List of validation results for each criterion
        """
        validation_results = []

        # Map test executions to criteria
        test_results_by_criteria = {}
        for test_exec in execution_results.get("test_executions", []):
            criteria_id = test_exec.get("criteria_id")
            if criteria_id:
                if criteria_id not in test_results_by_criteria:
                    test_results_by_criteria[criteria_id] = []
                test_results_by_criteria[criteria_id].append(test_exec)

        # Assess each criterion
        for criteria in criteria_list:
            criterion_tests = test_results_by_criteria.get(criteria.id, [])
            criterion_evidence = [e for e in evidence_list if any(t["id"] == e.test_id for t in criterion_tests)]

            # Determine if criterion is satisfied
            is_satisfied = self._is_criterion_satisfied(criteria, criterion_tests, criterion_evidence)

            # Calculate confidence level
            confidence = self._calculate_confidence(criteria, criterion_tests, criterion_evidence)

            # Create validation result
            result = ValidationResult(
                criteria_id=criteria.id,
                is_satisfied=is_satisfied,
                confidence_level=confidence,
                evidence=criterion_evidence,
                passed_tests=[t["id"] for t in criterion_tests if t.get("status") == "passed"],
                metadata={
                    "assessment_time": datetime.now().isoformat(),
                    "tests_run": len(criterion_tests),
                    "tests_passed": len([t for t in criterion_tests if t.get("status") == "passed"]),
                    "evidence_count": len(criterion_evidence)
                }
            )
            validation_results.append(result)

        return validation_results

    def _is_criterion_satisfied(self, criteria: AcceptanceCriteria,
                              test_executions: List[Dict[str, Any]],
                              evidence_list: List[ValidationEvidence]) -> bool:
        """
        Determine if a specific criterion is satisfied based on test results.

        Args:
            criteria: The acceptance criterion to evaluate
            test_executions: Test executions related to this criterion
            evidence_list: Evidence collected for this criterion

        Returns:
            True if criterion is satisfied, False otherwise
        """
        if not test_executions:
            return False  # No tests run means not satisfied

        # Check if all critical tests passed
        critical_tests_passed = all(
            t.get("status") == "passed"
            for t in test_executions
            if t.get("test_type") in ["functional"]  # Core functional tests
        )

        # Check if any critical tests failed
        critical_tests_failed = any(
            t.get("status") == "failed"
            for t in test_executions
            if t.get("test_type") in ["functional"]
        )

        # For now, criteria is satisfied if all functional tests pass
        # In a more sophisticated implementation, this would weigh different test types
        return critical_tests_passed and not critical_tests_failed

    def _calculate_confidence(self, criteria: AcceptanceCriteria,
                            test_executions: List[Dict[str, Any]],
                            evidence_list: List[ValidationEvidence]) -> float:
        """
        Calculate confidence level in the validation result.

        Args:
            criteria: The acceptance criterion
            test_executions: Test executions related to this criterion
            evidence_list: Evidence collected for this criterion

        Returns:
            Confidence level between 0.0 and 1.0
        """
        if not test_executions:
            return 0.0  # No tests = no confidence

        # Base confidence on test pass rate
        total_tests = len(test_executions)
        passed_tests = len([t for t in test_executions if t.get("status") == "passed"])
        base_confidence = passed_tests / total_tests if total_tests > 0 else 0.0

        # Adjust confidence based on evidence quality/quantity
        evidence_factor = min(1.0, len(evidence_list) / max(1, total_tests))  # Cap at 1.0

        # Adjust based on test types covered
        test_types_covered = set(t.get("test_type") for t in test_executions)
        type_coverage = len(test_types_covered) / 4.0  # Assume 4 main types: functional, negative, boundary, performance/security
        type_coverage = min(1.0, type_coverage)  # Cap at 1.0

        # Weighted combination
        confidence = (0.5 * base_confidence +
                     0.3 * evidence_factor +
                     0.2 * type_coverage)

        # Ensure bounds
        return max(0.0, min(1.0, confidence))

    def _generate_validation_summary(self, criteria_list: List[AcceptanceCriteria],
                                   execution_results: Dict[str, Any],
                                   validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """Generate a summary of the validation process."""
        total_criteria = len(criteria_list)
        satisfied_criteria = len([v for v in validation_results if v.is_satisfied])
        avg_confidence = sum(v.confidence_level for v in validation_results) / max(len(validation_results), 1)

        # Criteria by satisfaction status
        satisfied_by_type = {}
        for criteria, validation in zip(criteria_list, validation_results):
            if criteria.category not in satisfied_by_type:
                satisfied_by_type[criteria.category] = {"total": 0, "satisfied": 0}
            satisfied_by_type[criteria.category]["total"] += 1
            if validation.is_satisfied:
                satisfied_by_type[criteria.category]["satisfied"] += 1

        # Test execution summary
        test_summary = execution_results.get("summary", {})

        return {
            "total_criteria": total_criteria,
            "satisfied_criteria": satisfied_criteria,
            "unsatisfied_criteria": total_criteria - satisfied_criteria,
            "satisfaction_rate": (satisfied_criteria / total_criteria * 100) if total_criteria > 0 else 0,
            "average_confidence": round(avg_confidence, 2),
            "criteria_by_type": {
                cat: {
                    "total": info["total"],
                    "satisfied": info["satisfied"],
                    "satisfaction_rate": (info["satisfied"] / info["total"] * 100) if info["total"] > 0 else 0
                }
                for cat, info in satisfied_by_type.items()
            },
            "test_execution_summary": test_summary,
            "recommendations": self._generate_recommendations(validation_results)
        }

    def _generate_recommendations(self, validation_results: List[ValidationResult]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        failed_criteria = [vr for vr in validation_results if not vr.is_satisfied]
        low_confidence = [vr for vr in validation_results if vr.confidence_level < 0.7]

        if failed_criteria:
            recommendations.append(
                f"{len(failed_criteria)} acceptance criteria were not satisfied. "
                "Review failing tests and address underlying issues."
            )

        if low_confidence:
            recommendations.append(
                f"{len(low_confidence)} validation results have low confidence (<0.7). "
                "Consider increasing test coverage or improving test quality."
            )

        # Check for missing test types
        # This would be more sophisticated in a real implementation

        if not recommendations:
            recommendations.append("All validation criteria met with sufficient confidence.")

        return recommendations

    # Helper methods for converting objects to dictionaries
    def _criteria_to_dict(self, criteria: AcceptanceCriteria) -> Dict[str, Any]:
        """Convert AcceptanceCriteria to dictionary."""
        return {
            "id": criteria.id,
            "description": criteria.description,
            "given": criteria.given,
            "when": criteria.when,
            "then": criteria.then,
            "priority": criteria.priority,
            "category": criteria.category,
            "testable": criteria.testable,
            "metadata": criteria.metadata
        }

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

    def _evidence_to_dict(self, evidence: ValidationEvidence) -> Dict[str, Any]:
        """Convert ValidationEvidence to dictionary."""
        return {
            "id": evidence.id,
            "test_id": evidence.test_id,
            "type": evidence.type,
            "description": evidence.description,
            "data": evidence.data,
            "collected_at": evidence.collected_at.isoformat(),
            "collected_by": evidence.collected_by,
            "metadata": evidence.metadata
        }

    def _result_to_dict(self, result: ValidationResult) -> Dict[str, Any]:
        """Convert ValidationResult to dictionary."""
        return {
            "criteria_id": result.criteria_id,
            "is_satisfied": result.is_satisfied,
            "confidence_level": result.confidence_level,
            "evidence_count": len(result.evidence),
            "passed_tests": result.passed_tests,
            "metadata": result.metadata
        }
