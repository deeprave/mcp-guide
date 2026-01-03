"""Workflow constants."""

# Workflow phase names (without transition markers)
PHASE_DISCUSSION = "discussion"
PHASE_PLANNING = "planning"
PHASE_IMPLEMENTATION = "implementation"
PHASE_CHECK = "check"
PHASE_REVIEW = "review"

# Default workflow file
DEFAULT_WORKFLOW_FILE = ".guide.yaml"


# Helper functions for transition control markers
def require_entry_consent(phase: str) -> str:
    """Mark phase as requiring explicit consent to enter."""
    return f"*{phase}"


def require_exit_consent(phase: str) -> str:
    """Mark phase as requiring explicit consent to exit."""
    return f"{phase}*"


def require_both_consent(phase: str) -> str:
    """Mark phase as requiring explicit consent to enter and exit."""
    return f"*{phase}*"


# Default workflow sequence with transition controls
DEFAULT_WORKFLOW_PHASES = [
    PHASE_DISCUSSION,
    PHASE_PLANNING,
    require_entry_consent(PHASE_IMPLEMENTATION),
    require_exit_consent(PHASE_CHECK),
    require_exit_consent(PHASE_REVIEW),
]
