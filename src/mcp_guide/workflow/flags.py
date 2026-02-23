"""Workflow flag parsing and validation."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

from mcp_guide.core.result import Result
from mcp_guide.feature_flags.constants import (
    FLAG_STARTUP_INSTRUCTION,
    FLAG_WORKFLOW,
    FLAG_WORKFLOW_CONSENT,
    FLAG_WORKFLOW_FILE,
)
from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.feature_flags.validators import register_flag_validator
from mcp_guide.filesystem.read_write_security import ReadWriteSecurityPolicy, SecurityError
from mcp_guide.workflow.constants import (
    DEFAULT_WORKFLOW_PHASES,
    PHASE_CHECK,
    PHASE_DISCUSSION,
    PHASE_IMPLEMENTATION,
    PHASE_PLANNING,
    PHASE_REVIEW,
)

if TYPE_CHECKING:
    from mcp_guide.models.project import Project

# Valid phase names for validation
VALID_PHASES = {
    PHASE_DISCUSSION,
    PHASE_PLANNING,
    PHASE_IMPLEMENTATION,
    PHASE_CHECK,
    PHASE_REVIEW,
}


@dataclass
class WorkflowConfig:
    """Workflow configuration parsed from flags."""

    enabled: bool
    phases: list[str]


def validate_phase_name(phase: str) -> bool:
    """Validate that a phase name is valid.

    Args:
        phase: Phase name

    Returns:
        True if phase name is valid
    """
    return phase in VALID_PHASES


def substitute_variables(
    template: str,
    project_name: Optional[str] = None,
    project_key: Optional[str] = None,
    project_hash: Optional[str] = None,
) -> str:
    """Substitute variables in workflow flag values.

    Args:
        template: Template string with variables like {project-name}
        project_name: Project name for {project-name} substitution
        project_key: Project key for {project-key} substitution
        project_hash: Project hash for {project-hash} substitution

    Returns:
        String with variables substituted
    """
    result = template

    if project_name is not None:
        result = result.replace("{project-name}", project_name)

    if project_key is not None:
        result = result.replace("{project-key}", project_key)

    if project_hash is not None:
        result = result.replace("{project-hash}", project_hash)

    return result


def parse_workflow_phases(workflow_flag: Union[bool, list[str]]) -> WorkflowConfig:
    """Parse workflow flag into configuration.

    Args:
        workflow_flag: Boolean or list of phase names

    Returns:
        WorkflowConfig with enabled status and phases

    Raises:
        ValueError: If any phase name is invalid
    """
    if workflow_flag is False:
        return WorkflowConfig(enabled=False, phases=[])

    if workflow_flag is True:
        return WorkflowConfig(enabled=True, phases=DEFAULT_WORKFLOW_PHASES)

    # List of phases - validate each one
    validated_phases = []
    for phase in workflow_flag:
        if validate_phase_name(phase):
            validated_phases.append(phase)
        else:
            raise ValueError(f"Invalid phase name: '{phase}'. Valid phases are: {', '.join(sorted(VALID_PHASES))}")

    return WorkflowConfig(enabled=True, phases=validated_phases)


def validate_workflow_file_path(workflow_file: str, allowed_write_paths: list[str]) -> str:
    """Validate workflow file path against security policy.

    Args:
        workflow_file: Path to workflow state file
        allowed_write_paths: List of allowed write directories

    Returns:
        Validated path

    Raises:
        SecurityError: If path violates security policy
        ValueError: If allowed_write_paths is invalid
    """
    try:
        policy = ReadWriteSecurityPolicy(write_allowed_paths=allowed_write_paths)
        return policy.validate_write_path(workflow_file)
    except SecurityError:
        # Let security errors bubble up with their important messages
        raise
    except (TypeError, ValueError) as e:
        # ReadWriteSecurityPolicy constructor validation errors
        raise ValueError(f"workflow-file flag validation failed due to configuration error: {e}") from e


def _validate_workflow_flag(value: FeatureValue, is_project: bool) -> bool:
    """Validate workflow flag value with semantic checks."""
    if not isinstance(value, (bool, list)):
        return False

    if isinstance(value, bool):
        return True

    if isinstance(value, list):
        # All items must be strings and valid phase names (no markers allowed)
        for phase in value:
            if not isinstance(phase, str):
                return False
            # Reject phases with markers
            if phase.startswith("*") or phase.endswith("*"):
                return False
            # Must be valid phase name
            if not validate_phase_name(phase):
                return False

        # Discussion and implementation are mandatory
        if "discussion" not in value:
            return False
        if "implementation" not in value:
            return False

        return True

    return False


def _validate_workflow_file_flag(value: FeatureValue, is_project: bool) -> bool:
    """Validate workflow-file flag value."""
    if not isinstance(value, str) or not value.strip():
        return False

    # Basic validation - detailed security validation happens at use time
    # when we have access to project's allowed_write_paths
    return True


def _validate_workflow_consent_flag(value: FeatureValue, is_project: bool) -> bool:
    """Validate workflow-consent flag value."""
    if value is None:
        return True

    if isinstance(value, dict):
        # Validate structure: {phase: [consent_types]} or {phase: consent_type}
        for phase, consents in value.items():
            if not isinstance(phase, str):
                return False
            # Phase must be a valid phase name
            if not validate_phase_name(phase):
                return False

            # Normalize single string to list
            consent_list = [consents] if isinstance(consents, str) else consents

            if not isinstance(consent_list, list):
                return False
            # Each consent must be "entry" or "exit"
            if not all(c in ["entry", "exit"] for c in consent_list):
                return False
        return True

    return False


def parse_startup_expression(expr: str) -> tuple[list[str], list[str]]:
    """Parse startup expression into categories and collections.

    Args:
        expr: Expression like "docs,@guidelines,examples/README*"

    Returns:
        Tuple of (categories, collections)
    """
    if not expr or not expr.strip():
        return ([], [])

    categories = []
    collections = []

    for part in expr.split(","):
        part = part.strip()
        if not part:
            continue

        if part.startswith("@"):
            # Collection
            collections.append(part[1:])
        else:
            # Category (strip pattern if present)
            if "/" in part:
                part = part.split("/")[0]
            categories.append(part)

    return (categories, collections)


def validate_startup_expression(expr: str, project: "Project") -> Result[None]:
    """Validate startup expression against project.

    Args:
        expr: Expression to validate
        project: Project to validate against

    Returns:
        Result indicating success or error
    """
    if not expr or not expr.strip():
        return Result.ok(None)

    categories, collections = parse_startup_expression(expr)

    # Validate categories exist
    for cat in categories:
        if cat not in project.categories:
            return Result.failure(f"Category '{cat}' not found in project")

    # Validate collections exist
    for coll in collections:
        if coll not in project.collections:
            return Result.failure(f"Collection '{coll}' not found in project")

    return Result.ok(None)


def _validate_startup_instruction_flag(value: FeatureValue, is_project: bool) -> bool:
    """Validate startup-instruction flag value.

    Args:
        value: Flag value to validate
        is_project: Whether this is a project-level flag

    Returns:
        True if valid, False otherwise
    """
    # None or empty string is valid (flag not set)
    if value is None or value == "":
        return True

    # Must be a string
    if not isinstance(value, str):
        return False

    # Basic syntax check - will be validated against project when set
    # Just ensure it's not obviously malformed
    return bool(value.strip())


# Register validators at module import
register_flag_validator(FLAG_WORKFLOW, _validate_workflow_flag)
register_flag_validator(FLAG_WORKFLOW_FILE, _validate_workflow_file_flag)
register_flag_validator(FLAG_WORKFLOW_CONSENT, _validate_workflow_consent_flag)
register_flag_validator(FLAG_STARTUP_INSTRUCTION, _validate_startup_instruction_flag)
