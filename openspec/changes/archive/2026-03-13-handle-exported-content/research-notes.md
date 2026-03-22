# AI Agents with Semantic Indexing Research

## Agents with Knowledge/Indexing Capabilities

### Kiro/Q-Dev
- **Tool**: `knowledge` tool
- **Detection**: Tool availability check
- **Capabilities**:
  - Semantic search using MiniLLM
  - Keyword search using BM25
  - Persistent storage across sessions
  - Commands: show, add, remove, search, update, status
- **Usage Pattern**:
  ```
  knowledge(command="search", query="...", context_id="...")
  ```

### Claude Desktop/Code
- **Tool**: None identified for semantic indexing
- **Note**: Uses MCP context but no persistent knowledge base tool

### GitHub Copilot
- **Tool**: None identified for semantic indexing
- **Note**: Uses workspace context but no persistent indexing

### Cursor
- **Tool**: None identified for semantic indexing
- **Note**: Uses codebase context but no persistent indexing

### Windsurf
- **Tool**: None identified for semantic indexing
- **Note**: Uses workspace context but no persistent indexing

## Detection Strategy

For template conditional logic:
1. Check if `knowledge` tool is available (kiro/q-dev)
2. If available, provide knowledge base instructions
3. Otherwise, provide direct file path access

## Template Conditional Logic

```mustache
{{#knowledge_available}}
Check your knowledge base for '{{export.expression}}' content.
If not indexed, you can index it from: {{export.path}}
{{/knowledge_available}}
{{^knowledge_available}}
Content has been exported to: {{export.path}}
You can read this file directly if needed.
{{/knowledge_available}}
```

## Conclusion

Currently, only kiro/q-dev has a documented semantic indexing tool (`knowledge`). Other major AI agents rely on workspace/codebase context but don't expose persistent indexing capabilities through tools.

The template should focus on:
1. Primary: kiro/q-dev knowledge tool detection
2. Fallback: Direct file path access for all other agents
