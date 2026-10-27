# Tasks

## 1. Establish the upgrade boundary

- [ ] 1.1 Verify a released `chevron-ng` version exposes the required `async_render`, async extension, and async partial APIs; record the selected version and verify its public API in an isolated environment.
- [ ] 1.2 Inventory all renderer, frontmatter, partial, and Guide-extension call sites; add focused legacy behaviour fixtures for supported variables, sections, inverted sections, delimiter changes, partials, extension errors, and effective partial properties.

## 2. Upgrade the rendering dependency

- [ ] 2.1 Replace the legacy `chevron` dependency with the selected `chevron-ng` release and update the lockfile; verify a clean environment imports the expected `chevron` API.
- [ ] 2.2 Migrate template body and renderable frontmatter execution to the asynchronous renderer with filesystem partial lookup explicitly disabled; verify existing template and frontmatter rendering tests retain their agent-visible results.
- [ ] 2.3 Preserve Guide's existing partial loading, path containment, size limits, contribution tracking, and structured error handling around the new renderer; verify security and partial-integration tests pass.

## 3. Migrate template extensions

- [ ] 3.1 Create a per-render explicit `lambdas=` registry, remove callable Guide extensions from ordinary template data, and verify unregistered callable context values are not executed.
- [ ] 3.2 Convert Guide section extensions to the supported decorated section protocol; verify normal, nested, and failure behaviour for every currently supported extension.
- [ ] 3.3 Convert suitable derived-value extensions to decorated direct interpolation functions; verify Mustache escaping and context interpolation behaviour through renderer-level tests.
- [ ] 3.4 Add asynchronous extension coverage for document, partial, and renderable frontmatter rendering; verify concurrent rendering awaits results without a synchronous event-loop bridge.

## 4. Adopt only justified newer composition features

- [ ] 4.1 Audit current partial compositions for a narrow dynamic-tag or inheritance conversion; implement one only where it demonstrably simplifies an existing path while preserving output, containment, and partial-property behaviour, and verify the corresponding integration tests.

## 5. Verify the complete migration

- [ ] 5.1 Run the complete template, partial-security, frontmatter, and integration test suites in the foreground; verify legacy regression fixtures and asynchronous-extension coverage pass.
- [ ] 5.2 Run Ruff, Ty, package installation, and strict OpenSpec validation; verify there are no regressions or dependency-resolution warnings.
