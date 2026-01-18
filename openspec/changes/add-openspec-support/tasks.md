**Approval gate**: PENDING

## 1. Prerequisites
- [ ] 1.1 Await feature-flags implementation and approval
- [ ] 1.2 Define OpenSpec feature flag configuration schema
- [ ] 1.3 Establish OpenSpec directory detection strategy

## 2. Core OpenSpec Detection
- [ ] 2.1 Implement OpenSpec project detection (check openspec/ directory)
- [ ] 2.2 Add feature flag conditional logic
- [ ] 2.3 Create OpenSpec project metadata parser
- [ ] 2.4 Add error handling for malformed OpenSpec projects

## 3. MCP Tools Implementation
- [ ] 3.1 Implement list-specs tool
- [ ] 3.2 Implement list-changes tool
- [ ] 3.3 Implement get-change tool
- [ ] 3.4 Implement get-project-context tool
- [ ] 3.5 Add validate-change tool
- [ ] 3.6 Add show-delta tool
- [ ] 3.7 Add compare-specs tool

## 4. MCP Resources Implementation
- [ ] 4.1 Implement openspec://project resource
- [ ] 4.2 Implement openspec://specs/{domain} resource
- [ ] 4.3 Implement openspec://changes/{change-id} resource
- [ ] 4.4 Implement openspec://agents resource

## 5. MCP Prompts Implementation
- [ ] 5.1 Create @openspec draft-proposal prompt
- [ ] 5.2 Create @openspec review-proposal prompt
- [ ] 5.3 Create @openspec implement-tasks prompt
- [ ] 5.4 Create @openspec archive-change prompt

## 6. Template Context Integration
- [ ] 6.1 Add OpenSpec data to template context hierarchy
- [ ] 6.2 Integrate OpenSpec specs as template variables
- [ ] 6.3 Add OpenSpec change status to context
- [ ] 6.4 Update TemplateContext validation for OpenSpec data

## 7. Testing & Validation
- [ ] 7.1 Write unit tests for OpenSpec detection
- [ ] 7.2 Write integration tests for MCP tools
- [ ] 7.3 Test feature flag conditional behavior
- [ ] 7.4 Validate template context integration
- [ ] 7.5 Test error handling for missing OpenSpec structures

## 8. Response Formatting
- [ ] 8.1 Add FS_FILE_CONTENT handler for `.openspec-status.json`
- [ ] 8.2 Add FS_FILE_CONTENT handler for `.openspec-changes.json`
- [ ] 8.3 Add FS_FILE_CONTENT handler for `.openspec-show.json`
- [ ] 8.4 Format status response as markdown table
- [ ] 8.5 Format changes list as markdown table
- [ ] 8.6 Format show response as structured markdown
- [ ] 8.7 Format CLI error responses as user-friendly markdown
- [ ] 8.8 Return formatted responses as user/information type
- [ ] 8.9 Add tests for response formatting including error cases
