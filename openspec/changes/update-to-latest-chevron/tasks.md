# Tasks

## 1. Establish the upgrade boundary

- [x] 1.1 Verify a released `chevron-ng` version exposes a compatible synchronous `render` API; record the selected version and verify its public API in an isolated environment.
- [x] 1.2 Inventory all renderer, frontmatter, partial, and Guide-extension call sites; add focused legacy behaviour fixtures for supported variables, sections, inverted sections, delimiter changes, partials, extension errors, and effective partial properties.

## 2. Prove synchronous renderer compatibility

- [x] 2.1 Replace the legacy `chevron` dependency with the selected `chevron-ng` release and update the lockfile; verify a clean environment imports the expected `chevron` API.
- [x] 2.2 Migrate template body and renderable frontmatter execution to the synchronous renderer with filesystem partial lookup explicitly disabled; verify existing template and frontmatter rendering tests retain their agent-visible results.
- [x] 2.3 Preserve Guide's existing partial loading, path containment, size limits, contribution tracking, and structured error handling around the synchronous renderer; verify security and partial-integration tests pass.
- [x] 2.4 Establish the explicit `lambdas=` registry in synchronous rendering; move callable Guide extensions out of template data, annotate compatibility and one-argument section protocols, and verify unregistered callables cannot execute.

## 3. Migrate to asynchronous rendering and extensions

- [x] 3.1 Verify the selected release exposes the required `async_render`, async extension, and async partial APIs in an isolated environment.
- [x] 3.2 Migrate template body and renderable frontmatter execution to the asynchronous renderer with filesystem partial lookup explicitly disabled; verify the established synchronous compatibility tests retain their results.
- [x] 3.3 Adapt callbacks to the asynchronous render model: convert predicate and wrapper-only callbacks to `chevron.section`, retain `chevron.compat` only where rendered input is required for parsing or side effects, and retire the unused unfit `contains` extension while retaining `workflow.contains`; verify normal, nested, and failure behaviour for every currently supported extension.
- [x] 3.6 Retire the unused external-highlighter availability probe; retain `highlight_code` as unconditional language-labelled Markdown code fencing, remove Guide's unused direct dependency, and update the template-support specification.
- [x] 3.4 Convert suitable derived-value extensions to decorated direct interpolation functions; verify Mustache escaping and context interpolation behaviour through renderer-level tests.
- [x] 3.5 Add asynchronous extension coverage for document, partial, and renderable frontmatter rendering; verify concurrent rendering awaits results without a synchronous event-loop bridge.

## 4. Adopt only justified newer composition features

- [x] 4.1 Audit current partial compositions for a narrow dynamic-tag or inheritance conversion; implement one only where it demonstrably simplifies an existing path while preserving output, containment, and partial-property behaviour, and verify the corresponding integration tests. No justified conversion was found: current partial names are static author-owned dependencies, while the repeated issue-tracker templates deliberately provide individually discoverable documents and shared frontmatter contribution through their static partial.

## 5. Adopt Chevron 0.20 extensions with inventory checkpoints

- [x] 5.1 Upgrade only the `chevron-ng` dependency and lockfile to 0.20.0, then run the standard rendering and integration tests before changing Guide code or templates.
- [x] 5.2 Add a standalone production-template inventory runner outside pytest that discovers shipped templates and renders curated representative template and partial cases with declared expected outcomes; establish and run its 0.20.0 dependency-only baseline.
- [x] 5.3 Enable `Extension.CONDITIONAL_SECTIONS`, replace Guide-created iterable guard booleans with conditional sections in Guide-owned templates, and rerun the inventory runner.
- [x] 5.4 Enable `Extension.ENHANCED_ITERATORS`, remove the `IndexedList` context wrapper, migrate Guide-owned sequence formatting to `.`, `.first`, and `.last`, document native list and iterator-metadata authoring for every list type, and rerun the inventory runner.

## 6. Verify the complete migration

- [x] 6.1 Run the complete template, partial-security, frontmatter, and integration test suites in the foreground; verify legacy regression fixtures and asynchronous-extension coverage pass.

## 7. Preserve frontmatter lambda behaviour and diagnostics

- [x] 7.1 Add an explicit renderable-frontmatter lambda profile that retains required contextual extensions, preserves `_error` and per-field diagnostics through `RenderedContent`, retains successfully rendered sibling fields, and reports `recommend` as unsupported without an active delivery session.
- [x] 7.2 Centralise standard command short-option normalisation and apply it consistently to prompt flags and command URI queries; preserve arbitrary short names in non-command URI queries.
