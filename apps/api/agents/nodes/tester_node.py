import json
import logging
from typing import Any

from agents.sanitize import wrap_context, wrap_task
from agents.state import AgentState
from agents.utils import _is_timeout, call_with_timeout, load_prompt_template
from app.services.test_executor import TestExecutor, TestFramework, TestResult, TestResultStatus
from core.config import settings
from core.providers import get_provider, get_provider_for_user
from models.agent_outputs import Finding, ReviewOutput, Severity, Verdict

logger = logging.getLogger(__name__)

# Initialize test executor
test_executor = TestExecutor()


def _test_result_to_review_output(test_result: TestResult, summary: str = "") -> str:
    """Convert TestResult to ReviewOutput JSON string."""
    # Determine verdict based on test results
    if test_result.status == TestResultStatus.PASSED and test_result.failed == 0:
        verdict = Verdict.passed
    elif test_result.status == TestResultStatus.FAILED or test_result.failed > 0:
        verdict = Verdict.failed
    else:
        # Error, timeout, or other issues
        verdict = Verdict.review_needed

    # Create findings from test failures/errors
    findings = []
    if test_result.failed > 0:
        findings.append({
            "title": f"{test_result.failed} test(s) failed",
            "detail": f"See test output for details. Passed: {test_result.passed}, Failed: {test_result.failed}, Skipped: {test_result.skipped}",
            "severity": "high"
        })

    if test_result.status == TestResultStatus.ERROR:
        findings.append({
            "title": "Test execution error",
            "detail": test_result.stderr[:500] if test_result.stderr else "Unknown error",
            "severity": "high"
        })
    elif test_result.status == TestResultStatus.TIMEOUT:
        findings.append({
            "title": "Test execution timed out",
            "detail": f"Tests exceeded {test_executor.timeout_seconds} second limit",
            "severity": "high"
        })

    # Add summary if not provided
    if not summary:
        summary = f"Tests executed: {test_result.passed} passed, {test_result.failed} failed, {test_result.skipped} skipped. Status: {test_result.status.value}"

    # Create ReviewOutput
    # Convert dict findings to Finding objects
    finding_objects = []
    for f in findings:
        finding_objects.append(Finding(
            title=f["title"],
            detail=f["detail"],
            severity=Severity(f["severity"])
        ))

    review_output = ReviewOutput(
        verdict=verdict,
        summary=summary,
        findings=finding_objects
    )

    return review_output.model_dump_json()


