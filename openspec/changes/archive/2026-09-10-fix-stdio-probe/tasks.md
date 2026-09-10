## 1. Server-owned probe implementation

- [x] 1.1 Replace initial probe creation below `Session.bound_root_path` with an exclusively created, server-owned file directly beneath `/tmp`; write the unpredictable challenge, grant file read permission without modifying `/tmp`, and retain exact response registration; verify focused filesystem-probe tests pass.
- [x] 1.2 Make normal completion, mismatch, timeout, task stop, and Session disposal remove only the tracked server-owned `/tmp` probe and preserve one-shot state transitions; verify each terminal-path test passes.

## 2. Behavioural coverage

- [x] 2.1 Update success and mismatch probe tests to read and return the server-owned `/tmp` probe while asserting no probe path is created below the supplied client root; verify `tests/unit/test_client_resolution.py` passes.
- [x] 2.2 Add coverage for queued dispatch timeout and transport-disabled behaviour using the server-owned `/tmp` probe, including clean-up and read-permission assertions; verify the focused async tests pass.

## 3. Verification

- [x] 3.1 Run `uv run pytest tests/unit/test_client_resolution.py` in a foreground terminal and verify all client path, binding, and probe tests pass.
- [x] 3.2 Run the relevant broader test selection for filesystem tasks and verify formatting and static checks required by the repository pass.
