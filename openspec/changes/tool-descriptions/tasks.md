## 1. Create Template Documentation
- [ ] 1.1 Create `src/mcp_guide/tools/README.md` with tool description standard
- [ ] 1.2 Include template structure: Description → Schema → Usage → Examples
- [ ] 1.3 Add example showing proper Pydantic Field descriptions
- [ ] 1.4 Document markdown formatting requirements for each section

## 2. Update Existing Tools
- [ ] 2.1 Add reference comment to `tool_category.py`
- [ ] 2.2 Add reference comment to `tool_collection.py`
- [ ] 2.3 Add reference comment to `tool_content.py`
- [ ] 2.4 Add reference comment to `tool_project.py`
- [ ] 2.5 Add reference comment to `tool_utility.py`

## 3. Audit and Fix Field Descriptions
- [ ] 3.1 Audit all tool argument Pydantic models for missing Field descriptions
- [ ] 3.2 Add descriptions to any fields missing them
- [ ] 3.3 Verify schema generation includes all descriptions

## 4. Update Specification
- [ ] 4.1 Create spec delta for tool-infrastructure
- [ ] 4.2 Add requirement for tool description standard
- [ ] 4.3 Add scenarios for each section of the standard
