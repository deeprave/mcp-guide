# Filesystem Access

The MCP Guide server can request access to files and directories on the agent's filesystem to provide contextual assistance with your projects.

## What It Does

The filesystem access feature allows the MCP server to:
- Read file contents to understand your codebase
- List directory contents to discover project structure
- Detect project types and configurations
- Cache frequently accessed files for better performance

This enables more accurate and contextual assistance by understanding your actual project files rather than working from general knowledge alone.

## Security Model

**By default, filesystem access is restricted to protect your system.**

### Default Restrictions
- Access limited to common project directories (`src/`, `docs/`, `tests/`, etc.)
- No access to system directories (`/etc`, `/usr`, `/System`)
- No access to sensitive directories (`~/.ssh`, `~/.aws`, etc.)
- Path traversal attacks (`../../../etc/passwd`) are blocked
- Symbolic links are validated to prevent escaping allowed paths

### Security Audit
All filesystem access attempts are logged with:
- Requested path and operation type
- Success/failure status
- Security violations and blocked attempts
- Timestamp and context information

## Configuration

### Project-Level Path Configuration
Configure allowed paths in your project's `.guide-config.json`:

```json
{
  "filesystem": {
    "allowed_write_paths": [
      "src/",
      "docs/",
      "tests/",
      "config/",
      "custom-directory/"
    ],
    "additional_read_paths": [
      "node_modules/",
      "vendor/",
      "build/"
    ]
  }
}
```

### Removing Restrictions (Advanced)
If you need unrestricted filesystem access and fully trust this MCP server:

```bash
kiro-cli /tools trust-all
```

**⚠️ WARNING**: This removes all security restrictions. The MCP server will have access to your entire filesystem. Only use this if you:
- Completely trust this MCP server
- Understand the security implications
- Are working in an isolated/sandboxed environment

To restore restrictions:
```bash
kiro-cli /tools trust-all false
```

## How It Works

1. **Agent Request**: The MCP server requests file/directory access via sampling requests
2. **Security Check**: Requested paths are validated against allowed paths and security policies
3. **Agent Response**: Your agent (kiro-cli) reads the files and sends content back to the server
4. **Caching**: Frequently accessed files are cached with modification-time tracking
5. **Audit Logging**: All access attempts are logged for security monitoring

## Privacy Considerations

- File contents are only accessed when specifically requested by the MCP server
- No automatic scanning or indexing of your filesystem occurs
- Cached file contents are stored temporarily and respect modification times
- All access is logged and can be audited
- You maintain full control over which paths are accessible

The filesystem access feature is designed to be helpful while maintaining security by default. You can always restrict access further or remove restrictions entirely based on your specific needs and trust level.
