# Change: Update User Documentation for 1.2.0 Release

## Why

User documentation under `docs/user/` has not been updated for features added in 1.1.0 and 1.2.0. Key capabilities — the `guide://` URI scheme, `read_resource` tool, stored documents, Codex support, and export commands — are undocumented. The `content-accessor` feature flag is missing from the flag reference.

## What Changes

- Add new page `docs/user/guide-uris.md` documenting the `guide://` URI scheme (content URIs, command URIs, `read_resource` tool fallback, Codex-specific usage)
- Add new page `docs/user/stored-documents.md` documenting stored document ingest and management
- Update `docs/user/installation.md` with Codex agent configuration
- Update `docs/user/commands.md` with `:export/` commands (`:export/add`, `:export/list`, `:export/remove`)
- Update `docs/user/feature-flags.md` with `content-accessor` flag
- Update `docs/user/getting-started.md` with brief mentions of `guide://` URIs and stored documents
- Update `docs/index.md` with links to new pages

## Impact

- Affected specs: `documentation`
- Affected files: `docs/user/guide-uris.md` (new), `docs/user/stored-documents.md` (new), `docs/user/installation.md`, `docs/user/commands.md`, `docs/user/feature-flags.md`, `docs/user/getting-started.md`, `docs/index.md`
