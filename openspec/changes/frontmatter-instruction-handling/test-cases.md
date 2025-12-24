# Test Cases: Frontmatter Instruction Handling

## Test Case 1: Agent Instruction Content
**Input**: Content with `Type: agent/instruction` and custom `Instruction`
```yaml
---
Type: agent/instruction
Description: Testing guidelines
Instruction: Follow these testing guidelines when writing code.
---
# Testing Guidelines
- Write unit tests
- Use descriptive names
```

**Expected Output**:
- Content: "# Testing Guidelines\n- Write unit tests\n- Use descriptive names"
- Instruction: "Follow these testing guidelines when writing code."

## Test Case 2: User Information Content
**Input**: Content with `Type: user/information`
```yaml
---
Type: user/information
Description: User documentation
---
# User Guide
This is documentation for users.
```

**Expected Output**:
- Content: "# User Guide\nThis is documentation for users."
- Instruction: "Display this information to the user"

## Test Case 3: Agent Information Content
**Input**: Content with `Type: agent/information`
```yaml
---
Type: agent/information
Description: Internal context
---
# Internal Notes
These are internal implementation details.
```

**Expected Output**:
- Content: "# Internal Notes\nThese are internal implementation details."
- Instruction: "For your information and use. Do not display this content to the user."

## Test Case 4: Multiple Documents with Same Instruction
**Input**: Two documents both with `Instruction: "Follow these guidelines"`

**Expected Output**:
- Combined content from both documents
- Single instruction: "Follow these guidelines"

## Test Case 5: Multiple Documents with Different Instructions
**Input**:
- Document 1: `Type: agent/instruction`, `Instruction: "Follow guidelines A"`
- Document 2: `Type: agent/instruction`, `Instruction: "Follow guidelines B"`

**Expected Output**:
- Combined content from both documents
- Combined instruction: "Follow guidelines A Follow guidelines B" (or similar deduplication logic)

## Test Case 6: Mixed Content Types
**Input**:
- Document 1: `Type: user/information`
- Document 2: `Type: agent/instruction`, `Instruction: "Custom instruction"`

**Expected Output**:
- Combined content from both documents
- Instruction: "Display this information to the user. Custom instruction"

## Test Case 7: No Frontmatter (Backward Compatibility)
**Input**: Plain content without frontmatter
```
# Plain Content
This has no frontmatter.
```

**Expected Output**:
- Content: "# Plain Content\nThis has no frontmatter."
- Instruction: "Display this information to the user" (default)

## Test Case 8: Malformed Frontmatter
**Input**: Content with invalid YAML frontmatter
```yaml
---
Type: agent/instruction
Invalid: YAML: syntax
---
# Content
```

**Expected Output**:
- Content: "# Content" (frontmatter stripped even if malformed)
- Instruction: "Display this information to the user" (fallback)

## Test Case 9: Unknown Content Type
**Input**: Content with unrecognized type
```yaml
---
Type: unknown/type
Description: Unknown type
---
# Content
```

**Expected Output**:
- Content: "# Content"
- Instruction: "Display this information to the user" (fallback to user/information)
