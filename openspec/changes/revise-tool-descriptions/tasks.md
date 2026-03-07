## 1. Standard and Template
- [ ] 1.1 Update `src/mcp_guide/tools/README.md` — revise to concise description standard, remove JSON Schema section
- [ ] 1.2 Update `tool-infrastructure` spec delta

## 2. Remove verbose sections from compliant tools
- [ ] 2.1 `tool_project.py` — `get_project`: replace 40L verbose docstring with concise description
- [ ] 2.2 `tool_content.py` — `get_content`: replace 55L verbose docstring with concise description
- [ ] 2.3 `tool_update.py` — `update_documents`: replace 28L verbose docstring with concise description
- [ ] 2.4 `tool_utility.py` — `client_info`: replace 40L verbose docstring with concise description

## 3. Write concise descriptions for non-compliant tools
- [ ] 3.1 `tool_category.py` — all 7 tools
- [ ] 3.2 `tool_feature_flags.py` — all 4 tools
- [ ] 3.3 `tool_project.py` — remaining 9 tools (set_project, list_projects, list_project, clone_project, use_project_profile, list_profiles, show_profile, add_permission_path, remove_permission_path)
- [ ] 3.4 `tool_filesystem.py` — all 4 tools

## 4. Fix docstring placement
- [ ] 4.1 `tool_project.py` — move `list_profiles` docstring from `internal_list_profiles` to registered `list_profiles`
