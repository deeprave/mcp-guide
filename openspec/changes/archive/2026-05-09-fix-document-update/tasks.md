## 1. Autoupdate semantics

- [x] 1.1 Register `autoupdate` with the shared boolean normaliser used by pure boolean flags
- [x] 1.2 Update or add tests covering boolean-string normalisation for `autoupdate`
- [x] 1.3 Update startup autoupdate evaluation so unset is treated as enabled and only explicit `false` disables prompting
- [x] 1.4 Update or add tests covering `autoupdate` unset, `true`, and `false`
- [x] 1.5 Update any user-facing flag documentation that currently describes missing `autoupdate` as disabled

## 2. Acknowledged startup prompting

- [x] 2.1 Change `McpUpdateTask` to queue the update prompt as an acknowledged instruction
- [x] 2.2 Ensure `update_documents` acknowledgement clears the tracked instruction and stops reminders
- [x] 2.3 Add or update tests for acknowledged queueing and acknowledgement behavior

## 3. Unbound update tool

- [x] 3.1 Verify `update_documents` uses only global/session docroot state and does not depend on bound-project data or resolved project flags
- [x] 3.2 Remove bound-project enforcement from the `update_documents` tool registration
- [x] 3.3 Update internal tool logic to work with an unbound session and resolve docroot from global config only while preserving configuration/docroot error handling
- [x] 3.4 Add or update tests proving `update_documents` succeeds without a bound project when config/docroot is available
- [x] 3.5 Add or update tests for configuration/docroot resolution failures without relying on `no_project`

## 4. Removed document reconciliation

- [x] 4.1 Extend installer update logic to detect files tracked in the previous install archive that are absent from the new template set
- [x] 4.2 Delete removed upstream files only when the local copy is unchanged from the previous original
- [x] 4.3 Preserve removed upstream files when the local copy was modified by the user
- [x] 4.4 Ensure deletion touches files only and never removes parent directories
- [x] 4.5 Add or update installer tests for removed unchanged files, removed modified files, and parent-directory preservation

## 5. Validation

- [x] 5.1 Run `openspec validate fix-document-update --strict`
- [x] 5.2 Run the focused update-task, update-tool, and installer test suites for the touched behavior
