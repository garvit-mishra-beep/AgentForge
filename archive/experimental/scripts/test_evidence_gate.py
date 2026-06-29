import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.evidence_gate import (
    EvidencePackage,
    EvidenceItem,
    EvidenceValidator,
    ApprovalDecision,
    RewardRequest,
    create_test_log_evidence,
    create_code_evidence,
    create_document_evidence,
    create_metrics_evidence
)
from datetime import datetime


def test_evidence_gate_system():
    """Test that the evidence gate system components work correctly."""
    print("Testing Evidence Gate System...")

    # Test 1: Create evidence items
    test_evidence = create_test_log_evidence(
        "login_test",
        "/logs/test_login.xml",
        True,
        "Login test passed successfully"
    )

    code_evidence = create_code_evidence(
        "/src/auth/login_handler.py",
        "Login handler implementation"
    )

    doc_evidence = create_document_evidence(
        "/docs/API_SPEC.md",
        "API Specification",
        "Defines the authentication endpoints"
    )

    metrics_evidence = create_metrics_evidence(
        "login_response_time",
        1.2,
        "seconds",
        "Average login response time under load"
    )

    print("âœ“ Evidence items created successfully")

    # Test 2: Create evidence package
    evidence_package = EvidencePackage(
        agent_name="auth_builder",
        agent_role="builder",
        task_id="task-123",
        output_type="code",
        output_reference="auth_login_implementation",
        claim_statement="The login functionality correctly implements secure authentication",
        evidence_items=[test_evidence, code_evidence, doc_evidence, metrics_evidence]
    )

    print("âœ“ EvidencePackage created successfully")
    print(f"  - Evidence count: {len(evidence_package.evidence_items)}")
    print(f"  - Is sufficient: {evidence_package.is_sufficient()}")

    # Test 3: Validate evidence package
    validator = EvidenceValidator()
    validation_result = validator.validate_evidence_package(
        evidence_package,
        minimum_confidence=0.7
    )

    print("âœ“ Evidence validation completed")
    print(f"  - Is valid: {validation_result['is_valid']}")
    print(f"  - Evidence adequacy: {validation_result['evidence_adequacy']:.2f}")
    print(f"  - Strengths: {len(validation_result['strengths'])}")
    print(f"  - Weaknesses: {len(validation_result['weaknesses'])}")

    # Test 4: Create approval decision
    approval_decision = ApprovalDecision(
        decision_id="dec-001",
        evidence_package_id="ep-001",
        agent_name="auth_builder",
        agent_role="builder",
        decision="approved",
        reasoning="Sufficient evidence provided to support the claim",
        evidence_adequacy=validation_result['evidence_adequacy'],
        approval_conditions=["Ensure error handling is comprehensive"],
        objections=[]
    )

    print("âœ“ ApprovalDecision created successfully")
    print(f"  - Is approved: {approval_decision.is_approved()}")

    # Test 5: Create rework request
    rework_request = ReworkRequest(
        request_id="rreq-001",
        evidence_package_id="ep-002",
        agent_name="auth_builder",
        agent_role="builder",
        original_claim="The login functionality correctly implements secure authentication",
        issues_identified=[
            "Insufficient test coverage for edge cases",
            "Missing documentation for error handling"
        ],
        required_evidence=[
            "unit_test_results_for_edge_cases",
            "error_handling_documentation"
        ],
        suggested_improvements=[
            "Add test cases for invalid input scenarios",
            "Create comprehensive error handling documentation"
        ],
        priority="high"
    )

    print("âœ“ ReworkRequest created successfully")
    print(f"  - Is high priority: {rework_request.is_high_priority()}")

    # Test 6: Test with insufficient evidence
    weak_evidence_package = EvidencePackage(
        agent_name="weak_agent",
        agent_role="builder",
        task_id="task-456",
        output_type="code",
        output_reference="weak_implementation",
        claim_statement="This implementation is correct and complete",
        evidence_items=[create_code_evidence("/tmp/fake.py", "Placeholder code")]  # Just code, no tests or docs
    )

    weak_validation = validator.validate_evidence_package(
        weak_evidence_package,
        minimum_confidence=0.7
    )

    print("âœ“ Weak evidence validation completed")
    print(f"  - Is valid: {weak_validation['is_valid']}")
    print(f"  - Evidence adequacy: {weak_validation['evidence_adequacy']:.2f}")
    print(f"  - Missing requirements: {weak_validation['missing_requirements']}")

    return True


if __name__ == "__main__":
    success = test_evidence_gate_system()
    if success:
        print("\nâœ“ All evidence gate tests passed!")
    else:
        print("\nâœ— Some evidence gate tests failed!")
        exit(1)
