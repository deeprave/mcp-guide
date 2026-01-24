# Spec: Template Integration

## Command Templates

### list.mustache

#### Cache Check

```mustache
{{#openspec}}
{{#changes.0}}
## OpenSpec Changes
...
{{/changes.0}}

{{^changes.0}}
Run `openspec list --json` and send via guide_send_file_content with path `.openspec-changes.json`, then re-render this template.
{{/changes.0}}
{{/openspec}}
```

**Requirements**:
- MUST check `changes.0` for cache presence
- MUST display changes if cache exists
- MUST prompt refresh if cache empty
- MUST instruct re-render after refresh

#### Filter Support

```mustache
{{#kwargs.draft}}
Filter: Draft changes (no tasks)

{{/kwargs.draft}}
{{#kwargs.done}}
Filter: Completed changes (all tasks done)

{{/kwargs.done}}
{{#kwargs.prog}}
Filter: In-progress changes (has tasks but not complete)

{{/kwargs.prog}}
```

**Requirements**:
- MUST support --draft flag
- MUST support --done flag
- MUST support --prog flag
- MUST display filter description
- MUST match filter flag logic

#### Filtered Display

```mustache
{{#changes}}{{#kwargs.draft}}{{#is_draft}}
- `{{name}}` - {{status}} ({{progress}}) - {{lastModified}}{{/is_draft}}{{/kwargs.draft}}{{/changes}}
```

**Requirements**:
- MUST iterate over changes
- MUST check filter flag if filter active
- MUST display all fields
- MUST handle no filter (show all)
- MUST avoid extra newlines

### status.mustache

#### Cache-First Check

```mustache
{{#openspec.changes}}
Check if change `{{args.0.value}}` exists in cached changes list. If found, run status command.

If not found, refresh cache first, then run status command.
{{/openspec.changes}}

{{^openspec.changes}}
First refresh cache, then run status command.
{{/openspec.changes}}
```

**Requirements**:
- MUST check cache exists
- MUST validate change in cache
- MUST prompt refresh if cache empty
- MUST prompt refresh if change not found
- MUST run status after validation

### Mutation Templates

#### archive.mustache

```mustache
After successful archive, refresh the cache by running `openspec list --json` and sending via guide_send_file_content with path `.openspec-changes.json`.
```

**Requirements**:
- MUST instruct cache refresh
- MUST happen after operation
- MUST use correct file path
- MUST use guide_send_file_content

#### change/new.mustache

```mustache
After creating the change, refresh the cache by running `openspec list --json` and sending via guide_send_file_content with path `.openspec-changes.json`.
```

**Requirements**:
- MUST instruct cache refresh
- MUST happen after creation
- MUST use correct file path
- MUST use guide_send_file_content

#### init.mustache

```mustache
After initialization, refresh the cache by running `openspec list --json` and sending via guide_send_file_content with path `.openspec-changes.json`.
```

**Requirements**:
- MUST instruct cache refresh
- MUST happen after init
- MUST use correct file path
- MUST use guide_send_file_content

## Template Context

### OpenSpec Context Structure

```python
{
    "openspec": {
        "available": bool,
        "version": Optional[str],
        "changes": list[dict[str, Any]]
    }
}
```

**Requirements**:
- MUST include changes field
- MUST default to empty list
- MUST update on every render
- MUST call get_changes() method

### Changes List Structure

```python
[
    {
        "name": str,
        "status": str,
        "completedTasks": int,
        "totalTasks": int,
        "lastModified": str,
        "progress": str,
        "is_draft": bool,
        "is_done": bool,
        "is_in_progress": bool
    }
]
```

**Requirements**:
- MUST include all original fields
- MUST include computed filter flags
- MUST preserve field types
- MUST be JSON-serializable

## Display Formatting

### List Format

```
- `change-name` - status (progress) - date
```

**Requirements**:
- MUST use backticks for name
- MUST show status
- MUST show progress (N/A for drafts)
- MUST show formatted date
- MUST be one line per change

### Table Format

```
| Name | Status | Progress | Last Modified |
|------|--------|----------|---------------|
| name | status | progress | date          |
```

**Requirements**:
- MUST use markdown table
- MUST include header row
- MUST align columns
- MUST show all fields

## Error Handling

### Cache Miss

**Requirements**:
- MUST display clear instruction
- MUST specify exact command
- MUST specify file path
- MUST instruct re-render

### Invalid Cache

**Requirements**:
- MUST treat as cache miss
- MUST prompt refresh
- MUST NOT display error to user
- MUST log error internally

### Empty Results

**Requirements**:
- MUST display "no changes" message
- MUST NOT show empty list
- MUST NOT show table headers
- MUST be user-friendly
