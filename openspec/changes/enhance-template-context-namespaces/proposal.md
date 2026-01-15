# Enhance Template Context with Client-Server Namespaces

**Status**: ✅ **COMPLETE** - All features implemented and working
**Priority**: Medium
**Complexity**: Low

## Why

Template authors currently have limited access to client-side context information, with all template context coming from the server side. This creates limitations for generating personalized and environment-aware content.

**Current Limitations:**
- No access to client-side environment information
- All context comes from server-side only
- No standardized way to collect client OS and platform details
- Templates cannot adapt to client-specific environments

**Use Cases:**
- Platform-specific documentation generation
- Client environment-aware templates
- OS-specific command examples
- Personalized content based on client context

## What Changes

Enhanced the TemplateContext system with client-server namespace architecture:

### **Server Namespace** (`{{server.*}}`) ✅
- Renamed from `system` namespace for clarity
- Contains server-side system information
- `{{server.os}}` - Server operating system
- `{{server.platform}}` - Server platform details
- `{{server.python_version}}` - Server Python version

### **Client Context Collection System** ✅
- Two-step client context collection process
- Basic OS detection followed by detailed context gathering
- Client-server data exchange via `send_file_content` tool
- Structured JSON data format for context information
- Automatic startup via @task_init decorator on ClientContextTask

### **Template Context Integration** ✅
- Added `_build_client_context()` to template_context_cache
- Proper namespace layering with client data priority
- Fixed nested dictionary handling for namespace access
- Maintained backward compatibility
- Cache invalidation when client data updates

### **ClientContextTask System** ✅
- Follows existing workflow task pattern
- Handles client context collection lifecycle
- Template-driven instruction generation
- Event-based data processing
- TIMER_ONCE for startup, FS_FILE_CONTENT for data reception
- Implements #equals and #contains Mustache helpers

### **Additional Improvements** ✅
- Created system info template showing server and client data
- Fixed timer bugs (counter-based unique bits, task counting)
- Removed all sampling-based code (not supported by clients)
- Fixed task stats to properly track timer vs regular tasks

**Example Usage:**
```mustache
# Environment Information
Server OS: {{server.os}}
Client OS: {{client.os}}
Platform: {{client.platform}}
Hostname: {{client.hostname}}
User: {{user.name}}
Git Remote: {{repo.origin.fetch_url}}
```

## Impact

- **ENHANCEMENT**: No breaking changes to functionality
- **NAMESPACE CHANGE**: Renamed `system` to `server` (breaking change for templates using `{{system.*}}`)
- **NEW FEATURE**: Client context collection and integration - fully working
- **ARCHITECTURE**: Clean client-server boundary with structured data exchange
- **CLEANUP**: Removed non-functional sampling code
