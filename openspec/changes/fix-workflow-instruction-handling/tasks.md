## 1. Investigation
- [ ] 1.1 Examine workflow template rendering code to identify where instructions are processed
- [ ] 1.2 Check Result object construction to see if instruction field is being set correctly
- [ ] 1.3 Trace the flow from template frontmatter to final Result object
- [ ] 1.4 Identify if instruction is being overwritten or never set

## 2. Implementation
- [ ] 2.1 Fix instruction handling to preserve frontmatter instructions
- [ ] 2.2 Ensure Result object includes both template content and instruction
- [ ] 2.3 Verify no overwriting occurs during result processing

## 3. Testing
- [ ] 3.1 Test phase transition with frontmatter instruction preservation
- [ ] 3.2 Verify agent receives proper phase transition guidance
- [ ] 3.3 Confirm explicit consent messages are delivered

## 4. Validation
- [ ] 4.1 Run existing workflow tests to ensure no regressions
- [ ] 4.2 Test multiple phase transitions to verify consistent behavior
