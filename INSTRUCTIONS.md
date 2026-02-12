# MCP Development Instructions

## Critical Architecture Understanding

### ASYNC FIRST - NO EXCEPTIONS
- **ASYNC FIRST**: We are an async-first codebase. ALL functions must be async unless they are trivial and do not need to call any other functions
- **NEVER** create sync "wrapper" functions or duplicate code for sync versions
- **NEVER** use synchronous I/O methods in async applications
- **ALWAYS** use async file operations (AsyncPath, aiofiles, etc.)
  - **NO** Path.read_text(), open(), or other sync I/O in async contexts
  - **NO** sync versions of async functions - this creates code duplication and maintenance burden

### Text Transformation Tools - PROHIBITED
- **NEVER** use `sed`, `awk`, or `perl` for text transformations. NOT EVER, NOT UNDER ANY CIRCUMSTANCES.

  #### Why These Tools Are Prohibited
  - Use of these tools is error-prone and very often creates more work than making changes directly.
  - When applied to multiple files, fixing their mistakes takes longer than editing files individually
  - They create subtle bugs that are hard to detect
  - They don't handle edge cases well (special characters, multiline patterns, etc.)

  #### Approved Alternatives
  - **fs_write with str_replace** - Precise, safe, shows exactly what changes
  - **Manual file editing** - When only a few files need changes
  - **grep to find, then fs_write to fix** - Locate patterns first, then make targeted changes
  - **Code tool** - For semantic code transformations (renaming symbols, etc.)

  #### Key principle
  - **Precision over speed**. It's better to make 50 careful changes than 1 bulk change that breaks things.

### Client vs Server Filesystem
- **SERVER**: MCP server runs on the server filesystem
- **CLIENT**: Files like .guide.yaml, project files exist on CLIENT filesystem
- **NEVER** attempt to read client files directly from server code using Path.read_text() or similar
- **ALWAYS** ask the client/agent to send file content to the server when needed
- This is why we have tools like guide_send_file_content - the client sends content to server

### Code Organisation
- **ALWAYS** use module-level imports (PEP 8). In some circumstances this rule may be broken but **must be commented** as to the reason why
- **NEVER** inline template code in Python files
- **ALWAYS** use existing template infrastructure for rendering
- **NEVER** hardcode paths like "templates" / "_workflow" - use proper discovery

### Template Handling
- **USE** existing template discovery and rendering infrastructure
- **NEVER** create inline template strings in code
- **FOLLOW** established patterns for template location and rendering
- Templates MUST be discoverable and rendered through existing mechanisms

### Code Reuse
- **ALWAYS** check for existing code before implementing new functionality
- **USE** established patterns and infrastructure
- **AVOID** reimplementing functionality that already exists
- **LEVERAGE** existing utilities for common operations

### Data Structures and Control Flow
- **PREFER** static dictionaries and enums over if/elif/else chains for mapping values
- **USE** enums to conceptualise different states and options rather than string literals
- **LEVERAGE** dictionary lookups, match/case statements, and iteration over enums instead of conditional chains
- **CENTRALISE** conversion logic in enum classmethods using simple iteration patterns
- **AVOID** duplicating string-to-value mapping logic across multiple locations

  #### Why This Approach Is Better
  - **Maintainability**: Adding new options requires changes in only one place
  - **Readability**: Intent is clearer with descriptive enum names and dictionary structures
  - **Type Safety**: Enums provide compile-time checking and IDE support
  - **Brevity**: Less code to write and maintain compared to long if/elif chains
  - **Consistency**: Centralised conversion ensures uniform behaviour across the codebase

### Private variables
- **NEVER** access private variables of a foreign class or module
- **ALWAYS** use the public API of that foreign class or module ONLY
- **FOLLOW** public APIs - properties, attributes and functions provided by the class
- **NEVER** by extension, use getattr(), hasattr() or setattr() or a foreign class or module

## Common Mistakes the agent makes that must be avoided
1. **NEVER** create sync wrapper functions or have effectively duplicate sync/async versions
2. **NEVER** assume it is possible to read client files directly from server code
3. **NEVER** using sync I/O in async contexts
4. **NEVER** hardcoding filesystem paths
5. **NEVER** have template content in code
6. **NEVER** ignore and duplicate existing infrastructure and functionality
7. **NEVER** use function-level imports without requirement (avoiding circular imports or rarely used modules etc)
8. **NEVER** hardcode instruction text - use existing template rendering infrastructure
9. **NEVER** access private attributes
10. **NEVER** use sed, awk, or perl for text transformations - use fs_write str_replace instead
11. **NEVER** use long if/elif/else chains for value mapping - use enums and dictionaries instead

