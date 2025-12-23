"""Shared constants for tool modules."""

# Common error types
ERROR_NO_PROJECT = "no_project"
ERROR_NOT_FOUND = "not_found"
ERROR_INVALID_NAME = "invalid_name"
ERROR_SAVE = "save_error"
ERROR_FILE_READ = "file_read_error"
ERROR_SAFEGUARD = "safeguard_prevented"
ERROR_TEMPLATE = "template_error"
ERROR_FILE_ERROR = "file_error"

# Error instructions
INSTRUCTION_NOTFOUND_ERROR = "Present this error to the user and take no further action."
INSTRUCTION_PATTERN_ERROR = (
    "Present this error to the user so they can correct the pattern. Do NOT attempt corrective action."
)
INSTRUCTION_FILE_ERROR = (
    "Present this error to the user. The file may have been deleted, moved, or has permission issues."
)
INSTRUCTION_VALIDATION_ERROR = "Return error to user without attempting remediation"
INSTRUCTION_NO_PROJECT = "To fix: Call set_project with the basename of the current working directory."
INSTRUCTION_TEMPLATE_ERROR = "Check template syntax and available context variables"

# Display instructions
INSTRUCTION_DISPLAY_ONLY = "Display this information to the user."
