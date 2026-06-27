"""
Validation System for AgentForge.

This package provides a complete validation framework including:
- Acceptance Criteria Generation
- Acceptance Test Generation
- Validation Engine that coordinates the validation process
"""

from .core import AcceptanceCriteria, AcceptanceTest, ValidationEvidence, ValidationResult
from .acceptance_criteria_generator import AcceptanceCriteriaGenerator
from .acceptance_test_generator import AcceptanceTestGenerator
from .validation_engine import ValidationEngine

__all__ = [
    # Core data structures
    "AcceptanceCriteria",
    "AcceptanceTest",
    "ValidationEvidence",
    "ValidationResult",

    # Generators
    "AcceptanceCriteriaGenerator",
    "AcceptanceTestGenerator",

    # Main engine
    "ValidationEngine"
]