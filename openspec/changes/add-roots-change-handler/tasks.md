## 1. Implementation
- [ ] 1.1 Register `roots/list_changed` notification handler on MCP server
- [ ] 1.2 Implement handler: re-extract roots from MCP session context
- [ ] 1.3 Compare new roots against current `session.roots`
- [ ] 1.4 If project name changed, call `session.switch_project(new_name)`
- [ ] 1.5 Update `session.roots` with new roots list
- [ ] 1.6 Invalidate template context cache on roots change
- [ ] 1.7 Add tests for roots change detection and project switching
- [ ] 1.8 Add test for no-op when roots unchanged
