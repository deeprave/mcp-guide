"""Workflow flag parsing and validation."""

from dataclasses import dataclass
from typing import List, Optional, Union

from mcp_guide.filesystem.read_write_security import ReadWriteSecurityPolicy, SecurityError
from mcp_guide.workflow.constants import DEFAULT_WORKFLOW_PHASES, VALID_PHASES


@dataclass
class WorkflowConfig:
    """Workflow configuration parsed from flags."""

    enabled: bool
    phases: List[str]


def extract_phase_name(phase_with_markers: str) -> str:
    """Extract clean phase name from phase with transition markers.

    Args:
        phase_with_markers: Phase name possibly with * prefix/suffix

    Returns:
        Clean phase name without markers
    """
    return phase_with_markers.strip("*")


def validate_phase_name(phase: str) -> bool:
    """Validate that a phase name is valid.

    Args:
        phase: Phase name (with or without transition markers)

    Returns:
        True if phase name is valid
    """
    clean_phase = extract_phase_name(phase)
    return clean_phase in VALID_PHASES


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


def parse_workflow_phases(workflow_flag: Union[bool, List[str]]) -> WorkflowConfig:
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
            clean_phase = extract_phase_name(phase)
            raise ValueError(
                f"Invalid phase name: '{clean_phase}'. Valid phases are: {', '.join(sorted(VALID_PHASES))}"
            )

    return WorkflowConfig(enabled=True, phases=validated_phases)


def validate_workflow_file_path(workflow_file: str, allowed_write_paths: List[str]) -> str:
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
