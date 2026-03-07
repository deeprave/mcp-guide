## 1. Default write paths
- [ ] 1.1 `constants.py` — add `.kiro/knowledge/` to `DEFAULT_ALLOWED_WRITE_PATHS`
- [ ] 1.2 `session.py` `_project_to_dict` — omit `allowed_write_paths` from serialized output when it equals `DEFAULT_ALLOWED_WRITE_PATHS`

## 2. export_content tool
- [ ] 2.1 Add `export_content` tool to `src/mcp_guide/tools/tool_content.py`
- [ ] 2.2 Args: `expression` (str), `pattern` (optional str), `path` (str), `force` (bool, default False)
- [ ] 2.3 Validate `path` against project `allowed_write_paths`; return error if not permitted
- [ ] 2.4 Resolve content using same logic as `get_content`
- [ ] 2.5 Return content with `instruction` field directing agent to write to `path` (create-only or forced overwrite based on `force`)

## 3. Tests
- [ ] 3.1 Unit test: `_project_to_dict` omits default `allowed_write_paths`
- [ ] 3.2 Integration tests for `export_content` — valid path, invalid path, force flag behaviour
