## 1. Startup Prompt Gating

- [x] 1.1 Inspect `McpUpdateTask` startup/update prompting flow and identify the earliest safe point to resolve and validate `docroot`
- [x] 1.2 Reuse or extract the installer-side docroot safety validation needed to determine whether a documentation root is updateable
- [x] 1.3 Update startup prompt gating so invalid docroots, including template-source docroots, return without queuing an acknowledged `update_documents` instruction

## 2. Version File Handling

- [x] 2.1 Update the startup prompt path to require `{docroot}/.version` before attempting version comparison
- [x] 2.2 Treat missing installed version files as no-prompt conditions rather than update-needed states
- [x] 2.3 Preserve prompting for valid installed documentation roots whose installed version differs from the package version

## 3. Verification

- [x] 3.1 Add or update tests covering suppression when `docroot` resolves to the template source directory
- [x] 3.2 Add or update tests covering suppression when `{docroot}/.version` is missing
- [x] 3.3 Add or update tests confirming valid outdated installed docs still queue the acknowledged update prompt
