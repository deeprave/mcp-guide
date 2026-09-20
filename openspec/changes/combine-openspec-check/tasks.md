## 1. Combined OpenSpec check

- [x] 1.1 Replace the separate CLI-location and version templates with one cooperative `openspec-check` template. It SHALL collect the location with `which`/`where` and the `openspec --version` output in one agent command invocation, then report both values as JSON at `.openspec-info.json` via `{{tool_prefix}}send_file_content`. The instruction SHALL explain why Guide needs the result and that it is stored in the global `openspec-state` feature flag.

## 2. Single-round-trip detection flow

- [x] 2.1 Replace the two-stage OpenSpecTask request, acknowledgement, and event-handling flow with one combined detection request and `.openspec-info.json` response. It SHALL handle CLI-not-found, unparseable-version, and valid-version outcomes; preserve the existing `openspec-state` (`validated`, `version`, `checked`) contract; and trigger the existing project-structure check only after successful validation. `send_command_location` SHALL remain generic and unchanged.

## 3. Behavioural coverage

- [x] 3.1 Update OpenSpec task and acknowledgement tests to cover one queued detection request, the three detection outcomes, retained state serialisation, and the successful post-validation project check. Update any generic activation fixture only as required by the renamed template.

## 4. Validation

- [x] 4.1 Verify the rendered combined instruction communicates its purpose and route, confirm no references to the replaced templates remain, and run focused plus full test suites. Exercise a successful detection end-to-end and compare its persisted `openspec-state` shape with the previous contract.
