## 1. Safe partial-resolution boundary

- [ ] 1.1 Add a dedicated unsafe-partial resolution result and validate frontmatter references so absolute and home-anchored paths are rejected before lookup; verify unit tests confirm neither form reaches a filesystem read.
- [ ] 1.2 Update the partial loader to resolve relative references from the rendering template, retain the existing extension search order, and validate the final candidate through an explicit document-root resolver before reading; verify unit tests cover canonical in-root resolution and each extension form.
- [ ] 1.3 Thread the document-root resolver through every filesystem-backed template-rendering entry point and remove the unbounded current-directory/template-parent fallback for frontmatter partials; verify direct renderer tests supply a bounded resolver and ordinary no-partial rendering remains unchanged.

## 2. Rendering behaviour and regression coverage

- [ ] 2.1 Preserve valid nested parent-relative includes that canonically remain inside the document root; verify the existing command-partial integration cases continue to render expected content.
- [ ] 2.2 Reject traversal that escapes the document root, absolute paths, home-anchored paths, and symlinks whose final target is outside the root; verify parameterised tests prove the outside sentinel content is neither read nor rendered.
- [ ] 2.3 Ensure an unsafe partial is omitted with a non-sensitive diagnostic while the parent template and other safe partials still render; verify tests cover mixed safe and unsafe includes and no unsafe frontmatter or cache policy is merged.
- [ ] 2.4 Replace the legacy home-anchored partial success test with containment-rejection coverage and add end-to-end rendering tests using the actual document-root resolver; verify the test names and assertions describe the security contract.

## 3. Verification

- [ ] 3.1 Run the focused partial, frontmatter, renderer, and content-rendering test modules in the foreground; verify all pass with no unexpected template-output regressions.
- [ ] 3.2 Run the repository quality checks required for the changed Python modules and OpenSpec validation; verify they pass and `openspec validate fix-partial-resolution --strict` remains valid.
