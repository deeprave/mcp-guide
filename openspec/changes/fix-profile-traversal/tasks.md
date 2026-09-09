## 1. Central profile-loading boundary

- [x] 1.1 Add a shared simple-profile-basename validator that accepts valid built-ins including `_default` and rejects suffixes, separators, traversal, absolute paths, whitespace, and unsupported characters before filesystem lookup; verify focused unit parametrisation covers each case.
- [x] 1.2 Resolve the profiles root and candidate profile file canonically immediately before reading, reject targets outside the root, and verify unit tests prove an external symlink is not read while a contained symlink remains loadable.
- [x] 1.3 Preserve safe invalid-name and valid-not-found error distinctions without exposing external canonical paths, and verify direct `Profile.load` tests inspect both failure contracts.

## 2. Caller integration

- [x] 2.1 Route project profile application, profile inspection, category-filtered listing, and default-profile initialisation through the hardened loader without duplicate validation, and verify existing valid profile application and inspection behaviour remains unchanged.
- [x] 2.2 Add tool-level regression tests for traversal-style and escaping-symlink profile names, and verify their results are invalid-name failures with no external YAML content.

## 3. Verification

- [x] 3.1 Run `uv run pytest tests/unit/test_profile.py tests/integration/test_profile_application.py` in the foreground and verify all profile model and application tests pass.
- [x] 3.2 Run the relevant project-tool test subset in the foreground and verify profile error mapping remains compatible with standard tool results.
- [x] 3.3 Validate the completed OpenSpec change with `openspec validate fix-profile-traversal --type change --strict` and verify no validation errors remain.
