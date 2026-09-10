## Why

Profile loading appends a caller-controlled name to the profiles directory without
validating either the name or the canonical file target. A traversal-style name or
an escaping symlink can therefore make profile inspection or application read YAML
outside the bundled profiles directory.

## What Changes

- Permit only simple profile basenames: non-empty Unicode alphanumeric,
  underscore, and hyphen characters, including internal profiles such as
  `_default`, with no filename suffix or path component.
- Enforce profile-name validation at the shared profile-loading boundary, before
  existence checks or filesystem reads, so every caller receives the same
  protection.
- Resolve both the profiles directory and candidate profile target canonically and
  reject a candidate whose final target is not contained by that directory.
- Return safe validation or not-found failures without reading or disclosing an
  external YAML file.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `models`: Define safe profile identifier and profile-file containment behaviour
  for profile inspection, application, and internal profile loading.

## Impact

- Affected code: `mcp_guide.models.profile.Profile.load`, profile callers in
  project tools and configuration, and profile model/integration tests.
- Affected behaviour: profile names containing a separator, traversal component,
  absolute path, suffix, or other unsupported character become validation failures;
  symlinked profile files outside the canonical profiles directory are rejected.
