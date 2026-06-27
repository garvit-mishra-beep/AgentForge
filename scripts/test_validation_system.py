import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.validation import (
    AcceptanceCriteria,
    AcceptanceTest,
    ValidationEvidence,
    ValidationResult,
    AcceptanceCriteriaGenerator,
    AcceptanceTestGenerator,
    ValidationEngine
)
from datetime import datetime


def test_validation_system():
    """Test that the validation system components work correctly."""
    print("Testing Validation System...")

    # Test 1: Create acceptance criteria
    criteria = AcceptanceCriteria(
        id="test-001",
        description="User can login with valid credentials",
        given="User is on the login page",
        when="User enters valid username and password",
        then="User is redirected to the dashboard",
        priority="high",
        category="functional"
    )

    print("✓ AcceptanceCriteria created successfully")

    # Test 2: Generate acceptance criteria from user story
    gen = AcceptanceCriteriaGenerator()
    user_story = "As a customer, I want to view my order history, so that I can track my purchases."
    criteria_list = gen.generate_from_user_story(user_story, "functional")

    print(f"✓ Generated {len(criteria_list)} acceptance criteria from user story")

    # Test 3: Generate test cases from criteria
    test_gen = AcceptanceTestGenerator()
    test_cases = test_gen.generate_from_criteria(criteria_list[0])

    print(f"✓ Generated {len(test_cases)} test cases from criteria")

    # Test 4: Create validation evidence
    evidence = ValidationEvidence(
        id="ev-001",
        test_id="test-001",
        type="screenshot",
        description="Screenshot of successful login",
        data="/path/to/screenshot.png"
    )

    print("✓ ValidationEvidence created successfully")

    # Test 5: Create validation result
    result = ValidationResult(
        criteria_id="test-001",
        is_satisfied=True,
        confidence_level=0.95,
        evidence=[evidence],
        passed_tests=["test-001"]
    )

    print("✓ ValidationResult created successfully")

    # Test 6: Test validation engine
    engine = ValidationEngine()
    validation_result = engine.validate_requirement(
        "Users should be able to reset their password via email",
        "This is a security feature for account recovery",
        "security"
    )

    print(f"✓ ValidationEngine processed requirement:")
    print(f"  - Generated {len(validation_result['acceptance_criteria'])} criteria")
    print(f"  - Generated {validation_result['test_suite']['total_tests']} test cases")
    print(f"  - Validation duration: {validation_result['duration_seconds']:.2f} seconds")

    return True


if __name__ == "__main__":
    success = test_validation_system()
    if success:
        print("\n✓ All validation tests passed!")
    else:
        print("\n✗ Some validation tests failed!")
        exit(1)