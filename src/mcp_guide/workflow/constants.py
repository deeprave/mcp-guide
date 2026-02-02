"""Workflow constants."""

# Workflow phase names
PHASE_DISCUSSION = "discussion"
PHASE_PLANNING = "planning"
PHASE_IMPLEMENTATION = "implementation"
PHASE_CHECK = "check"
PHASE_REVIEW = "review"

# Default workflow file
DEFAULT_WORKFLOW_FILE = ".guide.yaml"

# Workflow directory name
WORKFLOW_DIR = "_workflow"

# Default workflow sequence
DEFAULT_WORKFLOW_PHASES = [
    PHASE_DISCUSSION,
    PHASE_PLANNING,
    PHASE_IMPLEMENTATION,
    PHASE_CHECK,
    PHASE_REVIEW,
]

# Default consent requirements
DEFAULT_WORKFLOW_CONSENT = {
    "implementation": ["entry"],
    "review": ["exit"],
}
