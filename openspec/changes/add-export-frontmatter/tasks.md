## 1. Export Metadata Resolution
- [x] 1.1 Reuse existing collected-document instruction resolution for exported content
- [x] 1.2 Resolve exported content type with precedence `user/information` < `agent/information` < `agent/instruction`
- [x] 1.3 Serialize resolved `type` and `instruction` as YAML frontmatter ahead of the exported payload

## 2. Export Tool Behavior
- [x] 2.1 Update `export_content` to prepend export frontmatter while preserving the existing rendered payload format beneath it
- [x] 2.2 Keep the export path, overwrite semantics, and tracking flow consistent with current behavior
- [x] 2.3 Add or update tests for single-document and multi-document export metadata resolution

## 3. Export Readback Guidance
- [x] 3.1 Update `_system/_export.mustache` to explain the meaning of exported `type` and `instruction` frontmatter
- [x] 3.2 Ensure both first-export and already-exported messages tell agents how to interpret exported files when they are read later
- [x] 3.3 Add or update template/tool tests covering the new guidance

## 4. Validation
- [x] 4.1 Run targeted export and instruction-resolution tests
- [x] 4.2 Run `openspec validate add-export-frontmatter --strict --no-interactive`
