---
type: agent/instruction
description: >
  Style Policy: Walrus Operator. Use the walrus operator (`:=`) where it eliminates a variable whose only purpose is to serve a conditional or loop expression.
---
# Style Policy: Walrus Operator

Use the walrus operator (`:=`) where it eliminates a variable whose only purpose
is to serve a conditional or loop expression.

## Rules

- Use `:=` when a variable is assigned solely for use in an `if` or `while`
  condition and is not needed outside that scope
- Do not use `:=` when it reduces clarity or when the assigned value is used
  in multiple places beyond the conditional

## Examples

```python
# Preferred
if match := pattern.search(text):
    process(match)

# Preferred
while chunk := file.read(8192):
    process(chunk)

# Avoid — no clarity benefit here
if (n := len(items)) > 10:
    print(n)  # n used outside the condition; assign normally
```

## Rationale

The walrus operator avoids introducing variables that exist only as a stepping
stone to a conditional. Reduces noise without sacrificing clarity when applied
appropriately.
