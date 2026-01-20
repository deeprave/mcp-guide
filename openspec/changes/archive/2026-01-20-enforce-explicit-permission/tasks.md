## 1. Analysis and Design
- [x] 1.1 Analyze current workflow phase parsing in workflow/parser.py
- [x] 1.2 Design permission marker syntax parsing ("*phase", "phase*", "*phase*")
- [x] 1.3 Define workflow.transitions template variable structure
- [x] 1.4 Identify integration points with template context system

## 2. Core Implementation
- [x] 2.1 Extend WorkflowState to include permission metadata
- [x] 2.2 Update workflow parser to handle permission markers
- [x] 2.3 Create transition permission calculation logic
- [x] 2.4 Add workflow.transitions to template context

## 3. Template Integration
- [x] 3.1 Update template context cache to include workflow transitions
- [x] 3.2 Ensure workflow.transitions available in all workflow templates
- [x] 3.3 Add transition guidance to default workflow templates

## 4. Configuration Support
- [x] 4.1 Support custom workflow phase definitions with permission markers
- [x] 4.2 Maintain backward compatibility with existing workflow configurations
- [x] 4.3 Validate permission marker syntax in workflow configurations

## 5. Testing
- [x] 5.1 Test permission marker parsing for all syntax variations
- [x] 5.2 Test workflow.transitions template variable generation
- [x] 5.3 Test integration with existing workflow functionality
- [x] 5.4 Test custom workflow configurations with permission markers

## 6. Documentation
- [x] 6.1 Document permission marker syntax in workflow documentation
- [x] 6.2 Update template documentation with workflow.transitions usage
- [x] 6.3 Provide examples of custom workflow configurations with permissions
