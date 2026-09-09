## 1. Safe partial-resolution boundary

- [x] 1.1 Add a dedicated unsafe-partial resolution result and validate frontmatter references so home-anchored and environment-variable expansion syntax is rejected before lookup; verify unit tests confirm neither form reaches a filesystem read and that invalid references log a warning without failing the parent template.
- [x] 1.2 Update the partial loader to resolve relative references from the including template, retain the existing independent underscore-filename and extension search rules and discovery exclusion, and validate the final candidate through an explicit server-side document-root resolver before reading without using client-filesystem resolution; verify unit tests cover canonical in-root resolution, permitted in-root absolute references, each extension form, and exclusion from ordinary category discovery.
- [x] 1.3 Thread the document-root resolver through every filesystem-backed template-rendering entry point and remove the unbounded current-directory/template-parent fallback for frontmatter partials; verify direct renderer tests supply a bounded resolver and ordinary no-partial rendering remains unchanged.

## 2. Rendering behaviour and regression coverage

- [x] 2.1 Preserve valid nested parent-relative includes that canonically remain inside the document root; verify the existing command-partial integration cases continue to render expected content.
- [x] 2.2 Reject traversal and absolute paths that escape the document root, home-anchored and environment-variable syntax, and symlinks whose final target is outside the root; verify parameterised tests prove the outside sentinel content is neither read nor rendered.
- [x] 2.3 Ensure an unsafe partial is omitted with a non-sensitive diagnostic while the parent template and other safe partials still render; verify tests cover mixed safe and unsafe includes and no unsafe frontmatter or cache policy is merged.
- [x] 2.4 Replace the legacy home-anchored partial success test with containment-rejection coverage, normalise bundled frontmatter references to omit the partial filename's leading underscore, and add end-to-end rendering tests using the actual document-root resolver; verify the test names and assertions describe the security contract.

## 3. Verification

- [x] 3.1 Run the focused partial, frontmatter, renderer, and content-rendering test modules in the foreground; verify all pass with no unexpected template-output regressions.
- [x] 3.2 Run the repository quality checks required for the changed Python modules and OpenSpec validation; verify they pass and `openspec validate fix-partial-resolution --strict` remains valid.
