## 1. Establish regression coverage

- [ ] 1.1 Audit every preflight caller and delivery-property merge across commands and skills; verify the design's affected-path list matches current source without changing unrelated working edits.
- [ ] 1.2 Add observable command and skill regressions for skipped instruction partials, form-only cache restrictions and actual rendered contributors; verify the failing cases reproduce leakage before the fix. Do not assert production source text.
- [ ] 1.3 Cover shared form discovery, requirements filtering, duplicate diagnostics, resolved input use and unrelated header evaluation; verify input behaviour remains independent of response metadata.

## 2. Separate preflight state from delivery

- [ ] 2.1 Restrict preflight processing and its returned state to elicitation needs, retaining temporary context only until extraction and clearing unrelated headers at that boundary; verify focused preflight behaviour tests pass and original rendering context remains intact.
- [ ] 2.2 Remove preflight delivery-property carriers, composition helpers and merges from every consumer, including commands and skills; verify regression tests show metadata derives only from rendered contributors.
- [ ] 2.3 Remove or revise tests expecting preflight-only explicit cache/disposition contributions; verify cache composition still follows existing rules when contributors actually render.

## 3. Document and validate

- [ ] 3.1 Update authoring guidance to explain form-only contributions and placement of delivery headers on rendered contributors; verify guidance agrees with the delta specs and contains no preflight cache exception.
- [ ] 3.2 Run focused pytest suites in a foreground terminal to completion, then required project checks and strict OpenSpec validation; record complete results in the configured handover context.
- [ ] 3.3 Resolve status with available agent and workflow information and verify `user/information`; also verify a required rendered setup partial retains its instruction disposition and form interactions still resolve before rendering.