async def tester_node(state: AgentState) -> dict[str, Any]:
    logger.info("Tester phase")

    # Get user and project context from state (with fallbacks)
    user_id = state.get("user_id", "00000000-0000-0000-0000-000000000001")
    project_id = state.get("project_id")
    db = state.get("db")  # Database session would be passed in state in a real implementation

    # Check if tester is configured
    if "tester" not in state["team_config"]:
        logger.info("No tester configured — skipping")
        # Return a passing test result when no tester configured
        empty_result = ReviewOutput(
            verdict=Verdict.passed,
            summary="No tester agent configured",
            findings=[]
        )
        return {"tester_output": empty_result.model_dump_json()}

    # Get the model for the tester
    model = state["team_config"]["tester"]["model"]

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

    timeout_s = settings.agent_timeout.get("tester", 20)
    max_tokens = settings.max_output_tokens if settings.fast_demo_mode else None

    env = load_prompt_template("tester.jinja2")
    template = env.get_template("tester.jinja2")
    system_prompt = template.render(
        task=wrap_task(state["task"]["description"]),
        plan=state.get("plan", "No plan"),
        builder_output=state.get("builder_output", "No output"),
        repository_context=wrap_context(state.get("repository_context", "")),
    )

    result = await call_with_timeout(
        provider, model, system_prompt, wrap_task(state["task"]["description"]),
        timeout_s=timeout_s, max_tokens=max_tokens,
    )

    is_timed_out = _is_timeout(result)
    if is_timed_out:
        timed_out = state.get("timed_out_agents", [])
        timed_out.append("tester")
        # Return a timeout result
        timeout_result = ReviewOutput(
            verdict=Verdict.review_needed,
            summary="Timed out - test generation incomplete",
            findings=[Finding(
                title="Test generation timed out",
                detail=f"Test generation exceeded {timeout_s} second limit",
                severity=Severity.medium
            )]
        )
        return {"tester_output": timeout_result.model_dump_json(), "timed_out_agents": timed_out}

    logger.info("Tester complete - attempting to execute generated tests")

    # Parse the tester output to get test files
    try:
        tester_output = result.content.strip()
        # Extract JSON from response (handle potential extra text)
        if tester_output.startswith("{"):
            test_json_str = tester_output
        else:
            # Try to find JSON in the response
            start_idx = tester_output.find("{")
            end_idx = tester_output.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                test_json_str = tester_output[start_idx:end_idx]
            else:
                raise ValueError("No JSON found in tester output")

        test_data = json.loads(test_json_str)

        # Extract test files - handle missing or null fields safely
        test_files_raw = test_data.get("files")
        if not isinstance(test_files_raw, list):
            test_files = []
        else:
            # Filter out non-dict items and None values
            test_files = [f for f in test_files_raw if isinstance(f, dict)]

        generation_summary = test_data.get("summary", "Generated tests")
        if not isinstance(generation_summary, str):
            generation_summary = str(generation_summary)

        if not test_files:
            logger.warning("No test files generated by tester")
            # Return the generation result as-is (let reviewer judge test quality)
            gen_result = ReviewOutput(
                verdict=Verdict.review_needed,  # Need review to see if tests are good
                summary=generation_summary,
                findings=[]
            )
            return {"tester_output": gen_result.model_dump_json()}

        # Extract source files from builder output
        source_files = {}
        builder_output = state.get("builder_output")
        if isinstance(builder_output, str) and builder_output.strip():
            try:
                builder_data = json.loads(builder_output)
                if isinstance(builder_data, dict):
                    builder_files_raw = builder_data.get("files")
                    if isinstance(builder_files_raw, list):
                        for file_change in builder_files_raw:
                            if isinstance(file_change, dict):
                                file_path = file_change.get("path")
                                content = file_change.get("content")
                                if isinstance(file_path, str) and isinstance(content, str):
                                    source_files[file_path] = content
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Could not parse builder output for source files: {e}")

        # Prepare test files for execution
        test_file_contents = {}
        for test_file in test_files:
            if not isinstance(test_file, dict):
                continue
            file_path = test_file.get("file_path")
            content = test_file.get("content")
            if isinstance(file_path, str) and isinstance(content, str) and file_path and content:
                test_file_contents[file_path] = content

        # Determine language from file extensions
        language = "python"  # default
        if test_file_contents:
            first_file = list(test_file_contents.keys())[0]
            if isinstance(first_file, str) and first_file.endswith(('.js', '.ts', '.jsx', '.tsx')):
                language = "javascript"

        framework = TestFramework.VITEST if language == "javascript" else TestFramework.PYTEST

        # Execute tests
        test_result = await test_executor.execute_tests(
            source_files=source_files,
            test_files=test_file_contents,
            framework=framework
        )

        # Convert test result to review output format
        test_output_summary = f"{generation_summary}. Tests executed."
        if test_result.stdout:
            # Take first line or so of stdout for summary
            stdout_lines = test_result.stdout.strip().split('\n')
            if stdout_lines and isinstance(stdout_lines[0], str):
                test_output_summary += f" {stdout_lines[0][:100]}"

        review_json = _test_result_to_review_output(
            test_result,
            test_output_summary
        )

        logger.info(f"Test execution completed: {test_result.status.value} - {test_result.passed} passed, {test_result.failed} failed")
        return {"tester_output": review_json}

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse tester output: {e}")
        logger.error(f"Tester output was: {result.content}")
        # Return error result
        error_result = ReviewOutput(
            verdict=Verdict.review_needed,
            summary=f"Test generation failed: {str(e)[:100]}",
            findings=[Finding(
                title="Test generation parsing error",
                detail=f"Could not parse test generator output: {str(e)[:200]}",
                severity=Severity.medium
            )]
        )
        return {"tester_output": error_result.model_dump_json()}
    except Exception as e:
        logger.error(f"Error in tester node: {e}")
        # Return error result
        error_result = ReviewOutput(
            verdict=Verdict.review_needed,
            summary=f"Test execution error: {str(e)[:100]}",
            findings=[Finding(
                title="Test execution error",
                detail=f"Unexpected error during testing: {str(e)[:200]}",
                severity=Severity.high
            )]
        )
        return {"tester_output": error_result.model_dump_json()}
