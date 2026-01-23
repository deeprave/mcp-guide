"""Constants for models."""

import re

# Default allowed filesystem paths for projects.
# These paths are relative to the project root and must have trailing slashes.
# Used by the filesystem interaction feature for security fencing.
# See: openspec/changes/agent-server-filesystem-interaction/specs/filesystem-interaction/spec.md
DEFAULT_ALLOWED_WRITE_PATHS: list[str] = [
    "openspec/",
    "memory/",
    "specs/",
    "templates/",
    "tasks/",
    "docs/",
    ".todo/",
    ".issues/",
]

# Name validation: Unicode alphanumeric, underscore, hyphen
NAME_PATTERN = r"^[\w-]+$"
_NAME_REGEX = re.compile(NAME_PATTERN, re.UNICODE)
