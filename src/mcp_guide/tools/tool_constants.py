"""Shared constants for tool modules."""

# Common error types
ERROR_NO_PROJECT = "no_project"
ERROR_NOT_FOUND = "not_found"
ERROR_SAVE = "save_error"
ERROR_NO_MATCHES = "no_matches"
ERROR_FILE_READ = "file_read_error"

# Error instructions
INSTRUCTION_NOTFOUND_ERROR = "Present this error to the user and take no further action."
INSTRUCTION_PATTERN_ERROR = (
    "Present this error to the user so they can correct the pattern. Do NOT attempt corrective action."
)
INSTRUCTION_FILE_ERROR = (
    "Present this error to the user. The file may have been deleted, moved, or has permission issues."
)
