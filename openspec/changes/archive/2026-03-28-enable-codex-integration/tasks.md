## 1. Prerequisites
- [x] 1.1 Add underscore prefix validation to `collection_add` in `tool_collection.py`
- [x] 1.2 Add underscore prefix validation to `collection_change` in `tool_collection.py`
- [x] 1.3 Add tests for collection underscore validation

## 2. URI Parsing
- [x] 2.1 Extend `GuideUri` dataclass to include command parsing fields
- [x] 2.2 Update `parse_guide_uri()` to detect underscore prefix in netloc
- [x] 2.3 Implement command path resolution using command cache from `discover_commands()`
- [x] 2.4 Parse remaining path segments as positional args
- [x] 2.5 Parse query params as kwargs with boolean inference
- [x] 2.6 Add tests for command URI parsing

## 3. Read Resource Tool Path
- [x] 3.1 Update `internal_read_resource()` to detect command URIs
- [x] 3.2 Route command URIs to `handle_command()`
- [x] 3.3 Pass parsed args and kwargs to the command handler
- [x] 3.4 Return command output as-is from the tool path
- [x] 3.5 Add error handling for invalid command execution in the tool path

## 4. MCP Resource Templates And Handlers
- [x] 4.1 Register second resource template `guide://_{command_path*}` for command URIs
- [x] 4.2 Update the MCP resource handler in `resources.py` to route command URIs through the same command execution flow as `internal_read_resource()`
- [x] 4.3 Preserve backward compatibility for content URIs served by `guide://{collection}/{document}`
- [x] 4.4 Add MCP resource-handler coverage for command execution failures

## 5. Integration Tests
- [x] 5.1 Test simple command URI parsing and `read_resource` handling: `guide://_project`
- [x] 5.2 Test command URIs with args and kwargs through the `read_resource` tool path
- [x] 5.3 Test backward compatibility for content URIs through parser and `read_resource`
- [x] 5.4 Add direct MCP resource-template coverage for `guide://_{command_path*}`
- [x] 5.5 Add direct MCP resource-handler tests for `guide://_project`
- [x] 5.6 Add direct MCP resource-handler tests for `guide://_category/add/docs`
- [x] 5.7 Add direct MCP resource-handler tests for `guide://_status?verbose=true`
- [x] 5.8 Add direct MCP resource-handler tests for invalid command errors

## 6. Documentation
- [x] 6.1 Confirm or update guide URI documentation with command URI examples
- [x] 6.2 Confirm or update user-facing docs to explain command resource discovery
- [x] 6.3 Update changelog if this change modifies advertised MCP capabilities
