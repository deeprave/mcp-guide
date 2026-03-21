# vulture whitelist — false-positive suppressions
# Referenced names are used by frameworks, protocols, or external callers.

# Pydantic
_.model_config  # BaseModel/BaseSettings config dict
_.validate_type_fields  # @model_validator on Pydantic models

# Type aliases (used in annotations)
_.YamlValue

# MCP async transport protocol interface
_.send
_.receive

# Event/timer system
_.is_timer_event
_.add_callback
_.unregister
_.cleanup_stopped
_.is_failure

# Registry / stats API (called by external consumers)
_.get_global_registry
_.get_stats
_.get_violation_count
_.get_content
_.get_dict
_.get_bool

# Logging level alias
_.TRACE

# Cache / session private attributes (set dynamically)
_._flag_checked
_._cached_content
_._cached_mtime
_._cached_context
_._instruction_id
_._version_this_session

# Syntax highlighting
_.pygments_available
_.highlighter

# CLI / prompt internals
_.raw_input
_.current_dir
_.MAX_PROMPT_ARGS
_.LazyPath
_.ParsedCommand
_.flags_list
_.from_value

# Workflow model fields
_.queued_at
_.cached_at
_.access_count
_.original_event_types

# Test-mode hooks (called from test fixtures)
_.enable_test_mode
_.disable_test_mode
_.clear_tool_registry
_.get_tool_registration
_.clear_prompt_registry
_.clear_resource_registry
_._reset_for_testing
_.send_found_files
_.set_filesystem_trust_mode
_.remove_current_session  # used in test teardown across many test files
_.initialize_task_manager  # registered as @mcp.on_init() callback, never called directly
_.plan  # Pydantic model field on WorkflowState; populated from .guide.yaml

# Document store public API (consumed by tool layer in subsequent issues)
_.add_document
_.get_document
_.get_document_content
_.remove_document
_.list_documents
_.created_at  # DocumentRecord dataclass field
_.updated_at  # DocumentRecord dataclass field
_.row_factory  # sqlite3.Connection attribute

# Discovery public API (consumed by content gathering in subsequent issues)
_.discover_documents
_.discover_document_stored
_.DocumentTask
# Module-level names
_.__all__
_.main
