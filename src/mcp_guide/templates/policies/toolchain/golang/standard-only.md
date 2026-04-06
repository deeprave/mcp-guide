---
type: agent/instruction
description: >
  Toolchain Policy: Standard toolchain only (Go)
---
# Toolchain Policy: Standard toolchain only (Go)

| Role | Tool |
|---|---|
| Build | `go build` |
| Test runner | `go test` |
| Assertions | standard library only (`t.Errorf`, `t.Fatalf`) |
| Linter | `go vet` + `golangci-lint` |
| Formatter | `gofmt` |

## Rationale

Minimal external dependencies. Idiomatic Go style per the standard library.
Suitable for libraries or teams that prefer to avoid third-party test dependencies.
