# Spec: Project Detection

## Old Implementation (Removed)

### Directory-Based Detection

**Process**:
1. Request directory listing of `openspec/`
2. Parse directory entries
3. Check for `project.md` file
4. Check for `changes/` directory
5. Check for `specs/` directory
6. Enable project if all three exist

**Problems**:
- Requires directory listing event
- Complex validation logic
- Multiple filesystem operations
- Unnecessary checks (directories created by OpenSpec)

## New Implementation

### File-Based Detection

**Process**:
1. Receive `FS_FILE_CONTENT` event
2. Check if path is `openspec/project.md`
3. Enable project if file exists

**Code**:
```python
if path_name == "project.md" and path.startswith("openspec/"):
    self._project_enabled = True
    self.task_manager.set_cached_data("openspec_project_enabled", True)
    logger.info("OpenSpec project enabled")

    # Request version and changes
    if not self._version_requested:
        self._version_requested = True
        await self.request_version_check()
    if not self._changes_requested:
        self._changes_requested = True
        await self.request_changes_json()

    return True
```

**Requirements**:
- MUST check path name is "project.md"
- MUST check path starts with "openspec/"
- MUST set _project_enabled to True
- MUST update task manager cache
- MUST log info message
- MUST request version if not requested
- MUST request changes if not requested
- MUST return True to indicate handled

## Template Changes

### Old Template (Removed)

**File**: `openspec-changes-check.mustache`

**Content**: Requested directory listing of `openspec/changes/`

**Removed**: No longer needed with cache-based approach

### Updated Template

**File**: `openspec-project-check.mustache`

**Old Content**:
```mustache
List the `openspec/` directory and send via guide_send_directory_listing
```

**New Content**:
```mustache
Read `openspec/project.md` and send via guide_send_file_content
```

**Requirements**:
- MUST request file content, not directory
- MUST use guide_send_file_content
- MUST specify exact file path
- MUST be simple and direct

## Removed Code

### _check_project_structure()

**Removed Method**:
```python
def _check_project_structure(self, entries: list[dict[str, Any]]) -> None:
    has_project_md = False
    has_changes_dir = False
    has_specs_dir = False

    for entry in entries:
        name = entry.get("name", "")
        entry_type = entry.get("type", "")

        if name == "project.md" and entry_type == "file":
            has_project_md = True
        elif name == "changes" and entry_type == "directory":
            has_changes_dir = True
        elif name == "specs" and entry_type == "directory":
            has_specs_dir = True

    self._project_enabled = has_project_md and has_changes_dir and has_specs_dir
```

**Reason**: Unnecessary complexity, directories created by OpenSpec

### _handle_changes_listing()

**Removed Method**:
```python
def _handle_changes_listing(self, entries: list[dict[str, Any]]) -> None:
    changes_list = [
        entry["name"]
        for entry in entries
        if entry.get("type") == "directory" and not entry.get("name", "").startswith(".")
    ]

    self.task_manager.set_cached_data("openspec_changes_list", changes_list)
```

**Reason**: Replaced by JSON-based caching

### Directory Event Handling

**Removed Code**:
```python
if event_type & EventType.FS_DIRECTORY:
    path = data.get("path", "")

    if path.rstrip("/") == "openspec":
        entries = data.get("files", [])
        self._check_project_structure(entries)
        # ...

    elif path.rstrip("/") == "openspec/changes":
        entries = data.get("files", [])
        self._handle_changes_listing(entries)
```

**Reason**: No longer using directory listings

## Benefits

### Performance

- **Before**: 2 directory listings per project check
- **After**: 1 file read per project check
- **Reduction**: 50% fewer filesystem operations

### Simplicity

- **Before**: 60+ lines of validation logic
- **After**: 15 lines of file check
- **Reduction**: 75% less code

### Reliability

- **Before**: Depends on directory structure
- **After**: Depends only on canonical file
- **Improvement**: More robust detection

## Migration

### Backward Compatibility

**Requirements**:
- MUST work with existing OpenSpec projects
- MUST NOT require project changes
- MUST NOT break existing workflows
- MUST handle missing project.md gracefully

### Testing

**Requirements**:
- MUST test with project.md present
- MUST test with project.md absent
- MUST test with partial structure
- MUST verify version/changes requests
