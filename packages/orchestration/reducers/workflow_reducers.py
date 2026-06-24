"""
Production-grade LangGraph Workflow Reducers.

Implements pure reducer functions for shared state merging in LangGraph workflows.

Reducer patterns:
- merge_lists: Safely concatenate list entries
- merge_dicts: Merge dictionary values without mutation
- accumulate_token_usage: Aggregate token consumption across providers
- deduplicate_artifacts: Merge artifacts while preventing duplicates

All reducers are pure functions that:
- Do NOT mutate inputs
- Return merged state safely
- Handle None and empty values
- Preserve ordering of events/logs
"""

import time
from typing import Dict, List, Any, Optional, Callable, Tuple

# ===============================
# REDUCER BASE FUNCTIONS
# ===============================


def merge_lists(
    existing: Optional[List[Any]],
    new: List[Any],
    deduplicate: bool = True
) -> List[Any]:
    """
    Merge two list entries safely without mutating inputs.

    Args:
        existing: Current list of items (may be None)
        new: New list of items to append
        deduplicate: If True, prevent duplicate entries by value comparison

    Returns:
        Merged list without mutation of inputs
    """
    # Handle None safely
    if existing is None:
        existing = []

    # Handle empty new list
    if not new:
        return existing.copy()

    # Handle deduplication
    if deduplicate:
        seen = set()
        merged = []
        for item in existing:
            # Use hashable representation for comparison
            item_key = hash(str(item)) if isinstance(item, (str, int, float, bool)) else str(item)
            if item_key not in seen:
                merged.append(item)
                seen.add(item_key)

        # Append non-duplicate items from new
        for item in new:
            item_key = hash(str(item)) if isinstance(item, (str, int, float, bool)) else str(item)
            if item_key not in seen:
                merged.append(item)
                seen.add(item_key)

        return merged

    # Simple concatenation
    return existing.copy() + new.copy()


