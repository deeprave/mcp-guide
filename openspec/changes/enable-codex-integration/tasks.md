## 1. Prerequisites
- [ ] 1.1 Add underscore prefix validation to `collection_add` in `tool_collection.py`
- [ ] 1.2 Add underscore prefix validation to `collection_change` in `tool_collection.py`
- [ ] 1.3 Add tests for collection underscore validation

## 2. URI Parsing
- [ ] 2.1 Extend `GuideUri` dataclass to include `is_command`, `command_path`, `args`, `kwargs` fields
- [ ] 2.2 Update `parse_guide_uri()` to detect underscore prefix in netloc
- [ ] 2.3 Implement command path resolution using command cache from `discover_commands()`
- [ ] 2.4 Parse remaining path segments as positional args
- [ ] 2.5 Parse query params as kwargs with boolean inference
- [ ] 2.6 Add tests for command URI parsing

## 3. Resource Handler
- [ ] 3.1 Register second resource template `guide://_{command}` for command URIs
- [ ] 3.2 Update `guide_resource()` to detect command URIs
- [ ] 3.3 Route command URIs to `handle_command()` from guide_prompt module
- [ ] 3.4 Pass parsed args and kwargs to command handler
- [ ] 3.5 Return command output as-is (no special formatting)
- [ ] 3.6 Add error handling for command execution failures

## 4. Integration Tests
- [ ] 4.1 Test simple command URI: `guide://_project`
- [ ] 4.2 Test command with args: `guide://_category/add/docs`
- [ ] 4.3 Test command with kwargs: `guide://_status?verbose=true`
- [ ] 4.4 Test command with both: `guide://_openspec/list?verbose=true`
- [ ] 4.5 Test backward compatibility: `guide://collection/document` still works
- [ ] 4.6 Test error cases: invalid command, missing args, etc.

## 5. Documentation
- [ ] 5.1 Update `guide-uri-scheme.md` with command URI examples
- [ ] 5.2 Add Codex CLI usage examples to README
- [ ] 5.3 Update CHANGELOG.md
