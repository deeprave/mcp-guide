# Change: Replace aiofiles with anyio and standardise test markers

## Why
`aiofiles` delegates file close to a thread executor via a separate `await` in `__aexit__`.
When a task is cancelled between open and close, the file handle leaks — surfacing as
`ResourceWarning: unclosed file` under Python 3.14 with `filterwarnings = ["error"]`.
`anyio.Path` runs open-read/write-close atomically in a single thread call, eliminating
this class of bug. `anyio` is already a dependency (used in 10+ source files); `aiofiles`
becomes redundant. Similarly, `pytest-asyncio` can be dropped in favour of anyio's
built-in pytest plugin.

## What Changes
- Replace all `aiofiles` usage in production code with `anyio.Path` equivalents
- Replace all `aiofiles` usage in test code with `anyio.Path` equivalents
- Remove `aiofiles` from dependencies
- Convert all `@pytest.mark.asyncio` to `@pytest.mark.anyio` (496 markers across 70 files)
- Remove `asyncio_mode = "auto"` from pyproject.toml
- Remove `pytest-asyncio` from dev dependencies

## Impact
- Affected specs: core-modules, test-quality
- Affected code: 7 source files, 70+ test files, pyproject.toml
- Drops two dependencies: `aiofiles`, `pytest-asyncio`
