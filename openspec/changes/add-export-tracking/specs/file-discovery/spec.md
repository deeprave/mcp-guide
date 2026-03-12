## REMOVED Requirements

### Requirement: Document Discovery Function - Time Filtering

**Reason:** Staleness detection now uses metadata hash comparison instead of mtime filtering during discovery. The `updated_since` parameter and associated filtering logic are no longer needed.

**Migration:** Remove `updated_since` parameter from `discover_documents()` function. Staleness is now detected by comparing metadata hashes after gathering all files.

## MODIFIED Requirements

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

## RENAMED Requirements

- FROM: `### Requirement: discover_category_files Function`
- TO: `### Requirement: Document Discovery Function`

**Rationale:** Function is used for commands, categories, and generic file discovery - not just categories. Name "discover_documents" better reflects its generic purpose and aligns with domain terminology.

**Parameter rename:** `category_dir` → `base_dir` for consistency with generic usage.
