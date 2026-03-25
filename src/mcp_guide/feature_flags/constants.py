"""Feature flag name constants."""

# Client context flags
FLAG_ALLOW_CLIENT_INFO = "allow-client-info"
FLAG_OPENSPEC = "openspec"

# Workflow flags
FLAG_WORKFLOW = "workflow"
FLAG_WORKFLOW_FILE = "workflow-file"
FLAG_WORKFLOW_CONSENT = "workflow-consent"

# Content format flags
FLAG_CONTENT_FORMAT = "content-format"
FLAG_CONTENT_STYLE = "content-style"
FLAG_CONTENT_ACCESSOR = "content-accessor"

# Startup flags
FLAG_STARTUP_INSTRUCTION = "startup-instruction"

# Path flags
FLAG_PATH_DOCUMENTS = "path-documents"
FLAG_PATH_EXPORT = "path-export"

DEFAULT_EXPORT_DIR = ".knowledge/"

AGENT_KNOWLEDGE_DIRS: dict[str, str] = {
    "kiro": ".kiro/knowledge/",
    "q-dev": ".kiro/knowledge/",
    "claude": ".claude/knowledge/",
    "claude-code": ".claude/knowledge/",
    "cursor": ".cursor/knowledge/",
    "cursor-agent": ".cursor/knowledge/",
    "copilot": ".github/instructions/knowledge/",
    "gemini": ".gemini/knowledge/",
    "codex": ".codex/knowledge/",
    "goose": ".goose/skills/",
    "block-goose-cli": ".goose/skills/",
}

# Update flags
FLAG_AUTOUPDATE = "autoupdate"

# Development flags
FLAG_GUIDE_DEVELOPMENT = "guide-development"
