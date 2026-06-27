"""
Evidence Validator Agent Node for AgentForge.
Integrates the Evidence Gate system into the agent workflow.
"""
import json
import logging
from typing import Dict, Any

from agents.sanitize import wrap_context, wrap_task
from agents.state import AgentState
from agents.utils import _is_timeout, call_with_timeout, load_prompt_template
from core.config import settings
from core.providers import get_provider, get_provider_for_user

# Import our evidence gate components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'app'))
from evidence_gate.core import EvidencePackage, EvidenceValidator, EvidenceItem

logger = logging.getLogger(__name__)


async def evidence_validator_node(state: AgentState) -> AgentState:
    """
    Agent node that validates evidence packages from other agents.
    This can be inserted into the workflow to enforce evidence-based approvals.
    """
    logger.info("Evidence Validator phase")

    # Get user and project context from state (with fallbacks)
    user_id = state.get("user_id", "00000000-0000-0000-0000-000000000001")
    project_id = state.get("project_id")
    db = state.get("db")  # Database session would be passed in state in a real implementation

    # Get the model for the evidence validator (could reuse team lead or have dedicated)
    model = state["team_config"].get("evidence_validator", {}).get("model",
                  state["team_config"].get("team_lead", {}).get("model", "default"))

    # Try to get user-specific provider configuration
    provider = None
    if db:
        try:
            provider, _ = await get_provider_for_user(
                model=model,
                user_id=user_id,
                project_id=project_id,
                db=db
            )
        except Exception as e:
            logger.warning("Failed to get user-specific provider, falling back to default: %s", e)
            provider = get_provider(model)
    else:
        # Fall back to default provider resolution
        provider = get_provider(model)

    timeout_s = settings.agent_timeout.get("evidence_validator", 30)
    max_tokens = settings.max_output_tokens if settings.fast_demo_mode else None

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

        # Store validation results in state for potential use by other agents
        validation_key = f"validation_{output_info['agent_name']}"
        state[validation_key] = validation_result

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

    # Store the summary in state
    state["evidence_validation_result"] = json.dumps(summary)
    state["current_step"] = state.get("current_step", "unknown") + "_evidence_validated"

    # Add to agent messages
    state["messages"].append({
        "role": "evidence_validator",
        "model": model,
        "content": json.dumps(summary, indent=2),
        "message_type": "evidence_validation",
        "metadata": {
            "validated_at
            }
        }

    logger.info("Evidence Validation complete")
    return state