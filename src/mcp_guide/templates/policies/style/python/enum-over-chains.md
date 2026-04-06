---
type: agent/instruction
description: >
  Style Policy: Enum/Dict/Match Over Long Chains. Prefer enums, dictionaries, or `match/case` over long `if`/`elif` chains.
---
# Style Policy: Enum/Dict/Match Over Long Chains

Prefer enums, dictionaries, or `match/case` over long `if`/`elif` chains.

## Rules

- Avoid `if`/`elif` chains with more than one `elif`
- Use `match/case` (Python 3.10+) for structural dispatch
- Use dictionaries for simple value lookup and dispatch
- Use enums for named constants that represent a closed set of values

## Examples

```python
# Avoid
if action == "start":
    do_start()
elif action == "stop":
    do_stop()
elif action == "restart":
    do_restart()

# Preferred — match
match action:
    case "start":
        do_start()
    case "stop":
        do_stop()
    case "restart":
        do_restart()

# Preferred — dispatch table
handlers = {"start": do_start, "stop": do_stop, "restart": do_restart}
handlers[action]()
```

## Rationale

Long chains are hard to extend, easy to get wrong, and hide the underlying
structure. Dispatch tables and match statements make the set of cases explicit.
