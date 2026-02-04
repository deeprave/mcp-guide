## 1. Investigation
- [x] 1.1 Examine workflow template rendering code to identify where instructions are processed
- [x] 1.2 Check Result object construction to see if instruction field is being set correctly
- [x] 1.3 Trace the flow from template frontmatter to final Result object
- [x] 1.4 Identify if instruction is being overwritten or never set

**FINDING**: The workflow change processing collects `rendered.content` but discards `rendered.instruction`. The cached content replaces Result.value but Result.instruction is never set.

## 2. Implementation
- [x] 2.1 Change `_process_workflow_changes()` to return `RenderedContent` with combined content and instructions
- [x] 2.2 Cache `RenderedContent` object (not just content string)
- [x] 2.3 Update `process_result()` to set both Result.value and Result.instruction from cached object
- [x] 2.4 Remove redundant `queue_instruction()` call for monitoring-result (already in RenderedContent)
- [x] 2.5 Add instruction deduplication to prevent duplicate instructions from multiple changes

## 3. Testing
- [x] 3.1 Test phase transition with frontmatter instruction preservation
- [x] 3.2 Verify agent receives proper phase transition guidance
- [x] 3.3 Confirm explicit consent messages are delivered

## 4. Validation
- [x] 4.1 Run existing workflow tests to ensure no regressions
- [x] 4.2 Test multiple phase transitions to verify consistent behavior