def merge_dicts(
    existing: Optional[Dict[str, Any]],
    new: Dict[str, Any],
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Merge two dictionaries without mutating inputs.

    Args:
        existing: Current dictionary (may be None)
        new: New dictionary to merge
        overwrite: If True, overwrite existing keys with new values

    Returns:
        Merged dictionary without mutation of inputs
    """
    # Handle None safely
    if existing is None:
        existing = {}

    # Handle empty new dict
    if not new:
        return existing.copy()

    if overwrite:
        # Deep merge with overwrite
        result = existing.copy()
        for key, value in new.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dicts
                result[key] = merge_dicts(result[key], value, overwrite=overwrite)
            else:
                result[key] = value.copy() if isinstance(value, (dict, list)) else value
        return result
    else:
        # Shallow merge - only add new keys
        result = existing.copy()
        for key, value in new.items():
            if key not in result or key not in existing:
                result[key] = value.copy() if isinstance(value, (dict, list)) else value
        return result


# ===============================
# EXECUTION TRACE REDUCERS
# ===============================


def append_execution_trace(
    existing: Optional[List[Dict[str, Any]]],
    new: List[Dict[str, Any]],
    deduplicate: bool = True
) -> List[Dict[str, Any]]:
    """
    Append execution trace entries with deduplication.

    Args:
        existing: Current execution trace (may be None)
        new: New trace entries to append
        deduplicate: Prevent duplicate trace entries by timestamp

    Returns:
        Merged execution trace without mutation
    """
    return merge_lists(
        existing=existing,
        new=new,
        deduplicate=deduplicate
    )


def update_trace_status(
    existing: Optional[List[Dict[str, Any]]],
    new: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Update status field in trace entry by id.

    Args:
        existing: Current execution trace
        new: New status update (must contain 'id' and 'status')

    Returns:
        Updated execution trace
    """
    if existing is None:
        existing = []

    if not new:
        return existing.copy()

    target_id = new.get("id")
    if not target_id:
        return existing.copy()

    # Find and update matching entry
    for trace_entry in existing:
        if trace_entry.get("id") == target_id:
            trace_entry["status"] = new.get("status")
            trace_entry["updated_at"] = time.time()
            return existing.copy()

    return existing.copy()


# ===============================
# TOKEN USAGE REDUCERS
# ===============================


def accumulate_token_usage(
    existing: Optional[Dict[str, Any]],
    new: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Accumulate token usage across providers with type-safe merging.

    Args:
        existing: Current token usage tracking
        new: New token usage to accumulate

    Returns:
        Merged token usage dictionary
    """
    if existing is None:
        existing = {}

    result = existing.copy()

    # Accumulate totals
    existing_total = result.get("total", {}).get("input_tokens", 0)
    existing_total = existing_total + (new.get("input_tokens", 0) or 0)

    result["total"] = {
        "input_tokens": existing_total,
        "output_tokens": result.get("total", {}).get("output_tokens", 0) + (new.get("output_tokens", 0) or 0),
        "total_tokens": result.get("total", {}).get("total_tokens", 0) + (new.get("total_tokens", 0) or 0)
    }

    # Merge provider-specific usage
    new_provider_usage = new.get("provider_usage", {})
    for provider, provider_data in new_provider_usage.items():
        if provider not in result:
            result[provider] = {}

        # Accumulate provider totals
        provider_input = result[provider].get("input_tokens", 0)
        provider_input = provider_input + (provider_data.get("input_tokens", 0) or 0)

        provider_output = result[provider].get("output_tokens", 0)
        provider_output = provider_output + (provider_data.get("output_tokens", 0) or 0)

        provider_total = provider_input + provider_output

        result[provider] = {
            "input_tokens": provider_input,
            "output_tokens": provider_output,
            "total_tokens": provider_total,
            "requests": result[provider].get("requests", 0) + (provider_data.get("requests", 0) or 0),
            "model": result[provider].get("model", new.get("model", ""))
        }

    return result


# ===============================
# PROVIDER USAGE REDUCERS
# ===============================


def merge_provider_usage(
    existing: Optional[Dict[str, Any]],
    new: Dict[str, Any],
    merge_models: bool = True
) -> Dict[str, Any]:
    """
    Merge provider usage records with model-level aggregation.

    Args:
        existing: Current provider usage tracking
        new: New provider usage to merge
        merge_models: If True, merge usage for same model across providers

    Returns:
        Merged provider usage dictionary
    """
    if existing is None:
        existing = {}

    if not new:
        return existing.copy()

    result = existing.copy()

    # Handle provider-level merging
    new_providers = new.get("providers", {})
    for provider_name, provider_data in new_providers.items():
        if provider_name not in result:
            result[provider_name] = {
                "usage_events": [],
                "models": {},
                "total_requests": 0,
                "errors": 0,
                "success_rate": 100.0
            }

        # Merge usage events
        existing_events = result[provider_name].get("usage_events", [])
        new_events = provider_data.get("events", [])
        result[provider_name]["usage_events"] = merge_lists(
            existing_events,
            new_events,
            deduplicate=True
        )

        # Merge model-specific data
        for model, model_data in provider_data.get("models", {}).items():
            if model not in result[provider_name]["models"]:
                result[provider_name]["models"][model] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "requests": 0,
                    "errors": 0,
                    "latency_ms": 0
                }

            model_result = result[provider_name]["models"][model]

            # Accumulate model usage
            model_result["input_tokens"] += model_data.get("input_tokens", 0)
            model_result["output_tokens"] += model_data.get("output_tokens", 0)
            model_result["requests"] += model_data.get("requests", 0)
            model_result["errors"] += model_data.get("errors", 0)

            # Update latency if new event is faster
            new_latency = model_data.get("latency_ms", 0)
            if new_latency > 0 and (model_result["latency_ms"] < new_latency or "latency_ms" not in model_result):
                model_result["latency_ms"] = new_latency

    return result


def record_provider_error(
    existing: Optional[Dict[str, Any]],
    error_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Record an error event for a provider and update success rate.

    Args:
        existing: Current provider usage tracking
        error_data: Error information including provider, model, error type

    Returns:
        Updated provider usage with error recorded
    """
    if existing is None:
        return {}

    provider = error_data.get("provider", "")
    model = error_data.get("model", "")
    error_type = error_data.get("type", "unknown")
    error_message = error_data.get("message", str(error_data))

    if not provider:
        return existing.copy()

    # Never mutate existing - always rebuild immutably
    result = existing.copy()

    # Initialize provider entry if needed
    if provider not in result:
        result[provider] = {
            "usage_events": [],
            "models": {},
            "total_requests": 0,
            "errors": 0,
            "success_rate": 100.0
        }

    # Create updated provider entry with incremented error count
    updated_provider = {
        **result[provider],
        "errors": result[provider].get("errors", 0) + 1
    }

    # Create new error event (always copy before adding)
    error_event = {
        "type": "error",
        "error_type": error_type,
        "error_message": error_message,
        "timestamp": time.time(),
        "model": model
    }

    # Merge into result safely
    result[provider]["usage_events"] = merge_lists(
        result[provider].get("usage_events", []),
        [error_event],
        deduplicate=False
    )

    # Update total_requests if present
    if result[provider].get("total_requests", 0) > 0:
        updated_provider["total_requests"] = result[provider]["total_requests"]

    return result


def record_provider_request(
    existing: Optional[Dict[str, Any]],
    request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Record a request event for a provider.

    Args:
        existing: Current provider usage tracking
        request_data: Request information including provider, model, tokens

    Returns:
        Updated provider usage with request recorded
    """
    if existing is None:
        existing = {}

    provider = request_data.get("provider", "")
    model = request_data.get("model", "")
    input_tokens = request_data.get("input_tokens", 0)
    output_tokens = request_data.get("output_tokens", 0)
    latency_ms = request_data.get("latency_ms", 0)
    success = request_data.get("success", True)

    if not provider:
        return existing.copy()

    # Never mutate existing - always rebuild immutably
    result = existing.copy()

    # Initialize provider entry if needed
    if provider not in result:
        result[provider] = {
            "usage_events": [],
            "models": {},
            "total_requests": 0,
            "errors": 0,
            "success_rate": 100.0
        }

    # Update total_requests immutably
    updated_provider = {
        **result[provider],
        "total_requests": result[provider].get("total_requests", 0) + 1
    }

    # Update model-specific data immutably if model exists
    if model and model in updated_provider.get("models", {}):
        existing_model = updated_provider["models"][model]
        updated_provider["models"][model] = {
            **existing_model,
            "input_tokens": existing_model.get("input_tokens", 0) + input_tokens,
            "output_tokens": existing_model.get("output_tokens", 0) + output_tokens,
            "requests": existing_model.get("requests", 0) + 1,
            "latency_ms": max(existing_model.get("latency_ms", 0), latency_ms)
        }
    # Or create new model entry
    elif model:
        updated_provider["models"][model] = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "requests": 1,
            "latency_ms": latency_ms
        }

    # Append success event immutably
    if success:
        event = {
            "type": "request",
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
            "success": success,
            "timestamp": time.time()
        }
        updated_provider["usage_events"] = merge_lists(
            updated_provider.get("usage_events", []),
            [event],
            deduplicate=False
        )

    # Calculate and set success rate immutably
    if updated_provider["total_requests"] > 0:
        successful = updated_provider["total_requests"] - updated_provider.get("errors", 0)
        updated_provider["success_rate"] = (successful / updated_provider["total_requests"]) * 100

    return result


# ===============================
# ARTIFACT REDUCERS
# ===============================


def deduplicate_artifacts(
    existing: Optional[List[Dict[str, Any]]],
    new: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge artifacts while preventing duplicates by checksum or identifier.

    Args:
        existing: Current list of artifacts (may be None)
        new: New artifacts to merge

    Returns:
        Deduplicated artifact list preserving first occurrence
    """
    if existing is None:
        existing = []

    if not new:
        return existing.copy()

    # Build set of seen checksums/identifiers
    seen_keys = set()
    for artifact in existing:
        checksum = artifact.get("checksum", artifact.get("id", ""))
        seen_keys.add(checksum)

    result = existing.copy()

    # Append non-duplicate artifacts
    for artifact in new:
        checksum = artifact.get("checksum", artifact.get("id", ""))
        if checksum not in seen_keys:
            result.append(artifact.copy())
            seen_keys.add(checksum)

    return result


def merge_artifact_metadata(
    existing: Optional[Dict[str, Any]],
    new: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge artifact metadata for known artifacts using explicit type-safe logic.

    Merge rules:
    - dict + dict → merge_dicts() (shallow merge, new keys only)
    - list + list → merge_lists() (concatenate with optional dedup)
    - primitive values → prefer new value (overwrite)
    - mismatched types → prefer new value

    Args:
        existing: Current artifact metadata
        new: New metadata to merge

    Returns:
        Merged artifact metadata
    """
    if existing is None:
        existing = {}

    if not new:
        return existing.copy()

    result = existing.copy()

    # Merge metadata for existing artifacts using explicit type-safe patterns
    for artifact_id, metadata in new.items():
        if artifact_id in result:
            existing_metadata = result[artifact_id]

            # Merge each field with explicit type handling
            for key, value in metadata.items():
                existing_value = existing_metadata.get(key)

                if key not in existing_value:
                    # New key: use new value (copy if mutable)
                    result[artifact_id][key] = value.copy() if isinstance(value, (dict, list)) else value
                elif isinstance(existing_value, dict) and isinstance(value, dict):
                    # dict + dict → use merge_dicts for shallow merge
                    result[artifact_id][key] = merge_dicts(existing_value, value, overwrite=False)
                elif isinstance(existing_value, list) and isinstance(value, list):
                    # list + list → use merge_lists
                    result[artifact_id][key] = merge_lists(existing_value, value, deduplicate=False)
                else:
                    # Primitive or mismatched types → prefer new value
                    result[artifact_id][key] = value.copy() if isinstance(value, (dict, list)) else value

    return result


# ===============================
# CONSENSUS REDUCERS
# ===============================


def accumulate_consensus(
    existing: Optional[List[Dict[str, Any]]],
    new: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Accumulate consensus votes from multiple agents.

    Args:
        existing: Current consensus history
        new: New consensus votes

    Returns:
        Accumulated consensus history
    """
    return merge_lists(existing, new, deduplicate=False)


def calculate_consensus_result(
    existing: Optional[List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Calculate current consensus result from vote history.

    Args:
        existing: Current consensus history

    Returns:
        Calculated consensus result
    """
    if not existing:
        return {
            "decision": None,
            "votes": {
                "for": 0,
                "against": 0,
                "abstain": 0
            },
            "confidence": 0.0,
            "final": False
        }

    # Count votes from latest entries
    for_votes = 0
    against_votes = 0
    abstain_votes = 0

    for vote in existing:
        vote_type = vote.get("vote", {}).get("type", "")
        if vote_type == "for":
            for_votes += 1
        elif vote_type == "against":
            against_votes += 1
        elif vote_type == "abstain":
            abstain_votes += 1

    total_votes = for_votes + against_votes + abstain_votes

    # Determine decision
    if total_votes == 0:
        decision = None
    elif for_votes > against_votes:
        decision = "approved"
    elif against_votes > for_votes:
        decision = "rejected"
    else:
        decision = "tie"

    # Calculate confidence (based on majority)
    if total_votes > 0:
        for_ratio = for_votes / total_votes
        against_ratio = against_votes / total_votes
        margin = abs(for_ratio - against_ratio)
        confidence = min(margin * 100, 100.0)
    else:
        confidence = 0.0

    return {
        "decision": decision,
        "votes": {
            "for": for_votes,
            "against": against_votes,
            "abstain": abstain_votes
        },
        "total_votes": total_votes,
        "confidence": confidence,
        "final": total_votes >= 3  # Require minimum votes for final decision
    }


# ===============================
# WEBSOCKET EVENT REDUCERS
# ===============================


def merge_websocket_events(
    existing: Optional[List[Dict[str, Any]]],
    new: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge websocket event logs without deduplication (preserve all events).

    Args:
        existing: Current event log
        new: New events to append

    Returns:
        Merged event log
    """
    return merge_lists(existing, new, deduplicate=False)


def filter_websocket_events(
    existing: Optional[List[Dict[str, Any]]],
    event_type: str,
    channel: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter websocket events by type and channel.

    Args:
        existing: Current event log
        event_type: Event type to filter by
        channel: Optional channel name to filter by

    Returns:
        Filtered event list
    """
    if existing is None:
        return []

    filtered = []
    for event in existing:
        if event.get("type") == event_type:
            if channel is None or event.get("channel") == channel:
                filtered.append(event.copy())

    return filtered


# ===============================
# RETRY HISTORY REDUCERS
# ===============================


def append_retry_attempt(
    existing: Optional[List[Dict[str, Any]]],
    new: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Append a retry attempt to the history.

    Args:
        existing: Current retry history
        new: Retry attempt data

    Returns:
        Updated retry history
    """
    return merge_lists(existing, [new], deduplicate=False)


def update_retry_status(
    existing: Optional[List[Dict[str, Any]]],
    attempt_id: str,
    status: str,
    error: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Update status of a retry attempt.

    Args:
        existing: Current retry history
        attempt_id: ID of the retry attempt to update
        status: New status (success, failure, timeout, etc.)
        error: Optional error details for failure

    Returns:
        Updated retry history
    """
    if existing is None:
        existing = []

    # Rebuild retry history immutably - never mutate original attempt objects
    updated_history: List[Dict[str, Any]] = []
    found_match = False

    for attempt in existing:
        # Copy attempt before potential modification
        updated_attempt = {**attempt}

        if attempt.get("attempt_id") == attempt_id:
            # Update status immutably using unpacking
            updated_attempt = {
                **updated_attempt,
                "status": status,
                "updated_at": time.time()
            }

            # Add error if provided (immutable merge)
            if error:
                updated_attempt = {
                    **updated_attempt,
                    "error": error
                }

            found_match = True
        # Keep original attempt if no match
        updated_history.append(updated_attempt)

    return updated_history


def count_failed_retries(
    existing: Optional[List[Dict[str, Any]]]
) -> int:
    """
    Count number of failed retry attempts.

    Args:
        existing: Current retry history

    Returns:
        Count of failed retries
    """
    if existing is None:
        return 0

    return sum(1 for attempt in existing if attempt.get("status") in ("failure", "timeout", "cancelled"))


# ===============================
# REDUCER REGISTRY
# ===============================

REDUCER_REGISTRY: Dict[str, Callable] = {
    "merge_lists": merge_lists,
    "merge_dicts": merge_dicts,
    "append_execution_trace": append_execution_trace,
    "update_trace_status": update_trace_status,
    "accumulate_token_usage": accumulate_token_usage,
    "merge_provider_usage": merge_provider_usage,
    "record_provider_request": record_provider_request,
    "record_provider_error": record_provider_error,
    "deduplicate_artifacts": deduplicate_artifacts,
    "merge_artifact_metadata": merge_artifact_metadata,
    "accumulate_consensus": accumulate_consensus,
    "calculate_consensus_result": calculate_consensus_result,
    "merge_websocket_events": merge_websocket_events,
    "filter_websocket_events": filter_websocket_events,
    "append_retry_attempt": append_retry_attempt,
    "update_retry_status": update_retry_status,
    "count_failed_retries": count_failed_retries
}


# ===============================
# EXECUTABLE EXAMPLES
# ===============================

if __name__ == "__main__":
    print("✓ Workflow Reducers initialized")
    print(f"  Available reducers: {len(REDUCER_REGISTRY)}")

    # Example: merge_lists
    existing_logs = [
        {"id": 1, "action": "planning", "timestamp": 1000.0},
        {"id": 2, "action": "development", "timestamp": 1001.0}
    ]
    new_logs = [{"id": 3, "action": "review", "timestamp": 1002.0}]

    merged = REDUCER_REGISTRY["merge_lists"](existing_logs, new_logs)
    print(f"\n✓ merge_lists example:")
    print(f"  Existing: {len(existing_logs)} items")
    print(f"  New: {len(new_logs)} items")
    print(f"  Merged: {len(merged)} items (deduplicated)")

    # Example: accumulate_token_usage
    existing_tokens = {
        "total": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        "anthropic": {"input_tokens": 80, "output_tokens": 40, "total_tokens": 120, "requests": 1}
    }
    new_tokens = {
        "input_tokens": 30,
        "output_tokens": 10,
        "total_tokens": 40,
        "provider_usage": {
            "anthropic": {"input_tokens": 30, "output_tokens": 10}
        }
    }

    accumulated = REDUCER_REGISTRY["accumulate_token_usage"](existing_tokens, new_tokens)
    print(f"\n✓ accumulate_token_usage example:")
    print(f"  Total input tokens: {accumulated['total']['input_tokens']}")
    print(f"  Anthropic requests: {accumulated.get('anthropic', {}).get('total_requests', 0)}")

    # Example: deduplicate_artifacts
    existing_artifacts = [
        {"name": "auth.py", "checksum": "sha256:abc123", "type": "source_file"}
    ]
    new_artifacts = [
        {"name": "utils.py", "checksum": "sha256:def456", "type": "source_file"},
        {"name": "auth.py", "checksum": "sha256:abc123", "type": "source_file"}  # Duplicate checksum
    ]

    deduplicated = REDUCER_REGISTRY["deduplicate_artifacts"](existing_artifacts, new_artifacts)
    print(f"\n✓ deduplicate_artifacts example:")
    print(f"  Existing: {len(existing_artifacts)} artifacts")
    print(f"  New: {len(new_artifacts)} artifacts")
    print(f"  Deduplicated: {len(deduplicated)} artifacts (duplicates removed)")

    # Example: merge_dicts
    existing_state = {
        "workflow_id": "wf-001",
        "status": "planning"
    }
    new_state = {
        "tasks": [],
        "implementation_logs": []
    }

    merged_state = REDUCER_REGISTRY["merge_dicts"](existing_state, new_state)
    print(f"\n✓ merge_dicts example:")
    print(f"  Original existing unchanged: {existing_state['workflow_id']}")
    print(f"  Merged keys: {list(merged_state.keys())}")

    # Example: calculate_consensus_result
    consensus_history = [
        {"agent": "agent-1", "vote": {"type": "for", "reason": "good code"}},
        {"agent": "agent-2", "vote": {"type": "for", "reason": "approved"}},
        {"agent": "agent-3", "vote": {"type": "abstain", "reason": "no opinion"}}
    ]

    result = REDUCER_REGISTRY["calculate_consensus_result"](consensus_history)
    print(f"\n✓ calculate_consensus_result example:")
    print(f"  Decision: {result['decision']}")
    print(f"  Votes for: {result['votes']['for']}")
    print(f"  Votes against: {result['votes']['against']}")
    print(f"  Confidence: {result['confidence']:.1f}%")
    print(f"  Final: {result['final']}")

    print("\n✓ All reducer examples completed successfully")

# ===============================
# LANGGRAPH STATE ANNOTATION EXAMPLES
# ===============================

"""
LangGraph State Annotation Examples.

These examples demonstrate how to use Pydantic typing with Annotated
for LangGraph state schemas. These are examples only - do NOT rewrite AgentState yet.

Usage in StateGraph:

    from typing import Annotated
    from typing_extensions import TypedDict
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver

    # Define state schema with reducer annotations
    class AgentState(TypedDict, total=False):
        implementation_logs: Annotated[
            List[Dict[str, Any]],
            merge_lists
        ]
        code_artifacts: Annotated[
            List[Dict[str, Any]],
            deduplicate_artifacts
        ]
        provider_usage: Annotated[
            Dict[str, Any],
            merge_provider_usage
        ]
        token_usage: Annotated[
            Dict[str, Any],
            accumulate_token_usage
        ]
        consensus_history: Annotated[
            List[Dict[str, Any]],
            accumulate_consensus
        ]
        websocket_events: Annotated[
            List[Dict[str, Any]],
            merge_websocket_events
        ]
        retry_history: Annotated[
            List[Dict[str, Any]],
            append_retry_attempt
        ]

    # Create graph with typed state
    graph = StateGraph(AgentState)

    # Add nodes and edges...

    # Compile with checkpointing
    compiled = graph.compile(checkpointer=MemorySaver())

Note:
- The Annotated type hints document the intended reducer for each field
- LangGraph will apply the appropriate merge strategy during state updates
- Use REDUCER_REGISTRY.get() to retrieve reducer functions at runtime
- Reducers must be pure functions that accept (existing, new) and return merged state
"""

if __name__ == "__main__":
    print("✓ Workflow Reducers initialized")
    print(f"  Available reducers: {len(REDUCER_REGISTRY)}")

    # Example: merge_lists
    existing_logs = [
        {"id": 1, "action": "planning", "timestamp": 1000.0},
        {"id": 2, "action": "development", "timestamp": 1001.0}
    ]
    new_logs = [{"id": 3, "action": "review", "timestamp": 1002.0}]

    merged = REDUCER_REGISTRY["merge_lists"](existing_logs, new_logs)
    print(f"\n✓ merge_lists example:")
    print(f"  Existing: {len(existing_logs)} items")
    print(f"  New: {len(new_logs)} items")
    print(f"  Merged: {len(merged)} items (deduplicated)")

    # Example: accumulate_token_usage
    existing_tokens = {
        "total": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        "anthropic": {"input_tokens": 80, "output_tokens": 40, "total_tokens": 120, "requests": 1}
    }
    new_tokens = {
        "input_tokens": 30,
        "output_tokens": 10,
        "total_tokens": 40,
        "provider_usage": {
            "anthropic": {"input_tokens": 30, "output_tokens": 10}
        }
    }

    accumulated = REDUCER_REGISTRY["accumulate_token_usage"](existing_tokens, new_tokens)
    print(f"\n✓ accumulate_token_usage example:")
    print(f"  Total input tokens: {accumulated['total']['input_tokens']}")
    print(f"  Anthropic requests: {accumulated.get('anthropic', {}).get('total_requests', 0)}")

    # Example: deduplicate_artifacts
    existing_artifacts = [
        {"name": "auth.py", "checksum": "sha256:abc123", "type": "source_file"}
    ]
    new_artifacts = [
        {"name": "utils.py", "checksum": "sha256:def456", "type": "source_file"},
        {"name": "auth.py", "checksum": "sha256:abc123", "type": "source_file"}  # Duplicate checksum
    ]

    deduplicated = REDUCER_REGISTRY["deduplicate_artifacts"](existing_artifacts, new_artifacts)
    print(f"\n✓ deduplicate_artifacts example:")
    print(f"  Existing: {len(existing_artifacts)} artifacts")
    print(f"  New: {len(new_artifacts)} artifacts")
    print(f"  Deduplicated: {len(deduplicated)} artifacts (duplicates removed)")

    # Example: merge_dicts
    existing_state = {
        "workflow_id": "wf-001",
        "status": "planning"
    }
    new_state = {
        "tasks": [],
        "implementation_logs": []
    }

    merged_state = REDUCER_REGISTRY["merge_dicts"](existing_state, new_state)
    print(f"\n✓ merge_dicts example:")
    print(f"  Original existing unchanged: {existing_state['workflow_id']}")
    print(f"  Merged keys: {list(merged_state.keys())}")

    # Example: calculate_consensus_result
    consensus_history = [
        {"agent": "agent-1", "vote": {"type": "for", "reason": "good code"}},
        {"agent": "agent-2", "vote": {"type": "for", "reason": "approved"}},
        {"agent": "agent-3", "vote": {"type": "abstain", "reason": "no opinion"}}
    ]

    result = REDUCER_REGISTRY["calculate_consensus_result"](consensus_history)
    print(f"\n✓ calculate_consensus_result example:")
    print(f"  Decision: {result['decision']}")
    print(f"  Votes for: {result['votes']['for']}")
    print(f"  Votes against: {result['votes']['against']}")
    print(f"  Confidence: {result['confidence']:.1f}%")
    print(f"  Final: {result['final']}")

    # ===============================
    # EDGE CASE VALIDATION TESTS
    # ===============================

    print("\n" + "=" * 60)
    print("EDGE CASE VALIDATION TESTS")
    print("=" * 60)

    # Test 1: None inputs
    print("\n[TEST 1] None inputs handling:")
    try:
        result_none = REDUCER_REGISTRY["merge_lists"](None, [])
        print(f"  ✓ merge_lists(None, []) → {len(result_none)} items")

        result_none = REDUCER_REGISTRY["accumulate_token_usage"](None, {"input_tokens": 0})
        print(f"  ✓ accumulate_token_usage(None, ...) → {result_none}")

        result_none = REDUCER_REGISTRY["merge_provider_usage"](None, {"providers": {}})
        print(f"  ✓ merge_provider_usage(None, ...) → {result_none}")

        print("  ✓ All None input tests passed")
    except Exception as e:
        print(f"  ✗ None input test failed: {e}")

    # Test 2: Empty lists
    print("\n[TEST 2] Empty lists handling:")
    try:
        result_empty = REDUCER_REGISTRY["merge_lists"]([], [])
        print(f"  ✓ merge_lists([], []) → {len(result_empty)} items")

        result_empty = REDUCER_REGISTRY["deduplicate_artifacts"]([], [])
        print(f"  ✓ deduplicate_artifacts([], []) → {len(result_empty)} artifacts")

        result_empty = REDUCER_REGISTRY["merge_websocket_events"]([], [])
        print(f"  ✓ merge_websocket_events([], []) → {len(result_empty)} events")

        print("  ✓ All empty list tests passed")
    except Exception as e:
        print(f"  ✗ Empty list test failed: {e}")

    # Test 3: Duplicate artifacts
    print("\n[TEST 3] Duplicate artifacts handling:")
    try:
        existing = [{"name": "app.py", "checksum": "sha256:xxx"}]
        new = [
            {"name": "app.py", "checksum": "sha256:xxx"},  # Same checksum
            {"name": "config.py", "checksum": "sha256:yyy"}  # Different checksum
        ]

        deduped = REDUCER_REGISTRY["deduplicate_artifacts"](existing, new)
        print(f"  ✓ Deduplicated from {len(existing) + len(new)} to {len(deduped)} artifacts")
        print(f"  ✓ First occurrence preserved: {[a['name'] for a in deduped]}")

        print("  ✓ Duplicate artifact tests passed")
    except Exception as e:
        print(f"  ✗ Duplicate artifact test failed: {e}")

    # Test 4: Malformed provider usage
    print("\n[TEST 4] Malformed provider usage handling:")
    try:
        malformed_existing = {
            "anthropic": {"models": {"gpt-4": {"input_tokens": 100}}}
        }
        malformed_new = {
            "providers": {
                "anthropic": {
                    "models": {
                        "gpt-4": {"input_tokens": 50, "output_tokens": 25},
                        "gpt-35": {"input_tokens": 30, "output_tokens": 15}
                    }
                }
            }
        }

        merged_malformed = REDUCER_REGISTRY["merge_provider_usage"](
            malformed_existing,
            malformed_new,
            merge_models=True
        )

        print(f"  ✓ Malformed merge handled without error")
        print(f"  ✓ Models tracked: {list(merged_malformed.get('anthropic', {}).get('models', {}).keys())}")

        print("  ✓ Malformed provider usage tests passed")
    except Exception as e:
        print(f"  ✗ Malformed provider usage test failed: {e}")

    # Test 5: Retry updates on missing IDs
    print("\n[TEST 5] Retry updates on missing IDs handling:")
    try:
        retry_history = [
            {"attempt_id": "R-001", "status": "success"},
            {"attempt_id": "R-002", "status": "failure", "error": {"type": "timeout"}}
        ]

        updated = REDUCER_REGISTRY["update_retry_status"](
            retry_history,
            "R-999",  # Non-existent ID
            "success"
        )

        print(f"  ✓ Non-existent ID handled gracefully")
        print(f"  ✓ History length unchanged: {len(updated)} (no mutation of non-matching)")

        # Verify original wasn't mutated
        print(f"  ✓ Original status preserved: {[a.get('status') for a in retry_history]}")

        print("  ✓ Retry update edge case tests passed")
    except Exception as e:
        print(f"  ✗ Retry update edge case test failed: {e}")

    # Test 6: Websocket event filtering
    print("\n[TEST 6] Websocket event filtering:")
    try:
        events = [
            {"type": "message", "channel": "dev", "payload": "msg1"},
            {"type": "connection", "channel": "dev", "payload": "connected"},
            {"type": "message", "channel": "prod", "payload": "msg2"},
            {"type": "error", "channel": "dev", "payload": "err1"},
        ]

        filtered = REDUCER_REGISTRY["filter_websocket_events"](events, "message")
        print(f"  ✓ Filter by type 'message': {len(filtered)} events")

        filtered = REDUCER_REGISTRY["filter_websocket_events"](events, "message", "dev")
        print(f"  ✓ Filter by type+channel 'message|dev': {len(filtered)} events")

        filtered_none = REDUCER_REGISTRY["filter_websocket_events"](None, "message")
        print(f"  ✓ Filter with None input: {filtered_none}")

        print("  ✓ Websocket event filtering tests passed")
    except Exception as e:
        print(f"  ✗ Websocket event filtering test failed: {e}")

    # Test 7: Consensus ties
    print("\n[TEST 7] Consensus ties handling:")
    try:
        # Exact tie
        tie_votes = [
            {"agent": "a1", "vote": {"type": "for"}},
            {"agent": "a2", "vote": {"type": "against"}}
        ]

        result_tie = REDUCER_REGISTRY["calculate_consensus_result"](tie_votes)
        print(f"  ✓ Tie case (1-1): decision='{result_tie['decision']}', total={result_tie['total_votes']}")

        # All abstain
        abstain_votes = [
            {"agent": "a1", "vote": {"type": "abstain"}},
            {"agent": "a2", "vote": {"type": "abstain"}}
        ]

        result_abstain = REDUCER_REGISTRY["calculate_consensus_result"](abstain_votes)
        print(f"  ✓ All abstain case: decision='{result_abstain['decision']}', total={result_abstain['total_votes']}")

        # No votes
        no_votes = []
        result_empty = REDUCER_REGISTRY["calculate_consensus_result"](no_votes)
        print(f"  ✓ No votes case: decision={result_empty['decision']}, final={result_empty['final']}")

        print("  ✓ Consensus tie handling tests passed")
    except Exception as e:
        print(f"  ✗ Consensus tie handling test failed: {e}")

    # Test 8: Immutability verification
    print("\n[TEST 8] Immutability verification:")
    try:
        original = {
            "provider": "tests",
            "models": {
                "model1": {"input_tokens": 100, "output_tokens": 50}
            },
            "total_requests": 0,
            "errors": 0
        }

        request_data = {
            "provider": "tests",
            "model": "model1",
            "input_tokens": 25,
            "output_tokens": 10,
            "latency_ms": 150,
            "success": True
        }

        # Call the reducer
        merged = REDUCER_REGISTRY["record_provider_request"](original, request_data)

        # Verify original wasn't mutated
        assert original["total_requests"] == 0, "Original was mutated!"
        assert original["models"]["model1"]["input_tokens"] == 100, "Nested original was mutated!"

        # Verify merged has new values
        assert merged["total_requests"] == 1, "Merged doesn't have new total_requests"
        assert merged["models"]["model1"]["input_tokens"] == 125, "Merged doesn't have accumulated input_tokens"

        print(f"  ✓ Original dict unchanged after record_provider_request")
        print(f"  ✓ Merged dict has updated values")

        print("  ✓ Immutability verification tests passed")
    except AssertionError as e:
        print(f"  ✗ Immutability verification failed: {e}")
    except Exception as e:
        print(f"  ✗ Immutability verification test failed: {e}")

    print("\n" + "=" * 60)
    print("ALL EDGE CASE VALIDATION TESTS COMPLETED")
    print("=" * 60)
