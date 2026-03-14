## 1. Standard and Template
- [x] 1.1 Update `src/mcp_guide/tools/README.md` — remove JSON Schema/Usage/Examples sections, revise to concise description standard (keep note about auto-generated Arguments)
- [x] 1.2 Update `tool-infrastructure` spec delta — clarify that manual JSON Schema is redundant, auto-generated Arguments section is kept

## 2. Remove redundant sections from verbose tools
- [x] 2.1 `tool_utility.py` — `client_info`: remove 40L hand-written JSON Schema + Usage + Examples, replace with ~3L concise description
- [x] 2.2 `tool_project.py` — `get_project`: remove 40L hand-written JSON Schema + Usage + Examples, replace with ~3L concise description
- [x] 2.3 `tool_content.py` — `get_content`: remove 55L hand-written JSON Schema + Usage + Examples, replace with ~3L concise description
- [x] 2.4 `tool_update.py` — `update_documents`: remove 28L hand-written JSON Schema + Usage + Examples, replace with ~3L concise description

## 3. Improve minimal tool descriptions
- [x] 3.1 `tool_category.py` — 5 category_collection_* tools (3-6L → ~4L each)
- [x] 3.2 `tool_feature_flags.py` — 4 flag tools (3-9L → ~4L each)
- [x] 3.3 `tool_filesystem.py` — 4 send_* tools (4L → ~3L each, clarify agent→server direction)
- [x] 3.4 `tool_project.py` — `list_profiles` (4L → ~3L, add context about filtering)

## 4. Optional: Polish adequate tools
- [x] 4.1 Review 10 adequate tools (8-12L) for consistency and clarity
