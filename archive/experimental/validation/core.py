"""
Validation Architecture V2 for AgentForge.
Implements acceptance criteria-driven development and validation.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


@dataclass
class AcceptanceCriteria:
    """Represents a single acceptance criterion."""
    id: str
    description: str
    given: str  # Preconditions
    when: str   # Action/trigger
    then: str   # Expected outcome
    priority: str = "medium"  # high, medium, low
    category: str = "functional"  # functional, performance, security, usability, etc.
    testable: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AcceptanceTest:
    """Represents a test case derived from acceptance criteria."""
    id: str
    criteria_id: str  # References the parent acceptance criterion
    name: str
    description: str
    test_type: str = "functional"  # unit, integration, e2e, performance, security, etc.
    steps: List[str] = field(default_factory=list)
    expected_results: List[str] = field(default_factory=list)
    test_data: Dict[str, Any] = field(default_factory=dict)
    automation_script: Optional[str] = None  # Path to automated test script
    pass_criteria: List[str] = field(default_factory=list)
    fail_criteria: List[str] = field(default_factory=list)
    estimated_effort: Optional[int] = None  # in minutes
    actual_result: Optional[str] = None
    status: str = "not_run"  # not_run, passed, failed, blocked, skipped
    executed_at: Optional[datetime] = None
    executed_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationEvidence:
    """Represents evidence collected during validation."""
    id: str
    test_id: str  # References the test that produced this evidence
    type: str  # log, screenshot, metric, artifact, etc.
    description: str
    data: Any  # Could be file path, JSON, text, etc.
    collected_at: datetime = field(default_factory=datetime.now)
    collected_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Represents the result of validating acceptance criteria."""
    criteria_id: str
    is_satisfied: bool
    confidence_level: float = 1.0  # 0.0 to 1.0
    evidence: List[ValidationEvidence] = field(default_factory=list)
    passed_tests: List[str] = field(default_factory=list)  # Test IDs that passed
    failed_tests: List[str] = field(default_factory=list)  # Test IDs that failed
    skipped_tests: List[str] = field(default_factory=list)  # Test IDs that were skipped
    blocking_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.now)
    validated_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_evidence(self, evidence: ValidationEvidence) -> None:
        """Add evidence to this validation result."""
        self.evidence.append(evidence)

    def add_test_result(self, test_id: str, passed: bool) -> None:
        """Add a test result to this validation."""
        if passed:
            self.passed_tests.append(test_id)
        else:
            self.failed_tests.append(test_id)

    def is_passing(self) -> bool:
        """Determine if the validation is considered passing."""
        # Basic implementation: no failed tests and no blocking issues
        return len(self.failed_tests) == 0 and len(self.blocking_issues) == 0

    def get_completion_percentage(self) -> float:
        """Get the percentage of tests that have been executed."""
        total_tests = len(self.passed_tests) + len(self.failed_tests) + len(self.skipped_tests)
        if total_tests == 0:
            return 0.0
        return (len(self.passed_tests) / total_tests) * 100.0
