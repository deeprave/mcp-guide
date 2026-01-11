## 1. Analysis and Design
- [ ] 1.1 Analyze current workflow phase parsing in workflow/parser.py
- [ ] 1.2 Design permission marker syntax parsing ("*phase", "phase*", "*phase*")
- [ ] 1.3 Define workflow.transitions template variable structure
- [ ] 1.4 Identify integration points with template context system

## 2. Core Implementation
- [ ] 2.1 Extend WorkflowState to include permission metadata
- [ ] 2.2 Update workflow parser to handle permission markers
- [ ] 2.3 Create transition permission calculation logic
- [ ] 2.4 Add workflow.transitions to template context

## 3. Template Integration
- [ ] 3.1 Update template context cache to include workflow transitions
- [ ] 3.2 Ensure workflow.transitions available in all workflow templates
- [ ] 3.3 Add transition guidance to default workflow templates

## 4. Configuration Support
- [ ] 4.1 Support custom workflow phase definitions with permission markers
- [ ] 4.2 Maintain backward compatibility with existing workflow configurations
- [ ] 4.3 Validate permission marker syntax in workflow configurations

## 5. Testing
- [ ] 5.1 Test permission marker parsing for all syntax variations
- [ ] 5.2 Test workflow.transitions template variable generation
- [ ] 5.3 Test integration with existing workflow functionality
- [ ] 5.4 Test custom workflow configurations with permission markers

## 6. Documentation
- [ ] 6.1 Document permission marker syntax in workflow documentation
- [ ] 6.2 Update template documentation with workflow.transitions usage
- [ ] 6.3 Provide examples of custom workflow configurations with permissions
