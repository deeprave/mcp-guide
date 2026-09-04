## REMOVED Requirements

### Requirement: Integration with FilesystemBridge
**Reason**: `FilesystemBridge` and `FileCache` no longer exist. Filesystem tools dispatch Session events directly.
**Migration**: Call `send_file_content` (and the other send_* tools) on the request Session; do not update a FileCache through FilesystemBridge.

### Requirement: guide_cache_file Tool
**Reason**: There is no server-side file cache. Agents deliver content with `send_file_content`.
**Migration**: Use `send_file_content`; content is carried on `FS_FILE_CONTENT` events.
