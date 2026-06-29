"""
Team Lead Evidence Gate for AgentForge.
Implements evidence-based approval workflow for agent outputs.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


@dataclass
class EvidencePackage:
    """Represents a package of evidence supporting an agent's claim or output."""
    agent_name: str  # Which agent produced the output being validated
    agent_role: str  # The role of the agent (planner, builder, tester, etc.)
    task_id: str     # ID of the task being worked on
    output_type: str  # Type of output (plan, code, test_results, review, etc.)
    output_reference: str  # Reference to the actual output (could be ID, path, etc.)
    claim_statement: str  # The specific claim being made (e.g., "Feature X implements requirement Y")
    evidence_items: List['EvidenceItem'] = field(default_factory=list)
    collected_at: datetime = field(default_factory=datetime.now)
    collected_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_evidence(self, evidence: 'EvidenceItem') -> None:
        """Add an evidence item to the package."""
        self.evidence_items.append(evidence)

    def get_evidence_by_type(self, evidence_type: str) -> List['EvidenceItem']:
        """Get all evidence items of a specific type."""
        return [e for e in self.evidence_items if e.evidence_type == evidence_type]

    def is_sufficient(self, min_evidence_count: int = 1) -> bool:
        """Determine if the evidence package meets minimum sufficiency criteria."""
        return len(self.evidence_items) >= min_evidence_count

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the evidence package."""
        evidence_by_type = {}
        for evidence in self.evidence_items:
            if evidence.evidence_type not in evidence_by_type:
                evidence_by_type[evidence.evidence_type] = 0
            evidence_by_type[evidence.evidence_type] += 1

        return {
            "agent": f"{self.agent_name} ({self.agent_role})",
            "task_id": self.task_id,
            "output_type": self.output_type,
            "claim": self.claim_statement,
            "evidence_count": len(self.evidence_items),
            "evidence_by_type": evidence_by_type,
            "is_sufficient": self.is_sufficient(),
            "collected_at": self.collected_at.isoformat()
        }


@dataclass
class EvidenceItem:
    """Represents a single piece of evidence."""
    evidence_type: str  # Type of evidence (test_log, screenshot, document, etc.)
    description: str    # Human-readable description of what this evidence shows
    data: Any           # The actual evidence data (file path, content, etc.)
    relevance: str      # How this evidence supports the claim
    confidence: float = 1.0  # Confidence in this evidence (0.0 to 1.0)
    collected_at: datetime = field(default_factory=datetime.now)
    collected_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApprovalDecision:
    """Represents a decision made by the Team Lead based on evidence review."""
    decision_id: str
    evidence_package_id: str
    agent_name: str
    agent_role: str
    decision: str  # "approved", "rejected", "requires_rework"
    reasoning: str
    evidence_adequacy: float  # Score from 0.0 to 1.0 indicating how well evidence supports the claim
    approval_conditions: List[str] = field(default_factory=list)  # Conditions that must be met
    objections: List[str] = field(default_factory=list)  # Specific objections to the evidence/claim
    decided_at: datetime = field(default_factory=datetime.now)
    decided_by: str = "team_lead"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_approved(self) -> bool:
        """Check if the decision is an approval."""
        return self.decision == "approved"

    def needs_rework(self) -> bool:
        """Check if the decision requires rework."""
        return self.decision in ["rejected", "requires_rework"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "decision_id": self.decision_id,
            "evidence_package_id": self.evidence_package_id,
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "decision": self.decision,
            "reasoning": self.reasoning,
            "evidence_adequacy": self.evidence_adequacy,
            "approval_conditions": self.approval_conditions,
            "objections": self.objections,
            "decided_at": self.decided_at.isoformat(),
            "decided_by": self.decided_by,
            "metadata": self.metadata
        }


@dataclass
class ReworkRequest:
    """Represents a request for rework based on insufficient or inadequate evidence."""
    request_id: str
    evidence_package_id: str
    agent_name: str
    agent_role: str
    original_claim: str
    issues_identified: List[str]  # Specific problems with the evidence or claim
    required_evidence: List[str]  # What evidence is needed to proceed
    suggested_improvements: List[str]  # Suggestions for how to improve
    priority: str = "medium"  # low, medium, high, critical
    requested_at: datetime = field(default_factory=datetime.now)
    requested_by: str = "team_lead"
    due_by: Optional[datetime] = None  # When the rework should be completed by
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_high_priority(self) -> bool:
        """Check if this is a high priority rework request."""
        return self.priority in ["high", "critical"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "request_id": self.request_id,
            "evidence_package_id": self.evidence_package_id,
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "original_claim": self.original_claim,
            "issues_identified": self.issues_identified,
            "required_evidence": self.required_evidence,
            "suggested_improvements": self.suggested_improvements,
            "priority": self.priority,
            "requested_at": self.requested_at.isoformat(),
            "requested_by": self.requested_by,
            "due_by": self.due_by.isoformat() if self.due_by else None,
            "metadata": self.metadata
        }


class EvidenceValidator:
    """
    Validates evidence packages against predefined criteria and standards.
    Determines whether evidence is sufficient to support claims made by agents.
    """

    def __init__(self):
        # Define evidence requirements for different agent roles and output types
        self.evidence_requirements = {
            "planner": {
                "plan": ["requirements_document", "acceptance_criteria", "task_breakdown"],
                "requirements": ["stakeholder_approval", "requirements_traceability_matrix"],
                "risks": ["risk_assessment_document", "mitigation_plan"]
            },
            "architect": {
                "design": ["architecture_diagram", "component_specification", "interface_definition"],
                "api_design": ["api_specification", "data_model", "security_considerations"],
                "database_design": ["schema_diagram", "normalization_documentation", "performance_considerations"]
            },
            "builder": {
                "code": ["source_code", "unit_test_results", "build_artifacts"],
                "feature": ["working_software_demo", "integration_test_results", "user_acceptance_feedback"],
                "bug_fix": ["failing_test_before", "passing_test_after", "root_cause_analysis"]
            },
            "tester": {
                "test_results": ["test_execution_log", "coverage_report", "defect_report"],
                "test_plan": ["test_strategy_document", "test_case_specifications", "test_data"],
                "automation": ["test_scripts", "ci_cd_pipeline_logs", "test_environment_specs"]
            },
            "reviewer": {
                "code_review": ["review_comments", "approved_changeset", "review_checklist"],
                "security_review": ["vulnerability_assessment", "penetration_test_results", "compliance_report"],
                "architecture_review": ["architecture_feedback", "design_pattern_analysis", "scalability_assessment"]
            },
            "security": {
                "vulnerability_assessment": ["scan_results", "remediation_plan", "risk_assessment"],
                "compliance": ["audit_report", "compliance_checklist", "certification_evidence"],
                "penetration_test": ["test_methodology", "findings_report", "remediation_recommendations"]
            },
            "deployment": {
                "release": ["release_notes", "deployment_logs", "rollback_plan"],
                "environment": ["configuration_files", "infrastructure_as_code", "health_check_results"],
                "rollback": ["backup_verification", "rollback_test_results", "service_restored"]
            }
        }

    def validate_evidence_package(self, evidence_package: EvidencePackage,
                                minimum_confidence: float = 0.7) -> Dict[str, Any]:
        """
        Validate an evidence package against requirements for the agent's role and output type.

        Args:
            evidence_package: The evidence package to validate
            minimum_confidence: Minimum confidence score required (0.0 to 1.0)

        Returns:
            Dictionary containing validation results
        """
        agent_role = evidence_package.agent_role
        output_type = evidence_package.output_type

        # Get required evidence types for this combination
        required_types = self.evidence_requirements.get(agent_role, {}).get(
            output_type, ["general_evidence"]
        )

        # Check what evidence we actually have
        provided_evidence_types = [e.evidence_type for e in evidence_package.evidence_items]

        # Calculate coverage
        covered_requirements = []
        missing_requirements = []

        for req_type in required_types:
            # Check if we have evidence of this type (exact match or subtype)
            if any(req_type in provided_type or provided_type in req_type
                   for provided_type in provided_evidence_types):
                covered_requirements.append(req_type)
            else:
                missing_requirements.append(req_type)

        # Calculate evidence adequacy score
        if len(required_types) == 0:
            adequacy_score = 1.0  # No requirements means automatically sufficient
        else:
            adequacy_score = len(covered_requirements) / len(required_types)

        # Factor in evidence confidence
        if evidence_package.evidence_items:
            avg_confidence = sum(e.confidence for e in evidence_package.evidence_items) / len(evidence_package.evidence_items)
            adequacy_score = (adequacy_score * 0.7) + (avg_confidence * 0.3)  # Weighted average

        # Determine if evidence is sufficient
        is_sufficient = (
            adequacy_score >= minimum_confidence and
            len(evidence_package.evidence_items) > 0
        )

        # Generate specific feedback
        strengths = []
        weaknesses = []
        recommendations = []

        # Analyze evidence quality
        high_confidence_evidence = [e for e in evidence_package.evidence_items if e.confidence >= 0.8]
        low_confidence_evidence = [e for e in evidence_package.evidence_items if e.confidence < 0.5]

        if high_confidence_evidence:
            strengths.append(f"{len(high_confidence_evidence)} high-confidence evidence items")
        if low_confidence_evidence:
            weaknesses.append(f"{len(low_confidence_evidence)} low-confidence evidence items (<0.5)")

        if not evidence_package.evidence_items:
            weaknesses.append("No evidence provided")
            recommendations.append("Provide relevant evidence to support your claims")
        elif len(missing_requirements) > 0:
            weaknesses.append(f"Missing evidence types: {', '.join(missing_requirements)}")
            recommendations.append(f"Provide evidence for: {', '.join(missing_requirements)}")
        else:
            strengths.append("All required evidence types provided")

        # Check evidence relevance
        relevant_evidence = [e for e in evidence_package.evidence_items if e.relevance.strip()]
        if len(relevant_evidence) == len(evidence_package.evidence_items):
            strengths.append("All evidence items have relevance explanations")
        else:
            weaknesses.append(f"{len(evidence_package.evidence_items) - len(relevant_evidence)} evidence items lack relevance explanations")
            recommendations.append("Explain how each piece of evidence supports your claim")

        return {
            "is_valid": is_sufficient,
            "evidence_adequacy": adequacy_score,
            "required_evidence_types": required_types,
            "provided_evidence_types": list(set(provided_evidence_types)),
            "covered_requirements": covered_requirements,
            "missing_requirements": missing_requirements,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "evidence_count": len(evidence_package.evidence_items),
            "high_confidence_count": len(high_confidence_evidence),
            "low_confidence_count": len(low_confidence_evidence)
        }

    def suggest_required_evidence(self, agent_role: str, output_type: str) -> List[str]:
        """Suggest what evidence should be provided for a given agent role and output type."""
        return self.evidence_requirements.get(agent_role, {}).get(
            output_type, ["Please consult documentation for specific evidence requirements"]
        )


# Convenience functions for creating common evidence types
def create_test_log_evidence(test_name: str, log_path: str, passed: bool,
                           description: str = None) -> EvidenceItem:
    """Create evidence from test execution logs."""
    return EvidenceItem(
        evidence_type="test_log",
        description=description or f"Test execution log for {test_name}",
        data={"test_name": test_name, "log_path": log_path, "passed": passed},
        relevance=f"Shows whether test '{test_name}' passed or failed",
        confidence=0.9 if passed else 0.3,  # High confidence for passing, low for failing
        metadata={"test_framework": "unknown"}  # Could be extended to detect framework
    )


def create_code_evidence(file_path: str, description: str = None) -> EvidenceItem:
    """Create evidence from source code files."""
    return EvidenceItem(
        evidence_type="source_code",
        description=description or f"Source code file: {file_path}",
        data={"file_path": file_path},
        relevance=f"Shows the implementation of {file_path}",
        confidence=0.8,
        metadata={"language": "detected_from_extension"}  # Could be enhanced
    )


def create_document_evidence(doc_path: str, doc_type: str, description: str = None) -> EvidenceItem:
    """Create evidence from documents."""
    return EvidenceItem(
        evidence_type=doc_type.lower().replace(" ", "_"),
        description=description or f"Document: {doc_path}",
        data={"file_path": doc_path, "document_type": doc_type},
        relevance=f"Provides {doc_type} information relevant to the claim",
        confidence=0.7,
        metadata={"document_format": "detected_from_extension"}
    )


def create_metrics_evidence(metric_name: str, value: float, unit: str = "",
                          description: str = None) -> EvidenceItem:
    """Create evidence from metrics/measurments."""
    return EvidenceItem(
        evidence_type="metric",
        description=description or f"Metric: {metric_name} = {value} {unit}",
        data={"metric_name": metric_name, "value": value, "unit": unit},
        relevance=f"Quantitative measurement of {metric_name}",
        confidence=0.8,  # Generally high confidence for objective measurements
        metadata={"measurement_type": "quantitative"}
    )
