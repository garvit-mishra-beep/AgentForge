"""
Evidence Validator Agent Node for AgentForge.
Integrates the Evidence Gate system into the agent workflow.
"""
import json
import logging
import os

# Import our evidence gate components
import sys
from datetime import UTC, datetime
from typing import Any

from agents.state import AgentState
from core.providers import get_provider, get_provider_for_user  # noqa: F401

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'app')))
from evidence_gate.core import EvidencePackage, EvidenceValidator

logger = logging.getLogger(__name__)


async def evidence_validator_node(state: AgentState) -> dict[str, Any]:
    """
    Agent node that validates evidence packages from other agents.
    This can be inserted into the workflow to enforce evidence-based approvals.
    """
    logger.info("Evidence Validator phase")

    ev_config = state["team_config"].get("evidence_validator")
    tl_config = state["team_config"].get("team_lead")
    if ev_config and "model" in ev_config:
        model = ev_config["model"]
    elif tl_config and "model" in tl_config:
        model = tl_config["model"]
    else:
        model = "default"

    # No LLM calls are needed since validation runs locally, so provider resolution is bypassed.

    # Prepare inputs. In a real implementation, we would extract evidence packages from the state
    # For now, we'll create a placeholder validation based on existing outputs

    # Gather outputs from previous agents that we might want to validate
    outputs_to_validate = []

    # Check if we have a plan to validate
    if state.get("plan"):
        outputs_to_validate.append({
            "agent_name": "planner",
            "agent_role": "planner",
            "output_type": "plan",
            "output_reference": "state.plan",
            "claim": "The plan adequately addresses the task requirements"
        })

    # Check if we have builder output to validate
    if state.get("builder_output"):
        outputs_to_validate.append({
            "agent_name": "builder",
            "agent_role": "builder",
            "output_type": "code",
            "output_reference": "state.builder_output",
            "claim": "The implemented code satisfies the design requirements"
        })

    # Check if we have test results to validate
    if state.get("tester_output"):
        outputs_to_validate.append({
            "agent_name": "tester",
            "agent_role": "tester",
            "output_type": "test_results",
            "output_reference": "state.tester_output",
            "claim": "The tests adequately verify the implemented functionality"
        })

    # Check if we have review output to validate
    if state.get("review"):
        outputs_to_validate.append({
            "agent_name": "reviewer",
            "agent_role": "reviewer",
            "output_type": "review",
            "output_reference": "state.review",
            "claim": "The review provides adequate feedback on the implementation"
        })

    # Perform validation for each output
    validation_results = []
    validator = EvidenceValidator()

    for output_info in outputs_to_validate:
        # Create a basic evidence package (in reality, this would come from actual evidence collection)
        evidence_package = EvidencePackage(
            agent_name=output_info["agent_name"],
            agent_role=output_info["agent_role"],
            task_id=state["task"]["id"],
            output_type=output_info["output_type"],
            output_reference=output_info["output_reference"],
            claim_statement=output_info["claim"],
            evidence_items=[],  # Would be populated by actual evidence collection in real implementation
            collected_by="evidence_validator_agent"
        )

        # Validate the evidence package
        validation_result = validator.validate_evidence_package(evidence_package)

        validation_results.append({
            "agent": output_info["agent_name"],
            "validation": validation_result
        })

    # Create a summary validation result
    overall_valid = all(v["validation"]["is_valid"] for v in validation_results)
    overall_confidence = sum(v["validation"]["evidence_adequacy"] for v in validation_results) / max(len(validation_results), 1)

    summary = {
        "evidence_validation_completed": True,
        "overall_valid": overall_valid,
        "overall_confidence": overall_confidence,
        "validations_performed": len(validation_results),
        "individual_validations": validation_results
    }

    results_dict = {
        v["agent"]: v["validation"] for v in validation_results
    }

    logger.info("Evidence Validation complete")
    updates: dict[str, Any] = {
        "evidence_validation_result": results_dict,
        "messages": [{
            "role": "evidence_validator",
            "model": model,
            "content": json.dumps(summary, indent=2),
            "message_type": "evidence_validation",
            "metadata": {
                "validated_at": datetime.now(UTC).isoformat()
            }
        }]
    }

    # Only update current_step if not in parallel execution to avoid concurrent updates conflict
    current_step = state.get("current_step", "unknown")
    if current_step not in ("reviewer", "tester", "security"):
        updates["current_step"] = current_step + "_evidence_validated"

    return updates
