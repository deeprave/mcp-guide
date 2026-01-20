**Approval gate**: APPROVED

## 1. Core OpenSpec Detection & Discovery
- [x] 1.1 Implement OpenSpecTask for client context
- [x] 1.2 Add CLI path verification via guide_send_command_location
- [x] 1.3 Add project structure detection via guide_send_directory_listing
- [x] 1.4 Add version detection via guide_send_file_content
- [x] 1.5 Add changes list monitoring (60-minute timer)
- [x] 1.6 Cache discovery results in template context

## 2. Template Context Integration
- [x] 2.1 Add openspec context to template_context_cache
- [x] 2.2 Provide openspec.available boolean
- [x] 2.3 Provide openspec.version string
- [x] 2.4 Set openspec to false when disabled
- [x] 2.5 Add requires-openspec frontmatter support

## 3. Command Templates Implementation
- [x] 3.1 Create :openspec/init (user information)
- [x] 3.2 Create :openspec/list command
- [x] 3.3 Create :openspec/status command
- [x] 3.4 Create :openspec/show command
- [x] 3.5 Create :openspec/validate command
- [x] 3.6 Create :openspec/archive command
- [x] 3.7 Create :openspec/schemas command
- [x] 3.8 Create :openspec/change/new command
- [x] 3.9 Add command discovery with requires-openspec filtering

## 4. Response Formatting
- [x] 4.1 Add formatted status display (list format default)
- [x] 4.2 Add formatted changes list (list format default)
- [x] 4.3 Add --table flag support for tabular format
- [x] 4.4 Add human-readable relative timestamps
- [x] 4.5 Expand glob patterns in artifact paths
- [x] 4.6 Suppress verbose context-gathering output

## 5. Testing
- [x] 5.1 Write unit tests for OpenSpecTask
- [x] 5.2 Test CLI detection
- [x] 5.3 Test project detection
- [x] 5.4 Test version detection
- [x] 5.5 Test changes monitoring
- [x] 5.6 Test template context integration
