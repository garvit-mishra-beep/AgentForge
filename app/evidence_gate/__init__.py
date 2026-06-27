"""
Evidence Gate System for AgentForge.

This package implements evidence-based approval workflows requiring agents to
provide verifiable evidence for their claims before progressing in the workflow.
"""

from .core import (
    EvidencePackage,
    EvidenceValidator,
    EvidenceItem,
    ApprovalDecision,
    ReworkRequest,
    create_test_log_evidence,
    create_code_evidence,
    create_document_evidence,
    create_metrics_evidence
)

__all__ = [
    "EvidencePackage",
    "EvidenceValidator",
    "EvidenceItem",
    "ApprovalDecision",
    "ReworkRequest",
    "create_test_log_evidence",
    "create_code_evidence",
    "create_document_evidence",
    "create_metrics_evidence"
]