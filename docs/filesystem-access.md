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

### Multi-Layer Security Architecture

The filesystem access system implements defense-in-depth with multiple security layers:

1. **Path Validation Layer**
   - Normalizes all paths to prevent traversal attacks
   - Validates against allowed path prefixes
   - Blocks access to system and sensitive directories
   - Resolves and validates symbolic links

2. **Security Policy Layer**
   - Enforces read/write permissions per project
   - Maintains audit logs of all access attempts
   - Tracks security violations and blocked requests
   - Provides configurable security levels

3. **Sampling Request Layer**
   - Agent-side validation before file operations
   - Secure communication between server and agent
   - Fallback handling for unsupported operations
   - Error recovery and retry mechanisms

### Default Security Restrictions

- **Read Access**: Limited to project directories (`src/`, `docs/`, `tests/`, etc.)
- **Write Access**: Restricted to explicitly configured paths only
- **System Protection**: No access to system directories (`/etc`, `/usr`, `/System`)
- **Privacy Protection**: No access to sensitive directories (`~/.ssh`, `~/.aws`, etc.)
- **Attack Prevention**: Path traversal attacks (`../../../etc/passwd`) are blocked
- **Link Validation**: Symbolic links are resolved and validated to prevent escaping

### Security Audit and Monitoring

All filesystem access attempts are comprehensively logged with:
- Requested path and operation type (read/write/list)
- Success/failure status and error details
- Security violations and blocked attempts
- Timestamp, user context, and request source
- Performance metrics and cache statistics

Audit logs are structured for easy analysis and can be integrated with security monitoring systems.

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
      "build/",
      "external-libs/"
    ]
  }
}
```

### Configuration Options

#### `allowed_write_paths` (Array of strings)
- **Purpose**: Directories where the MCP server can read and write files
- **Default**: `["src/", "docs/", "tests/", "examples/", "config/"]`
- **Security**: Paths are validated and normalized
- **Format**: Relative paths from project root, must end with `/`

#### `additional_read_paths` (Array of strings)
- **Purpose**: Additional directories for read-only access (beyond write paths)
- **Default**: `[]` (empty)
- **Use Cases**: Dependencies, build outputs, external libraries
- **Security**: Read-only access, cannot modify files in these paths

### Adding Paths via Commands

Use the built-in commands to safely add paths to your project configuration:

```bash
# Add a directory to allowed write paths
kiro-cli /add-write-path "new-module/"

# Add a directory to additional read paths
kiro-cli /add-read-path "external-deps/"

# List current filesystem configuration
kiro-cli /show-filesystem-config
```

These commands automatically:
- Validate path format and security
- Update your project configuration
- Apply changes immediately
- Maintain configuration file formatting

### Advanced Security Configuration

#### Removing Restrictions (Use with Caution)
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

## Architecture Overview

### Component Interaction

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Server    │───▶│  Sampling API    │───▶│   Agent (CLI)   │
│                 │    │                  │    │                 │
│ • Path requests │    │ • Security check │    │ • File access   │
│ • Content proc. │    │ • Audit logging  │    │ • Response send │
│ • Cache mgmt.   │    │ • Error handling │    │ • Local validation│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   File Cache    │    │ Security Policy  │    │ Path Validator  │
│                 │    │                  │    │                 │
│ • LRU eviction  │    │ • Path rules     │    │ • Normalization │
│ • Size limits   │    │ • Audit trail    │    │ • Symlink check │
│ • TTL tracking  │    │ • Violation log  │    │ • Traversal block│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow

1. **Request**: MCP server requests file/directory access
2. **Validation**: Security policy validates path against allowed lists
3. **Sampling**: Secure sampling request sent to agent
4. **Agent Processing**: Agent validates and performs file operation
5. **Response**: File content/listing sent back to server
6. **Caching**: Results cached with modification time tracking
7. **Audit**: All operations logged for security monitoring

## How It Works

### File Access Process

1. **Path Request**: MCP server requests access to a specific file or directory
2. **Security Validation**:
   - Path normalized and validated against security policy
   - Checked against allowed_write_paths and additional_read_paths
   - System and sensitive directories blocked
3. **Cache Check**: Recently accessed files served from cache if still valid
4. **Sampling Request**: If not cached, secure request sent to agent
5. **Agent Validation**: Agent performs additional security checks
6. **File Operation**: Agent reads file/directory and sends response
7. **Caching**: Response cached with modification time for future requests
8. **Audit Logging**: Complete operation logged for security monitoring

### Performance Optimizations

- **Intelligent Caching**: LRU cache with size and entry limits
- **Modification Tracking**: Files re-read only when modified
- **Batch Operations**: Multiple file requests optimized
- **Compression**: Large responses compressed for network efficiency

## Privacy Considerations

- **Explicit Access**: File contents only accessed when specifically requested
- **No Scanning**: No automatic scanning or indexing of your filesystem
- **Temporary Caching**: Cached contents stored temporarily with TTL
- **Modification Respect**: Cache invalidated when files change
- **Complete Logging**: All access attempts logged and auditable
- **User Control**: Full control over accessible paths and security level
- **Opt-in Model**: Filesystem access requires explicit configuration

## Troubleshooting

### Common Issues

**Access Denied Errors**
- Check if path is in `allowed_write_paths` or `additional_read_paths`
- Verify path format (relative, ends with `/` for directories)
- Review audit logs for security violations

**Performance Issues**
- Monitor cache hit rates in statistics
- Adjust cache size limits if needed
- Check for excessive file modification causing cache misses

**Configuration Problems**
- Validate JSON syntax in `.guide-config.json`
- Use `/show-filesystem-config` to verify current settings
- Check file permissions on configuration file

The filesystem access feature is designed to be helpful while maintaining security by default. You can always restrict access further or remove restrictions entirely based on your specific needs and trust level.
