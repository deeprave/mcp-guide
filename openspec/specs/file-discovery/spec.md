# file-discovery Specification

## Purpose
TBD - created by archiving change add-export-tracking. Update Purpose after archive.
## Requirements
### Requirement: Document Discovery Function

The system SHALL provide a `discover_documents()` function that discovers files in a directory with metadata.

**Function signature:**
```python
async def discover_documents(
    base_dir: Path,
    patterns: list[str],
) -> list[FileInfo]
```

Arguments:
- `base_dir` (required, Path): Absolute path to base directory
- `patterns` (required, list[str]): Glob patterns to match files

The function SHALL:
- Validate `base_dir` is absolute and exists
- Expand patterns to include template variants
- Deduplicate template/non-template pairs (prefer non-template)
- Return list of FileInfo with metadata (path, size, mtime, name)

#### Scenario: Discover all matching files
- **WHEN** patterns provided
- **THEN** return all files matching patterns with metadata

