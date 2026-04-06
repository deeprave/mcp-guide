---
type: agent/instruction
description: >
  Toolchain Policy: Standard toolchain + testify (Go)
---
# Toolchain Policy: Standard toolchain + testify (Go)

| Role | Tool |
|---|---|
| Build | `go build` |
| Test runner | `go test` |
| Assertions | `testify` (`assert`, `require`) |
| Mocking | `testify/mock` or `gomock` |
| Linter | `golangci-lint` |
| Formatter | `gofmt` / `goimports` |

## Key commands

```bash
go test ./...
golangci-lint run
goimports -w .
```

## Rationale

`testify` provides cleaner assertions than the standard library's manual
`t.Errorf` style, while staying close to idiomatic Go.
