## 1. Confirmed correction: session-management

- [ ] 1.1 Apply this change's `specs/session-management/spec.md` delta to `openspec/specs/session-management/spec.md` at archive time (or verify it applies cleanly now as a dry run). Verify completion by `openspec validate --specs` passing for `session-management` and the corrected requirement text matching the real `make_no_project_result()`/`GuideRuntime.get_no_project_instruction()` implementation in `src/mcp_guide/result_constants.py` and `src/mcp_guide/runtime.py`.

## 2. Priority audit: rewritten subsystems

- [ ] 2.1 Audit every spec describing `GuideRuntime` behavior (search `openspec/specs/*/spec.md` for "GuideRuntime") against `src/mcp_guide/runtime.py`, recording each requirement as accurate, needs-correction, or unclear. Verify completion by a written audit table covering every match.
- [ ] 2.2 Audit every spec describing `TaskManager` behavior (search for "TaskManager") against `src/mcp_guide/task_manager/manager.py`, recording the same verdicts. Verify completion by a written audit table covering every match.
- [ ] 2.3 Audit the remainder of `session-management`'s spec (beyond the no-project-result requirement already corrected in task 1) against `src/mcp_guide/session.py`. Verify completion by a written audit table covering every requirement in that file.
- [ ] 2.4 For each `needs-correction` verdict found in 2.1-2.3, write a `MODIFIED` (or `REMOVED`, with Reason and Migration, if genuinely obsolete) delta following the pattern established in task 1's `session-management` delta. Verify completion by `openspec validate --specs` passing for each corrected capability.

## 3. Secondary audit: remaining specs

- [ ] 3.1 Audit remaining specs not covered by task 2, prioritized by file size (largest first) as a secondary signal. Record the same accurate/needs-correction/unclear verdict for each. Verify completion by a written audit table covering every remaining file under `openspec/specs/`.
- [ ] 3.2 For each `needs-correction` verdict from 3.1 that can be corrected within this change's scope, write the corresponding delta. For any that can't (too large, needs a design discussion, or genuinely ambiguous), record it as explicit follow-up rather than silently leaving it. Verify completion by `openspec validate --specs` passing for each corrected capability, and a written list of explicit follow-up items for anything not corrected here.

## 4. Splitting oversized specs

- [ ] 4.1 Identify every spec file exceeding ~500 lines (`wc -l openspec/specs/*/spec.md`, sorted descending). Verify completion by a written list of files and line counts.
- [ ] 4.2 For each oversized file, split its requirements into multiple files along natural boundaries (e.g. by requirement theme within the same capability, or into a subdirectory if the capability itself has distinct sub-areas), preserving every requirement's full text and its `## Purpose` section on at least one resulting file. Verify completion by `openspec validate --specs` passing and each resulting file being under ~500 lines.
- [ ] 4.3 Re-read each split file standalone (not just structurally-valid) to confirm it reads coherently without requiring the sibling files for context beyond normal cross-references. Verify completion by a brief per-file readability note.

## 5. Final validation

- [ ] 5.1 Run `openspec validate --specs` (or the store-scoped equivalent) across the whole specs tree and confirm a clean result. Verify completion by the command's output showing zero errors.
- [ ] 5.2 Compile the final list of specs not yet audited or not yet corrected (from tasks 2-3) as tracked follow-up work, distinct from this change's completed scope. Verify completion by a written, itemized follow-up list.
