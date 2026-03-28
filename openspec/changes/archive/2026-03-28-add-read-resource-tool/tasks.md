## 1. Prerequisites
- [x] 1.1 Add underscore prefix validation to `collection_add` in `tool_collection.py`
- [x] 1.2 Add underscore prefix validation to `collection_change` in `tool_collection.py`
- [x] 1.3 Add tests for collection underscore validation

## 2. URI Parser
- [x] 2.1 Create `src/mcp_guide/uri_parser.py` with `GuideUri` dataclass and `parse_guide_uri()` function
- [x] 2.2 Validate `guide://` scheme, reject all others
- [x] 2.3 Parse content URIs into expression and optional pattern
- [x] 2.4 Detect command URIs by underscore prefix, resolve command path via longest-match against command list
- [x] 2.5 Parse remaining path segments as positional args
- [x] 2.6 Parse query params as kwargs with boolean inference
- [x] 2.7 Add unit tests for URI parser (content URIs, command URIs, invalid schemes, edge cases)

## 3. Tool Implementation
- [x] 3.1 Create `src/mcp_guide/tools/tool_resource.py` with `ReadResourceArgs` and `read_resource` tool
- [x] 3.2 Route content URIs to `internal_get_content`
- [x] 3.3 Route command URIs to `handle_command`
- [x] 3.4 Register tool in `tools/__init__.py`
- [x] 3.5 Add integration tests for content and command URI routing, error handling
