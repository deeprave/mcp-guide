## 1. Fix: Partial instruction applied when partial not rendered
- [x] 1.1 Wrap `processed_partials` dict in a tracking subclass that records which keys chevron actually accesses during rendering
- [x] 1.2 After rendering, only collect frontmatter from partials that were actually accessed
- [x] 1.3 Tests: partial instruction NOT applied when partial isn't in template body; IS applied when it is

## 2. Fix: Partial instruction fields not rendered as templates
- [x] 2.1 After loading partial content in `renderer.py`, render the partial's `instruction` and `description` fields through chevron with the current context
- [x] 2.2 Tests: `{{INSTRUCTION_AGENT_INSTRUCTIONS}}` and `{{tool_prefix}}` resolve correctly in partial instructions

## 3. Validation
- [x] 3.1 Status command displays correctly (not overridden by unused `_client-info` partial)
- [x] 3.2 Commands that DO use `{{>client-info}}` still get the instruction applied
- [x] 3.3 Full test suite passes
