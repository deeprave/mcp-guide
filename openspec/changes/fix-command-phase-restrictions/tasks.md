## 1. Investigation
- [ ] 1.1 Identify where `requires-workflow-phase` is processed in the codebase
- [ ] 1.2 Trace command execution flow to understand why help text is shown instead of blocking
- [ ] 1.3 Determine if other `requires-*` directives have similar issues
- [ ] 1.4 Document current behavior vs expected behavior

## 2. Implementation
- [ ] 2.1 Fix phase restriction enforcement logic
- [ ] 2.2 Add proper error messages for blocked commands
- [ ] 2.3 Ensure consistent behavior across all `requires-*` directives
- [ ] 2.4 Update command processing to either block or execute completely

## 3. Testing
- [ ] 3.1 Test commands with phase restrictions in allowed phases
- [ ] 3.2 Test commands with phase restrictions in disallowed phases
- [ ] 3.3 Test commands without phase restrictions
- [ ] 3.4 Verify error messages are clear and helpful

## 4. Check
- [ ] 4.1 Run all existing tests to ensure no regressions
- [ ] 4.2 Manually test the `:issue` command in different phases
- [ ] 4.3 Verify other workflow commands work correctly
- [ ] 4.4 **READY FOR REVIEW** - Request user review explicitly
