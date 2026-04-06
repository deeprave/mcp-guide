---
type: agent/instruction
description: >
  Style Policy: Comprehensions. Prefer list/dict/set comprehensions over imperative loops when the result is readable.
---
# Style Policy: Comprehensions

Prefer list/dict/set comprehensions over imperative loops when the result is readable.

## Rules

- Use comprehensions for simple transformations and filters
- Do not use comprehensions when the logic is complex enough to obscure intent
- Generator expressions are preferred over list comprehensions when the result
  is consumed once
- Avoid nested comprehensions beyond two levels

## Examples

```python
# Preferred
valid = [item.process() for item in items if item.is_valid()]

# Avoid
results = []
for item in items:
    if item.is_valid():
        results.append(item.process())
```

## Rationale

Comprehensions are more declarative and typically more readable for simple
cases. Preserves intent over mechanism.
