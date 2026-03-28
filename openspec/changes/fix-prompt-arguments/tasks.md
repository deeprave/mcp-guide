## 1. Investigation
- [ ] 1.1 Reproduce the issue: invoke `guide` prompt with arguments in TUI mode and confirm args are empty/missing
- [ ] 1.2 Compare how FastMCP registers prompt parameters via `mcp.prompt()` vs how TUI clients send prompt arguments
- [ ] 1.3 Add debug logging to capture the raw arguments received by the `guide` function in both TUI and stdio modes
- [ ] 1.4 Determine whether the `promptfunc` decorator wrapper is the cause or if the issue is in FastMCP/client argument marshalling

## 2. Fix
- [ ] 2.1 Apply the fix based on investigation findings
- [ ] 2.2 Verify arguments are received correctly in both TUI and stdio modes

## 3. Check
- [ ] 3.1 Run existing prompt tests
- [ ] 3.2 Manual verification in TUI mode
