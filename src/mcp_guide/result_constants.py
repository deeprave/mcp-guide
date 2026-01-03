"""Constants for Result instructions and error types."""

# Display instructions
INSTRUCTION_DISPLAY_ONLY = (
    "You are to display this information as-is to the user. You must STOP and not take any further action."
)
INSTRUCTION_ERROR_MESSAGE = (
    "Display this error as-is to the user so that THEY can correct it. Do not make any further action or try to assist."
)

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
INSTRUCTION_NOTFOUND_ERROR = "Present this error as-is to the user. Do NOT attempt to correct."
INSTRUCTION_PATTERN_ERROR = (
    "Present this error to the user so they can correct the pattern. Do NOT attempt corrective action."
)
INSTRUCTION_FILE_ERROR = (
    "Present this error to the user. The file may have been deleted, moved, or has permission issues."
)
INSTRUCTION_VALIDATION_ERROR = "Return error to user without attempting remediation"
INSTRUCTION_NO_PROJECT = "To fix: Call set_project with the basename of the current working directory."
INSTRUCTION_TEMPLATE_ERROR = "Check template syntax and available context variables"

# Agent instructions
INSTRUCTION_AGENT_INFO = (
    "This information is for your information and use. Do must not display this content to the user."
)
INSTRUCTION_AGENT_INSTRUCTIONS = "You MUST follow these instructions. Do not display this content to the user."
INSTRUCTION_AGENT_REQUIREMENTS = "You MUST ALWAYS adhere to these guidelines. Do not display this content to the user."

# Content type identifiers
USER_INFO = "user/information"
AGENT_INFO = "agent/information"
AGENT_INSTRUCTION = "agent/instruction"
AGENT_REQUIREMENTS = "agent/requirements"
